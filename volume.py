import drive
import directoryentry

class Volume:
    BITMAP_FREE_BLOCK = '-'
    BITMAP_USED_BLOCK = '+'

    def __init__(self, name):
        self.drive = drive.Drive(name)

    def format(self):
        self.drive.format()
        block = self.drive.read_block(0)
        block = Volume.modify_block(block, 0, Volume.BITMAP_FREE_BLOCK * drive.Drive.DRIVE_SIZE)

        directory_entry = str(directoryentry.DirectoryEntry())
        cursor = drive.Drive.DRIVE_SIZE
        flag = True
        while flag:
            try:
                block = Volume.modify_block(block, cursor, directory_entry)
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
        block_number_list = self.locate_directory(path_list)
        return self.get_block_number_list_directory_entry(block_number_list)

    def mkfile(self, full_pathname):
        path_list = Volume.get_path_list(full_pathname)
        directory_list, file_name = Volume.get_directory_and_file_name(path_list)
        block_number_list = self.locate_directory(directory_list)

    def modify_block(block, start, data):
        end = start + len(data)
        if end > len(block):
            raise ValueError("invalid internal data")
        return block[:start] + data + block[end:]

    def write_block(self, n, data):
        self.drive.write_block(n, data)
        block = self.drive.read_block(0)
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

    def get_block_directory_entry(self, n):
        """Return a list of DirectoryEntry objects in block n."""
        block = self.drive.read_block(n)
        cursor = 0
        if n == 0:
            # skip bitmap
            cursor += drive.Drive.DRIVE_SIZE
        entry_list = []
        while cursor < drive.Drive.BLK_SIZE:
            entry = directoryentry.DirectoryEntry(block[cursor:cursor + directoryentry.DirectoryEntry.ENTRY_LENGTH])
            cursor += directoryentry.DirectoryEntry.ENTRY_LENGTH
            if len(entry.file_name) > 0:
                entry_list.append(entry)
        return entry_list

    def get_block_number_list_directory_entry(self, block_number_list):
        """Return a list of DirectoryEntry objects in all blocks given in the list."""
        entry_list = []
        for block_number in block_number_list:
            entry_list += self.get_block_directory_entry(block_number)
        return entry_list

    def locate_directory(self, directory_list):
        """Return a block number list containing all the blocks owned by this directory."""
        block_number_list = [0]
        for directory in directory_list:
            entry_list = self.get_block_number_list_directory_entry(block_number_list)
            # find the directory
            found = False
            i = 0
            while not found and i < len(entry_list):
                entry = entry_list[i]
                i += 1
                if entry.file_type == directoryentry.DirectoryEntry.DIRECTORY and entry.file_name == directory:
                    found = True
                    block_number_list = []
                    for block in entry.blocks:
                        if block > 0:
                            block_number_list.append(block)
            if not found:
                raise ValueError("directory '{}' dose not exist".format(directory))
        return block_number_list
