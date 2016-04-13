from charmhelpers.core import host
from charmhelpers.core import unitdata
from charmhelpers.core.hookenv import storage_get
from charmhelpers.core.hookenv import storage_list
from charmhelpers.fetch import apt_install
from charmhelpers.fetch import apt_update
from charmhelpers.fetch import add_source

from charms.reactive import remove_state
from charms.reactive import set_state
from charms.reactive import hook
from charms.reactive import when
from charms.reactive import when_not

from zfs import ZfsPool
from btrfs import BtrfsPool

from charms import layer


@hook('disk-pool-storage-attached')
def storage_attached():
    '''Run every time storage is attached to the charm.'''
    # Emit a state that this hook has been called.
    set_state('disk-pool-storage-attached')
    # Get the name of the storage and set a state that that one is available.
    # or perhaps a more generic storage attached hook that other things can
    # handle.
    # set_state('/dev/sda.available')


@when('disk-pool-storage-attached')
@when_not('disk-pool-tools-installed')
def install_storage_tools():
    '''Install the appropriate disk tools.'''
    storage_driver = get_storage_driver()
    if storage_driver == 'btrfs':
        pkg_list = ['btrfs-tools']
        apt_install(pkg_list, fatal=True)
        set_state('btrfs-tools-installed')
    if storage_driver == 'zfs':
        # Get the lsb_release information as a dictionary.
        lsb_release = host.lsb_release()
        # Figure out the codename for this cloud instance.
        if lsb_release and lsb_release['DISTRIB_CODENAME'] == 'trusty':
            add_source('ppa:zfs-native/stable')
            apt_update(fatal=True)
            # The zfs package names are different in trusty
            pkg_list = ['debootstrap', 'spl-dkms', 'zfs-dkms', 'ubuntu-zfs']
        else:
            pkg_list = ['zfsutils-linux']
        # Install the packages and exit if that operation fails.
        apt_install(pkg_list, fatal=True)
        set_state('zfs-tools-installed')
    set_state('disk-pool-tools-installed')


@when('disk-pool-storage-attached', 'btrfs-tools-installed')
def handle_btrfs_pool():
    '''The btrfs tools are installed, use the btfs tools.'''
    mount_point = get_mount_point()
    devices = get_devices()
    try:
        bfs = BtrfsPool(mount_point)
        for dev in devices:
            bfs.add(dev)
    except OSError:
        bfs = BtrfsPool.create(mountPoint=mount_point, devices=devices)
        bfs.mount(devices[0], mount_point)
    remove_state('disk-pool-storage-attached')


@when('disk-pool-storage-attached', 'zfs-tools-installed')
def handle_zfs_pool():
    '''The zfs tools are installed, use the zfs tools.'''
    unmounted_devices = get_unmounted_devices()
    number_of_devices = len(unmounted_devices)
    mount_point = get_mount_point()
    # Since we are using raidz you must add devices in multiples of 3.
    if number_of_devices > 0 and number_of_devices % 3 == 0:
        zfs = ZfsPool(mount_point)
        # Mount the devices in zfs.
        zfs.add(unmounted_devices, True)
        # Add the devices to the charm k/v store so we don't mount them again.
        add_mounted_devices(unmounted_devices)
    # Remove the disk-pool-storage-attached state, as we have handled it.
    remove_state('disk-pool-storage-attached')


def get_unmounted_devices():
    '''Return a list of devices that are not yet mounted.'''
    # Get a set of the storage devices available.
    device_set = set(get_devices())
    kv_store = unitdata.kv()
    mounted_set = set(kv_store.get('mounted.devices') or [])
    # Use sets here to do subtraction and deduplicate the entries.
    return list(device_set - mounted_set)


def add_mounted_devices(devices):
    '''Add the list of devices to the charm key/value store for tracking.'''
    # When devices is not a list, put it in a list.
    if not isinstance(devices, list):
        devices = [devices]
    kv_store = unitdata.kv()
    mounted_devices = kv_store.get('mounted.devices') or []
    # Save the mounted devices in the charm k/v store.
    kv_store.set('mounted.devices', mounted_devices + devices)


def get_storage_driver():
    '''Get the storage-driver for this layer.'''
    layer_options = layer.options('storage')
    return layer_options['storage-driver']


def get_mount_point():
    '''Get the storage-driver for this layer.'''
    layer_options = layer.options('storage')
    return layer_options['mount-point']


def get_devices():
    '''Get a list of storage devices.'''
    devices = []
    storage_ids = storage_list()
    for sid in storage_ids:
        storage = storage_get('location', sid)
        devices.append(storage)
    return devices
