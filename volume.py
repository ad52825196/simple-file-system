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
        block = drive.Drive.EMPTY_BLK
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
        entry, block_number_list = self.locate(full_pathname, directoryentry.DirectoryEntry.DIRECTORY, show = True)
        if entry is not None:
            block_number_list = entry.get_valid_blocks()
        return self.get_block_number_list_directory_entry(block_number_list)

    def mkfile(self, full_pathname, file_type = directoryentry.DirectoryEntry.FILE):
        parent_entry, block_number_list, file_name = self.locate(full_pathname, file_type, True)
        empty_entry_list = self.get_block_number_list_directory_entry(block_number_list, True)
        if len(empty_entry_list) > 0:
            entry = empty_entry_list[0]
        elif parent_entry is not None:
            # not root directory
            block_number, block = self.allocate_new_directory_block()
            parent_entry.add_new_block(block_number)
            self.write_block(block_number, block)
            parent_entry.file_length += len(block)
            self.write_entry(parent_entry)
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
        entry, block_number_list = self.locate(full_pathname, directoryentry.DirectoryEntry.FILE)
        return self.get_entry_content(entry), entry

    def delfile(self, full_pathname, file_type = directoryentry.DirectoryEntry.FILE):
        entry, block_number_list = self.locate(full_pathname, file_type)
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
        if len(path_list) == 2 and path_list[-1] == '':
            return []
        else:
            return path_list[1:]

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

    def locate(self, full_pathname, file_type = directoryentry.DirectoryEntry.FILE, make = False, show = False):
        """Return the DirectoryEntry object of the final file or directory if make is False, otherwise the DirectoryEntry object of the parent directory. Also return a block number list containing all the blocks owned by the parent directory. If this is the root directory, the returning DirectoryEntry object will be None and the block number list will only contain block 0."""
        path_list = Volume.get_path_list(full_pathname)
        entry = None
        block_number_list = [0]
        if len(path_list) == 0:
            # root directory
            if show:
                return entry, block_number_list
            else:
                raise ValueError("no file name specified")
        directory_list = path_list[:-1]
        file_name = path_list[-1]
        if len(file_name) == 0:
            raise ValueError("no file name specified")
        if ' ' in file_name:
            raise ValueError("cannot have spaces in file name")
        parent_entry = None
        for directory in directory_list:
            entry_list = self.get_block_number_list_directory_entry(block_number_list)
            # find the directory
            parent_entry = Volume.find_entry_in_entry_list(directoryentry.DirectoryEntry.DIRECTORY, directory, entry_list)
            if parent_entry is None:
                raise ValueError("directory '{}' dose not exist".format(directory))
            block_number_list = parent_entry.get_valid_blocks()
        entry_list = self.get_block_number_list_directory_entry(block_number_list)
        entry = Volume.find_entry_in_entry_list(file_type, file_name, entry_list)
        if make and entry is not None:
            raise ValueError("'{}' already exists".format(file_name))
        elif not make and entry is None:
            raise ValueError("'{}' does not exist".format(file_name))
        if make:
            return parent_entry, block_number_list, file_name
        return entry, block_number_list

    def allocate_new_directory_block(self):
        """Find a free block and generate a block filled with directory entries but not write to the disk. Return the free block number and the content of the block."""
        block_number = self.find_free_block()
        block = drive.Drive.EMPTY_BLK
        entry = str(directoryentry.DirectoryEntry())
        cursor = 0
        flag = True
        while flag:
            try:
                block = Volume.modify_block(block, cursor, entry)
                cursor += directoryentry.DirectoryEntry.ENTRY_LENGTH
            except:
                flag = False
        return block_number, block

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
