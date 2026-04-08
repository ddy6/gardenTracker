import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from auth import create_auth_cookie, create_authenticated_csrf_token, create_csrf_token, csrf_tokens_match, is_valid_auth_cookie, is_valid_csrf_token


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

    def test_valid_csrf_round_trip(self):
        secret = "test-secret"
        token = create_csrf_token(secret, now=1_700_000_000, ttl_seconds=60)
        self.assertTrue(is_valid_csrf_token(token, secret, now=1_700_000_030))

    def test_csrf_rejects_tampering(self):
        secret = "test-secret"
        token = create_csrf_token(secret, now=1_700_000_000, ttl_seconds=60)
        tampered = token.replace("csrf", "spoof", 1)
        self.assertFalse(is_valid_csrf_token(tampered, secret, now=1_700_000_030))

    def test_csrf_expires(self):
        secret = "test-secret"
        token = create_csrf_token(secret, now=1_700_000_000, ttl_seconds=10)
        self.assertFalse(is_valid_csrf_token(token, secret, now=1_700_000_011))

    def test_csrf_pair_requires_matching_cookie_and_form_token(self):
        secret = "test-secret"
        token = create_csrf_token(secret, now=1_700_000_000, ttl_seconds=60)
        other = create_csrf_token(secret, now=1_700_000_000, ttl_seconds=60)
        self.assertTrue(csrf_tokens_match(token, token, secret, now=1_700_000_030))
        self.assertFalse(csrf_tokens_match(token, other, secret, now=1_700_000_030))

    def test_authenticated_csrf_token_is_derived_from_auth_cookie(self):
        secret = "test-secret"
        auth_cookie = create_auth_cookie(secret, now=1_700_000_000, ttl_seconds=60)
        token = create_authenticated_csrf_token(auth_cookie, secret)
        self.assertTrue(token.startswith("csrf-auth|"))
        self.assertEqual(token, create_authenticated_csrf_token(auth_cookie, secret))


if __name__ == "__main__":
    unittest.main()
