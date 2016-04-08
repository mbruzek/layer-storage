import os

from shlex import split
from subprocess import check_call
from subprocess import check_output

from storagepool import StoragePool


class ZfsPool(StoragePool):
    '''The class to create a zfs storage pool.'''

    # The devices should be a list of strings.
    devices = []
    # The pool name must begin with a letter, and can only contain alphanumeric
    # characters as well as underscore ("_"), dash ("-"), period ("."), colon
    # (":"), and space (" "). The pool names "mirror", "raidz", "spare" and
    # "log" are reserved, as are names beginning with  the  pattern  "c[0-9]".
    pool_name = 'zfs-storage-pool'
    # The mount point has to be an abolute path.
    mountpoint = ''

    def __init__(self, reference):
        '''Return an ZfsPool object using a specified pool name.'''
        self.pool_name = reference

    @classmethod
    def create(cls, mount_point, devices, force=False):
        '''Return a new StoragePool object of devices at the mount point.'''
        pool = cls('zfs-storage-pool')
        # The mount point must be an absolute path.
        pool.mountpoint = os.path.abspath(mount_point)
        pool.devices = devices

        # The command that creates a zfs disk pool.
        cmd = 'sudo zpool create -m {0} {1} raidz '.format(pool.mountpoint,
                                                           pool.pool_name)
        cmd += ' '.join(pool.devices)
        print(cmd)
        # Run the command.
        output = check_output(split(cmd))
        return pool

    @property
    def size(self):
        '''Return a string tuple of used and total size of the storage pool.'''
        # Create a command to get the details of the storage pool (no header).
        cmd = 'sudo zfs list -H ' + self.pool_name
        output = check_output(split(cmd))
        if output:
            # NAME           USED  AVAIL  REFER  MOUNTPOINT
            # mbruzek-pool  62.5K   688M    19K  /mbruzek-pool
            self.used = str(line.split()[1])
            self.total = str(line.split()[2])
        # Return a tuple of used and available for this pool.
        return self.used, self.total

    def add(self, devices):
        '''Add devices to the zfs storage pool. This operation can fail if
        the number of disks does not match the origin raidz pool.'''
        # The self.mount_point will only exist if we created the zfs pool.
        if self.mountpoint:
            # The command that adds a device to a zfs pool.
            cmd = 'sudo zpool add {0} raidz '.format(self.pool_name)
            cmd += ' '.join(devices)
            print(cmd)
            check_call(split(cmd))
        else:
            # The command that creates a zfs pool without a mount point.
            cmd = 'sudo zpool create {0} raidz '.format(self.pool_name)
            cmd += ' '.join(devices)
            print(cmd)
            check_call(split(cmd))
            self.mountpoint = self.mount_point(self.pool_name)
        # Append the devices to the device list.
        if self.devices:
            self.devices.append(devices)
        else:
            self.devices = devices

    def mount_point(self, name):
        '''Return the mount point for the zfs pool name.'''
        # The command to get the mount_point property from a zfs pool.
        cmd = 'sudo zfs get -H mountpoint {0}'.format(name)
        output = check_output(split(cmd))
        if output:
            # NAME          PROPERTY    VALUE          SOURCE
            # mbruzek-pool  mountpoint  /mbruzek-pool  default
            return output.split()[2]
