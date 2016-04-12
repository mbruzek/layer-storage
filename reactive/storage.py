import os
from subprocess import check_call

from charmhelpers.core import host
from charmhelpers.core import unitdata
from charmhelpers.core.hookenv import config
from charmhelpers.core.hookenv import status_set
from charmhelpers.core.hookenv import storage_get
from charmhelpers.core.hookenv import storage_list
from charmhelpers.fetch import apt_install
from charmhelpers.fetch import configure_sources


from charms.reactive import set_state
from charms.reactive import hook
from charms.reactive import when
from charms.reactive import when_not

from btrfs import BtrfsPool
from zfs import ZfsPool

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
        lsb_release = host.lsb_release()
        if lsb_release and lsb_release['DISTRIB_CODENAME'] == 'trusty':
            configure_sources(update=True,
                              source_var='ppa:zfs-native/stable')
            pkg_list = ['debootstrap', 'spl-dkms', 'zfs-dkms', 'ubuntu-zfs']
        else:
            pkg_list = ['zfsutils-linux']
        apt_install(pkg_list, fatal=True)
        set_state('zfs-tools-installed')
    set_state('disk-pool-tools-installed')


@when('disk-pool-storage-attached', 'btrfs-tools-installed')
def handle_btrfs_pool():
    '''The btrfs tools are installed, use the btfs tools.'''
    mount_path = '/var/lib/docker'
    devices = get_devices()
    try:
        bfs = BtrfsPool(mount_path)
        for dev in devices:
            bfs.add(dev)
    except OSError:
        bfs = BtrfsPool.create(mountPoint=mount_path, devices=devices)
        bfs.mount(devices[0], mount_path)
    remove_state('disk-pool-storage-attached')


@when('disk-pool-storage-attached', 'zfs-tools-installed')
def handle_zfs_pool():
    '''The zfs tools are installed, use the zfs tools.'''
    unmounted_devices = get_unmounted_devices()
    # Since we are using raidz you must add devices in multiples of 3.
    if len(unmounted_devices) % 3 == 0:
        zfs = ZfsPool('juju-zfs-pool')
        zfs.add(unmounted_devices)
        add_mounted_devices(unmounted_devices)
    remove_state('disk-pool-storage-attached')


def get_unmounted_devices():
    '''Return a list of devices that are not yet mounted.'''
    device_set = {get_devices()}
    kv_store = unitdata.kv()
    mounted_set = {kv_store.get('mounted.devices') or []}
    return list(device_set - mounted_set)


def add_mounted_devices(devices):
    '''Add the list of devices to the charm key/value store for tracking.'''
    if not isinstance(devices, list):
        devices = [devices]
    kv_store = unitdata.kv()
    mounted_devices = kv_store.get('mounted.devices') or []
    kv_store.set('mounted.devices', mounted_devices + devices)


def get_storage_driver():
    '''Get the storage-driver for this layer.'''
    layer_options = layer.options('docker')
    return layer_options['storage-driver']


def get_devices():
    '''Get a list of storage devices.'''
    devices = []
    storage_ids = storage_list()
    for sid in storage_ids:
        storage = storage_get('location', sid)
        devices.append(storage)
    return devices
