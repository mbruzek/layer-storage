# Charm Layer for Storage

This repository contains the charm layer for storage, which can be used as a
base layer for other charms that use the Juju storage feature. For more 
information about Juju charms or layers please refer to 
the [Charm Layers](https://jujucharms.com/docs/devel/developer-layers)
documentation.

## Usage

In a layer that wants to use storage, the integration can be as simple as
placing the following in the `layer.yaml` file:

```yaml
includes: ['layer:storage']
```

Then amend the reactive code as you require to deliver and manage the 
lifecycle of your applications using storage. Refer to the
documentation on [how to write a layer](https://jujucharms.com/docs/devel/developer-layer-example).

Once you have the code written to manage storage you need to assemble
the charm from the layers. To do this run the `charm build` command from the
layer directory you just created.

```
charm build
```

Once built you should be able to deploy the assembled charm.

```
juju deploy ./<series>/<charm-name>
```

Where series it the code name for Ubuntu releases, such as "trusty" or "xenial"
and charm-name is what you named the layer in metadata.yaml.

### States

The storage layer raises a few synthetic events:

- disk-pool-storage-attached

- disk-pool-storage-tools-installed

##### disk-pool-storage-attached

When the -storage-attached hook runs this layer emits the 
`disk-pool-storage-attached` event. Other layers could use this state to 
run operations after storage is attached, such as format, or create a
file system.

```python
@when('disk-pool-storage-attached')
def prepare_disk():
    # Do some checks and prepare the storage.
```

##### disk-pool-storage-tools-installed

When the `disk-pool-storage-tools-installed` state is emitted the appropriate
tools for the pool have been installed.

```python
@when('disk-pool-storage-tools-installed')
def storage_info():
    # Use the pool tools to get details about storage
```

### Layer Options

##### storage-driver

The storage driver to use when mounting or pooling the devices. The supported
pool types are `btrfs`, and `zfs`. The `overlay` and `aufs` drivers are also
supported, but multiple devices will be mounted separately.
