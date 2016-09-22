import drive
import directoryentry

class Volume:
    BITMAP_FREE_BLOCK = '-'
    BITMAP_USED_BLOCK = '+'

    def __init__(self, name):
        self.name = name
        self.drive = drive.Drive(name)

    def format(self):
        self.drive.format()
        block = self.drive.read_block(0)
        block = Volume.modify_block(block, 0, Volume.BITMAP_FREE_BLOCK * drive.Drive.DRIVE_SIZE)

        entry = str(directoryentry.DirectoryEntry())
        cursor = drive.Drive.DRIVE_SIZE
        flag = True
        while flag:
            try:
                block = Volume.modify_block(block, cursor, entry)
                cursor += directoryentry.DirectoryEntry.ENTRY_LENGTH
            except:
                flag = False
        self.write_block(0, block)

    def reconnect(self):
        self.drive.reconnect()

    def disconnect(self):
        self.drive.disconnect()

    def ls(self, full_pathname):
        """Return a list of DirectoryEntry objects in the given directory."""
        path_list = Volume.get_path_list(full_pathname)
        block_number_list, directory = self.locate_directory(path_list)
        return self.get_block_number_list_directory_entry(block_number_list)

    def mkfile(self, full_pathname, file_type = directoryentry.DirectoryEntry.FILE):
        path_list = Volume.get_path_list(full_pathname)
        directory_list, file_name = Volume.get_directory_and_file_name(path_list)
        block_number_list, directory = self.locate_directory(directory_list)
        entry_list = self.get_block_number_list_directory_entry(block_number_list)
        entry = Volume.find_entry_in_entry_list(file_type, file_name, entry_list)
        if entry is not None:
            raise ValueError("'{}' exists in the directory".format(file_name))
        empty_entry_list = self.get_block_number_list_directory_entry(block_number_list, True)
        if len(empty_entry_list) > 0:
            entry = empty_entry_list[0]
        elif directory is not None:
            # not root directory
            block_number = self.allocate_new_directory_block()
            try:
                directory.add_new_block(block_number)
            except:
                self.write_block(block_number, release = True)
                raise
            directory.file_length += drive.Drive.BLK_SIZE
            self.write_entry(directory)
            entry = directoryentry.DirectoryEntry(block_number = block_number)
        else:
            raise IOError("no more space in root directory")
        entry.file_type = file_type
        entry.file_name = file_name
        self.write_entry(entry)

    def mkdir(self, full_pathname):
        self.mkfile(full_pathname, directoryentry.DirectoryEntry.DIRECTORY)

    def append(self, full_pathname, data):
        content, entry = self.get_file_content(full_pathname)
        content += data
        entry = self.write_file_content(entry, content)
        self.write_entry(entry)

    def get_file_content(self, full_pathname):
        """Return the file content along with the directory entry of this file."""
        path_list = Volume.get_path_list(full_pathname)
        directory_list, file_name = Volume.get_directory_and_file_name(path_list)
        block_number_list, directory = self.locate_directory(directory_list)
        entry_list = self.get_block_number_list_directory_entry(block_number_list)
        entry = Volume.find_entry_in_entry_list(directoryentry.DirectoryEntry.FILE, file_name, entry_list)
        if entry is None:
            raise ValueError("file '{}' does not exist".format(file_name))
        return self.get_entry_content(entry), entry

    def delfile(self, full_pathname, file_type = directoryentry.DirectoryEntry.FILE):
        path_list = Volume.get_path_list(full_pathname)
        directory_list, file_name = Volume.get_directory_and_file_name(path_list)
        block_number_list, directory = self.locate_directory(directory_list)
        entry_list = self.get_block_number_list_directory_entry(block_number_list)
        entry = Volume.find_entry_in_entry_list(file_type, file_name, entry_list)
        if entry is None:
            raise ValueError("'{}' does not exist".format(file_name))
        block_number_list = entry.get_valid_blocks()
        if file_type == directoryentry.DirectoryEntry.DIRECTORY:
            entry_list = self.get_block_number_list_directory_entry(block_number_list)
            if len(entry_list) > 0:
                raise IOError("directory is not empty")
        for block_number in block_number_list:
            self.write_block(block_number, release = True)
        entry = directoryentry.DirectoryEntry(block_number = entry.block_number, start = entry.start)
        self.write_entry(entry)

    def deldir(self, full_pathname):
        self.delfile(full_pathname, directoryentry.DirectoryEntry.DIRECTORY)

    def modify_block(block, start, data):
        end = start + len(data)
        if end > len(block):
            raise ValueError("invalid internal data")
        return block[:start] + data + block[end:]

    def write_block(self, n, data = '', release = False):
        if release:
            data = drive.Drive.EMPTY_BLK
        data += ' ' * (drive.Drive.BLK_SIZE - len(data))
        self.drive.write_block(n, data)
        block = self.drive.read_block(0)
        if release:
            block = Volume.modify_block(block, n, Volume.BITMAP_FREE_BLOCK)
        else:
            block = Volume.modify_block(block, n, Volume.BITMAP_USED_BLOCK)
        self.drive.write_block(0, block)

    def get_path_list(full_pathname):
        path_list = full_pathname.split('/')
        if path_list[0] != '' or len(path_list) < 2:
            raise ValueError("invalid pathname")
        if path_list[-1] == '':
            return path_list[1:-1]
        else:
            return path_list[1:]

    def get_directory_and_file_name(path_list):
        if len(path_list) < 1:
            raise ValueError("no file name specified")
        directory_list = path_list[:-1]
        file_name = path_list[-1]
        if ' ' in file_name:
            raise ValueError("cannot have spaces in file name")
        return directory_list, file_name

    def get_block_directory_entry(self, n, empty = False):
        """Return a list of DirectoryEntry objects in block n."""
        block = self.drive.read_block(n)
        cursor = 0
        if n == 0:
            # skip bitmap
            cursor += drive.Drive.DRIVE_SIZE
        entry_list = []
        while cursor < drive.Drive.BLK_SIZE:
            entry = directoryentry.DirectoryEntry(block[cursor:cursor + directoryentry.DirectoryEntry.ENTRY_LENGTH], n, cursor)
            cursor += directoryentry.DirectoryEntry.ENTRY_LENGTH
            if (not empty and len(entry.file_name) > 0) or (empty and len(entry.file_name) == 0):
                entry_list.append(entry)
        return entry_list

    def get_block_number_list_directory_entry(self, block_number_list, empty = False):
        """Return a list of DirectoryEntry objects in all blocks given in the list."""
        entry_list = []
        for block_number in block_number_list:
            entry_list += self.get_block_directory_entry(block_number, empty)
        return entry_list

    def locate_directory(self, directory_list):
        """Return a block number list containing all the blocks owned by this directory and the DirectoryEntry record."""
        entry = None
        block_number_list = [0]
        for directory in directory_list:
            entry_list = self.get_block_number_list_directory_entry(block_number_list)
            # find the directory
            entry = Volume.find_entry_in_entry_list(directoryentry.DirectoryEntry.DIRECTORY, directory, entry_list)
            if entry is None:
                raise ValueError("directory '{}' dose not exist".format(directory))
            block_number_list = entry.get_valid_blocks()
        return block_number_list, entry

    def allocate_new_directory_block(self):
        """Allocate a new block and fill with directory entries. Return the new block number."""
        block_number = self.find_free_block()
        block = self.drive.read_block(block_number)
        entry = str(directoryentry.DirectoryEntry())
        cursor = 0
        flag = True
        while flag:
            try:
                block = Volume.modify_block(block, cursor, entry)
                cursor += directoryentry.DirectoryEntry.ENTRY_LENGTH
            except:
                flag = False
        self.write_block(block_number, block)
        return block_number

    def find_free_block(self):
        """Find a free block in the volume."""
        block = self.drive.read_block(0)
        for i in range(drive.Drive.DRIVE_SIZE):
            if block[i] == Volume.BITMAP_FREE_BLOCK:
                return i
        raise IOError("no more space in volume '{}'".format(self.name))

    def write_entry(self, entry):
        block = self.drive.read_block(entry.block_number)
        block = Volume.modify_block(block, entry.start, str(entry))
        self.write_block(entry.block_number, block)

    def find_entry_in_entry_list(file_type, file_name, entry_list):
        """Return the found DirectoryEntry object in the entry_list or None if does not exist."""
        for entry in entry_list:
            if  entry.file_type == file_type and entry.file_name == file_name:
                return entry

    def get_entry_content(self, entry):
        content = ''
        block_number_list = entry.get_valid_blocks()
        for block_number in block_number_list:
            content += self.drive.read_block(block_number)
        return content[:entry.file_length]

    def write_file_content(self, entry, content):
        entry.file_length = 0
        block_number_list = entry.get_valid_blocks()
        while len(content) > 0:
            if len(block_number_list) > 0:
                block_number = block_number_list.pop(0)
            else:
                block_number = self.find_free_block()
                entry.add_new_block(block_number)
            self.write_block(block_number, content[:drive.Drive.BLK_SIZE])
            entry.file_length += min(drive.Drive.BLK_SIZE, len(content))
            content = content[drive.Drive.BLK_SIZE:]
        return entry
