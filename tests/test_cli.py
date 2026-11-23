import os
from pathlib import Path
import tempfile
import unittest

from proxmox_duo.cli import load_settings


class ConfigTests(unittest.TestCase):
    def test_private_config_loads(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "duo.ini"
            config.write_text(
                "[duo]\\nikey=DIexample\\nskey=secret\\nhost=api-test.duosecurity.com\\n"
            )
            os.chmod(config, 0o600)
            settings = load_settings(str(config))
            self.assertEqual(settings.ikey, "DIexample")

    def test_world_readable_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            config = Path(directory) / "duo.ini"
            config.write_text("[duo]\\nikey=x\\nskey=y\\nhost=api-test.duosecurity.com\\n")
            os.chmod(config, 0o644)
            with self.assertRaises(ValueError):
                load_settings(str(config))

    def test_symlink_is_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory) / "real.ini"
            target.write_text("[duo]\\nikey=x\\nskey=y\\nhost=api-test.duosecurity.com\\n")
            os.chmod(target, 0o600)
            link = Path(directory) / "link.ini"
            link.symlink_to(target)
            with self.assertRaises(ValueError):
                load_settings(str(link))


if __name__ == "__main__":
    unittest.main()
