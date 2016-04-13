import os

from shlex import split
from subprocess import call
from subprocess import check_call
from subprocess import check_output

from storage_pool import StoragePool


class ZfsPool(StoragePool):
    '''The class to create raidz zfs storage pools from a list of devices.
    The raidz group is a variation on RAID-5 that allows for better
    distribution of parity and eliminates the "RAID-5 write hole" (in
    which data and parity become inconsistent after a power loss). Data
    and parity is striped across all disks within a raidz group.'''

    # The devices should be a list of strings.
    devices = []
    # The pool name must begin with a letter, and can only contain alphanumeric
    # characters as well as underscore ("_"), dash ("-"), period ("."), colon
    # (":"), and space (" "). The pool names "mirror", "raidz", "spare" and
    # "log" are reserved, as are names beginning with  the  pattern  "c[0-9]".
    pool_name = ''
    # The mount point has to be an abolute path.
    mountpoint = ''

    def __init__(self, mount_point, name='juju-zfs-pool'):
        '''Return an ZfsPool object using the specified mount point. Notice
        this does not actually create the zfs pool.'''
        # TODO validate/normalize the pool name before proceeding.
        self.pool_name = name
        # The mount point must be an absolute path.
        self.mountpoint = os.path.abspath(mount_point)

    @classmethod
    def create(cls, mount_point, devices, force=False):
        '''Return a new ZfsPool object wiith the specified mount point and
        list of devices. This method actually creates the raidz zfs pool if
        it does not already exist.'''
        pool = cls(mount_point)
        pool.add(devices, force)
        return pool

    @property
    def size(self):
        '''Return a string tuple of used and total size of the zfs pool.'''
        # Create a command to get the details of the storage pool (no header).
        cmd = 'sudo zfs list -H {0}'.format(self.pool_name)
        output = check_output(split(cmd))
        if output:
            # NAME           USED  AVAIL  REFER  MOUNTPOINT
            # mbruzek-pool  62.5K   688M    19K  /mbruzek-pool
            self.used = str(line.split()[1])
            self.total = str(line.split()[2])
        # Return a tuple of used and available for this pool.
        return self.used, self.total

    def add(self, devices, force=False):
        '''Add devices to a raidz zfs storage pool. This operation can fail if
        the number of disks does not match the original raidz pool.'''
        force_flag = '-f' if force else ''
        # When the pool exists, add devices to the pool.
        if ZfsPool.exists(self.pool_name):
            # The command that adds a device to a raidz zfs pool.
            cmd = 'sudo zpool add {0} {1} raidz '.format(force_flag,
                                                         self.pool_name)
            cmd += ' '.join(devices)
            print(cmd)
            check_call(split(cmd))
            self.devices.append(devices)
        else:  # The pool does not yet exist, so we must create a new pool.
            # The command that creates a new raidz zfs disk pool.
            cmd = 'sudo zpool create {0} -m {1} {2} raidz '.format(
                    force_flag,
                    self.mountpoint,
                    self.pool_name)
            cmd += ' '.join(devices)
            print(cmd)
            output = check_output(split(cmd))
            self.devices = devices

    @staticmethod
    def exists(name):
        '''Return True if the specified zfs pool exists, False otherwise.'''
        # The command to list the pool by name.
        cmd = 'sudo zfs list -H {0}'.format(name)
        return_code = call(split(cmd))
        return return_code == 0
