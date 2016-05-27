import unittest

from zfs import ZfsPool
from mock import patch
from mock import MagicMock


class TestZfsPool(unittest.TestCase):
    """Test that the ZfsPool class is calling the right commands."""

    @patch.object(ZfsPool, 'exists', MagicMock(return_value=False))
    def testCreate(self):
        with patch('zfs.check_call') as zcc:
            ZfsPool.create('/tmp', ['/dev/sdx1', '/dev/sdy1', '/dev/sdz1'])
            zcc.assert_called_with([
                'sudo',
                'zpool',
                'create',
                '-m',
                '/tmp',
                'juju-zfs-pool',
                'raidz',
                '/dev/sdx1',
                '/dev/sdy1',
                '/dev/sdz1'])

    @patch.object(ZfsPool, 'exists', MagicMock(return_value=True))
    def testCreateTrue(self):
        with patch('zfs.check_call') as zcc:
            ZfsPool.create('/tmp/1', ['/dev/sde1', '/dev/sdf1', '/dev/sdg1'])
            zcc.assert_called_with([
                'sudo',
                'zpool',
                'add',
                'juju-zfs-pool',
                'raidz',
                '/dev/sde1',
                '/dev/sdf1',
                '/dev/sdg1'])

    @patch.object(ZfsPool, 'exists', MagicMock(return_value=False))
    def testAdd(self):
        with patch('zfs.check_call') as zcc:
            pool = ZfsPool('/home/ubuntu')
            pool.add(['/dev/sdm1', '/dev/sdn1', '/dev/sdo1'])
            zcc.assert_called_with([
                'sudo',
                'zpool',
                'create',
                '-m',
                '/home/ubuntu',
                'juju-zfs-pool',
                'raidz',
                '/dev/sdm1',
                '/dev/sdn1',
                '/dev/sdo1'])

    @patch.object(ZfsPool, 'exists', MagicMock(return_value=True))
    def testAddTrue(self):
        with patch('zfs.check_call') as zcc:
            pool = ZfsPool('/home/ubuntu')
            pool.add(['/dev/sdp1', '/dev/sdq1', '/dev/sdr1'])
            zcc.assert_called_with([
                'sudo',
                'zpool',
                'add',
                'juju-zfs-pool',
                'raidz',
                '/dev/sdp1',
                '/dev/sdq1',
                '/dev/sdr1'])

    def testExists(self):
        with patch('zfs.call') as zc:
            ZfsPool.exists('zfs-pool')
            zc.assert_called_with([
                'sudo',
                'zfs',
                'list',
                '-H',
                'zfs-pool'])


    def testSize(self):
        with patch('zfs.check_output') as zco:
            pool = ZfsPool('/home/zfs')
            pool.size
            zco.assert_called_with([
                'sudo',
                'zfs',
                'list',
                '-H',
                'juju-zfs-pool'])
