import volume
from subprocess import call

volume = volume.Volume('vdrive')
volume.format()
call('head -n 1 vdrive', shell=True)