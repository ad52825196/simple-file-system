import drive
from subprocess import call

vdrive = drive.Drive('vdrive')
vdrive.format()
call('cat vdrive', shell=True)