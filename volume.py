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
        position = drive.Drive.DRIVE_SIZE
        flag = True
        while flag:
            try:
                block = Volume.modify_block(block, position, directory_entry)
                position += len(directory_entry)
            except:
                flag = False
        Volume.write_block(self.drive, 0, block)

    def reconnect(self):
        self.drive.reconnect()

    def disconnect(self):
        self.drive.disconnect()

    def modify_block(block, start, data):
        end = start + len(data)
        if end > len(block):
            raise ValueError("invalid internal data")
        return block[:start] + data + block[end:]

    def write_block(drive, n, data):
        drive.write_block(n, data)
        block = drive.read_block(0)
        block = Volume.modify_block(block, n, Volume.BITMAP_USED_BLOCK)
        drive.write_block(0, block)
