import unittest
from unittest.mock import Mock

from proxmox_duo.push import DuoPush, Settings


class DuoPushTests(unittest.TestCase):
    def setUp(self):
        self.mock = Mock()
        self.client = DuoPush(
            Settings("DIexample", "secret", "api-1234.duosecurity.com"),
            client=self.mock,
        )

    def test_only_push_is_requested(self):
        self.mock.auth.return_value = {"txid": "transaction"}
        self.assertEqual(self.client.start("root"), "transaction")
        self.mock.auth.assert_called_once_with(
            factor="push", username="root", device="auto", async_txn=True
        )

    def test_missing_txid_fails_closed(self):
        self.mock.auth.return_value = {"result": "allow"}
        with self.assertRaises(RuntimeError):
            self.client.start("root")

    def test_realm_name_rejected(self):
        with self.assertRaises(ValueError):
            self.client.start("root@pam")

    def test_waiting(self):
        self.mock.auth_status.return_value = {"waiting": True, "success": False}
        self.assertEqual(self.client.status("x")["state"], "waiting")

    def test_approval(self):
        self.mock.auth_status.return_value = {
            "waiting": False, "success": True, "trusted_device_token": "ignored"
        }
        self.assertEqual(self.client.status("x"), {"state": "approved", "message": ""})

    def test_bypass_not_approval(self):
        self.mock.auth_status.return_value = {
            "waiting": False, "success": False, "status": "bypass"
        }
        self.assertEqual(self.client.status("x")["state"], "denied")

    def test_unrecognized_response_denied(self):
        self.mock.auth_status.return_value = {}
        self.assertEqual(self.client.status("x")["state"], "denied")

    def test_invalid_hostname(self):
        with self.assertRaises(ValueError):
            Settings("key", "secret", "attacker.example.com")


if __name__ == "__main__":
    unittest.main()
