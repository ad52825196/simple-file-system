class DirectoryEntry:
    FILE = 'f:'
    DIRECTORY = 'd:'
    DEFAULT_FILE_TYPE = FILE
    FILE_TYPE_LENGTH = 2
    MAX_FILE_NAME_LENGTH = 8
    MAX_NUMBER_OF_BLOCKS = 12
    FILE_SIZE_LENGTH = 4
    BLOCK_NUMBER_LENGTH = 3
    ENTRY_LENGTH = FILE_TYPE_LENGTH + MAX_FILE_NAME_LENGTH + 1 + FILE_SIZE_LENGTH + 1 + (BLOCK_NUMBER_LENGTH + 1) * MAX_NUMBER_OF_BLOCKS

    def __init__(self, entry_string = None):
        if entry_string is None:
            self.file_type = DirectoryEntry.DEFAULT_FILE_TYPE
            self.file_name = ''
            self.file_length = 0
            self.blocks = []
            for i in range(DirectoryEntry.MAX_NUMBER_OF_BLOCKS):
                self.blocks.append(0)
        else:
            cursor = 0
            self.file_type = entry_string[cursor:cursor + DirectoryEntry.FILE_TYPE_LENGTH]
            cursor += DirectoryEntry.FILE_TYPE_LENGTH
            self.file_name = entry_string[cursor:cursor + DirectoryEntry.MAX_FILE_NAME_LENGTH].strip()
            cursor += DirectoryEntry.MAX_FILE_NAME_LENGTH + 1
            self.file_length = int(entry_string[cursor:cursor + DirectoryEntry.FILE_SIZE_LENGTH])
            cursor += DirectoryEntry.FILE_SIZE_LENGTH + 1
            self.blocks = []
            for i in range(DirectoryEntry.MAX_NUMBER_OF_BLOCKS):
                self.blocks.append(int(entry_string[cursor:cursor + DirectoryEntry.BLOCK_NUMBER_LENGTH]))
                cursor += DirectoryEntry.BLOCK_NUMBER_LENGTH + 1

    def __str__(self):
        format_string = "{:{FILE_TYPE_LENGTH}}{:{MAX_FILE_NAME_LENGTH}} {:0{FILE_SIZE_LENGTH}}:"
        for i in range(DirectoryEntry.MAX_NUMBER_OF_BLOCKS):
            format_string += "{:0{BLOCK_NUMBER_LENGTH}} "
        return format_string.format(
            self.file_type, 
            self.file_name, 
            self.file_length, 
            *self.blocks, 
            FILE_TYPE_LENGTH = DirectoryEntry.FILE_TYPE_LENGTH, 
            MAX_FILE_NAME_LENGTH = DirectoryEntry.MAX_FILE_NAME_LENGTH, 
            FILE_SIZE_LENGTH = DirectoryEntry.FILE_SIZE_LENGTH, 
            BLOCK_NUMBER_LENGTH = DirectoryEntry.BLOCK_NUMBER_LENGTH)
