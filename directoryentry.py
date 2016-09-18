class DirectoryEntry:
    FILE_TYPE = {'file': 'f:', 'directory': 'd:'}
    DEFAULT_FILE_TYPE = 'file'
    MAX_FILE_NAME_LENGTH = 8
    MAX_NUMBER_OF_BLOCKS = 12

    def __init__(self):
        self.file_type = DirectoryEntry.DEFAULT_FILE_TYPE
        self.file_name = ''
        self.file_length = 0
        self.blocks = []
        for i in range(DirectoryEntry.MAX_NUMBER_OF_BLOCKS):
            self.blocks.append(0)

    def __str__(self):
        format_string = "{}{:<{MAX_FILE_NAME_LENGTH}} {:04}:"
        for i in range(DirectoryEntry.MAX_NUMBER_OF_BLOCKS):
            format_string += "{:03} "
        return format_string.format(
            DirectoryEntry.FILE_TYPE[self.file_type],
            self.file_name,
            self.file_length,
            *self.blocks,
            MAX_FILE_NAME_LENGTH = DirectoryEntry.MAX_FILE_NAME_LENGTH)
