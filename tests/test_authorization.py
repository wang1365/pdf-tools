import json
import importlib.util
import sys
import tempfile
import unittest
from datetime import UTC, datetime, timedelta
from pathlib import Path

AUTH_PATH = Path(__file__).resolve().parents[1] / "pdf_tools" / "authorization.py"
spec = importlib.util.spec_from_file_location("pdf_tools_authorization", AUTH_PATH)
authorization = importlib.util.module_from_spec(spec)
assert spec and spec.loader
sys.modules[spec.name] = authorization
spec.loader.exec_module(authorization)

AuthorizationStore = authorization.AuthorizationStore
build_canonical_json = authorization.build_canonical_json
is_cache_valid = authorization.is_cache_valid
verify_offline_license_document = authorization.verify_offline_license_document


class AuthorizationCoreTests(unittest.TestCase):
    def test_cache_is_valid_until_cache_until(self):
        now = datetime(2026, 5, 17, tzinfo=UTC)
        self.assertTrue(is_cache_valid({"cacheUntil": "2026-05-18T00:00:00.000Z"}, now))
        self.assertFalse(is_cache_valid({"cacheUntil": "2026-05-16T23:59:59.000Z"}, now))

    def test_store_round_trips_json_state(self):
        with tempfile.TemporaryDirectory() as tmp:
            store = AuthorizationStore(Path(tmp) / "auth.json")
            store.save({"token": "abc", "cacheUntil": "2026-05-18T00:00:00.000Z"})
            self.assertEqual(store.load()["token"], "abc")

    def test_canonical_json_sorts_nested_keys(self):
        payload = {"b": 1, "a": {"d": 4, "c": 3}}
        self.assertEqual(build_canonical_json(payload), '{"a":{"c":3,"d":4},"b":1}')

    def test_offline_license_rejects_device_mismatch_before_signature(self):
        document = {
            "schema_version": 1,
            "license_id": "lic_test",
            "product": "pdf-tools-pro",
            "edition": "pro",
            "user_id": "user-1",
            "subscription_id": "sub-1",
            "entitlements": ["desktop_basic_access"],
            "seat_limit": 1,
            "device": {"fingerprint": "device-a", "device_name": None, "os_name": None, "os_arch": None},
            "issued_at": "2026-05-17T00:00:00.000Z",
            "not_before": "2026-05-17T00:00:00.000Z",
            "expires_at": (datetime.now(UTC) + timedelta(days=1)).isoformat().replace("+00:00", "Z"),
            "issuer": "pdf-tools-home-trae",
            "signature_alg": "Ed25519",
            "signature": "invalid",
        }

        result = verify_offline_license_document(
            document,
            expected_product="pdf-tools-pro",
            device_fingerprint="device-b",
            public_key_pem="",
        )

        self.assertFalse(result.valid)
        self.assertIn("设备指纹", result.message)


if __name__ == "__main__":
    unittest.main()
