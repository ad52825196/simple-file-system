import csv
import sys
import directoryentry
import volume

def main():
    v = None
    while True:
        try:
            command_list = input("> ").strip().split(maxsplit = 1)
            command = get_command(command_list)
            if command == 'format':
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
                LS_FORMAT = "{:4}    {:8}    {:4}"
                title = LS_FORMAT.format('type', 'filename', 'size')
                print(title)
                print("-" * len(title))
                for entry in entry_list:
                    print(LS_FORMAT.format(entry.file_type, entry.file_name, entry.file_length))
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
            elif command == 'quit':
                disconnect(v)
                sys.exit()
            else:
                raise ValueError("invalid command")
        except Exception as e:
            print(e)

def get_command(command_list):
    if len(command_list) < 1:
        raise ValueError("invalid command")
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
