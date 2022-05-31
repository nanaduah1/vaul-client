from vaultclient import __version__

from vaultclient.client import VaultClient

def test_version():
    assert __version__ == '0.2.0'
