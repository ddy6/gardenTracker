import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from auth import create_auth_cookie, is_valid_auth_cookie


class AuthHelperTests(unittest.TestCase):
    def test_valid_cookie_round_trip(self):
        secret = "test-secret"
        cookie = create_auth_cookie(secret, now=1_700_000_000, ttl_seconds=60)
        self.assertTrue(is_valid_auth_cookie(cookie, secret, now=1_700_000_030))

    def test_cookie_rejects_tampering(self):
        secret = "test-secret"
        cookie = create_auth_cookie(secret, now=1_700_000_000, ttl_seconds=60)
        tampered = cookie.replace("garden", "spoof", 1)
        self.assertFalse(is_valid_auth_cookie(tampered, secret, now=1_700_000_030))

    def test_cookie_expires(self):
        secret = "test-secret"
        cookie = create_auth_cookie(secret, now=1_700_000_000, ttl_seconds=10)
        self.assertFalse(is_valid_auth_cookie(cookie, secret, now=1_700_000_011))


if __name__ == "__main__":
    unittest.main()
