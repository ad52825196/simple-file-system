import csv
import sys
import directoryentry
import volume

def main():
    v = None
    while True:
        try:
            command_list = input().strip().split(maxsplit = 1)
            command = get_command(command_list)
            if command is None:
                pass
            elif command == 'format':
                v = connect_volume(command_list, v)
                v.format()
            elif command == 'reconnect':
                v = connect_volume(command_list, v)
                try:
                    v.reconnect()
                except:
                    v = None
                    raise
            elif command == 'ls':
                if v is None:
                    raise ValueError("no volume is connected")
                args = get_args(command_list)
                entry_list = v.ls(args[0])
                LS_FORMAT = "{:{NAME_LENGTH}}    {:{TYPE_LENGTH}}    {:{SIZE_LENGTH}}"
                title = LS_FORMAT.format('name', 'type', 'size', 
                    NAME_LENGTH = max(4, directoryentry.DirectoryEntry.MAX_FILE_NAME_LENGTH), 
                    TYPE_LENGTH = max(4, directoryentry.DirectoryEntry.FILE_TYPE_LENGTH), 
                    SIZE_LENGTH = max(4, directoryentry.DirectoryEntry.FILE_SIZE_LENGTH))
                print("Currently showing directory {}".format(args[0]))
                print(title)
                print("-" * len(title))
                for entry in entry_list:
                    print(LS_FORMAT.format(entry.file_name, entry.file_type, entry.file_length, 
                        NAME_LENGTH = max(4, directoryentry.DirectoryEntry.MAX_FILE_NAME_LENGTH), 
                        TYPE_LENGTH = max(4, directoryentry.DirectoryEntry.FILE_TYPE_LENGTH), 
                        SIZE_LENGTH = max(4, directoryentry.DirectoryEntry.FILE_SIZE_LENGTH)))
            elif command == 'mkfile':
                if v is None:
                    raise ValueError("no volume is connected")
                args = get_args(command_list)
                v.mkfile(args[0])
            elif command == 'mkdir':
                if v is None:
                    raise ValueError("no volume is connected")
                args = get_args(command_list)
                v.mkdir(args[0])
            elif command == 'append':
                if v is None:
                    raise ValueError("no volume is connected")
                args = get_args(command_list)
                if len(args) < 2:
                    raise ValueError("invalid command")
                v.append(args[0], args[1])
            elif command == 'print':
                if v is None:
                    raise ValueError("no volume is connected")
                args = get_args(command_list)
                content, entry = v.get_file_content(args[0])
                print(content)
            elif command == 'delfile':
                if v is None:
                    raise ValueError("no volume is connected")
                args = get_args(command_list)
                v.delfile(args[0])
            elif command == 'deldir':
                if v is None:
                    raise ValueError("no volume is connected")
                args = get_args(command_list)
                v.deldir(args[0])
            elif command == 'quit':
                disconnect(v)
                sys.exit()
            else:
                raise ValueError("invalid command")
        except EOFError:
            disconnect(v)
            sys.exit()
        except Exception as e:
            print(e)

def get_command(command_list):
    if len(command_list) < 1:
        return None
    return command_list[0]

def get_args(command_list):
    if len(command_list) < 2:
        raise ValueError("invalid command")
    return next(csv.reader([command_list[1]], delimiter = ' '))

def disconnect(v):
    try:
        v.disconnect()
    except:
        pass

def connect_volume(command_list, old):
    args = get_args(command_list)
    volume_name = args[0]
    disconnect(old)
    return volume.Volume(volume_name)

if __name__ == '__main__':
    main()
