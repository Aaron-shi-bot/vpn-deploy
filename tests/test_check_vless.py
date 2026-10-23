"""Synthetic, offline regression tests for the VLESS distribution checker."""

import base64
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

SCRIPT = Path(__file__).resolve().parents[1] / "skills/vpn-deploy/scripts/check_vless.py"
SPEC = importlib.util.spec_from_file_location("check_vless", SCRIPT)
checker = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(checker)

# These are fabricated test values and cannot authenticate to any real service.
UUID_ONE = "11111111-1111-4111-8111-111111111111"
UUID_TWO = "22222222-2222-4222-8222-222222222222"
PUBLIC_KEY = base64.urlsafe_b64encode(bytes(range(32))).decode("ascii").rstrip("=")
SHORT_ID = "0123456789abcdef"


def link(node_uuid=UUID_ONE):
    return (f"vless://{node_uuid}@synthetic.example.invalid:443?"
            f"encryption=none&type=tcp&security=reality&flow=xtls-rprx-vision&"
            f"sni=synthetic-sni.example.invalid&fp=chrome&pbk={PUBLIC_KEY}&sid={SHORT_ID}"
            "#synthetic-node")


def codes(result):
    return {error["code"] for error in result["errors"]}


class AnalyzeTests(unittest.TestCase):
    def test_valid_selected_profile(self):
        result = checker.analyze(link())
        self.assertTrue(result["ok"])
        self.assertEqual(result["count"], 1)
        self.assertTrue(result["limitations"])
        self.assertTrue(checker.analyze(link().replace("type=tcp", "type=raw"))["ok"])

    def test_all_required_parameters(self):
        values = {"encryption": "none", "type": "tcp", "security": "reality",
                  "flow": "xtls-rprx-vision", "sni": "synthetic-sni.example.invalid",
                  "fp": "chrome", "pbk": PUBLIC_KEY, "sid": SHORT_ID}
        for key, value in values.items():
            with self.subTest(key=key):
                result = checker.analyze(link().replace(f"{key}={value}", f"{key}="))
                self.assertFalse(result["ok"])
                self.assertIn("MISSING_" + key.upper(), codes(result))

    def test_duplicate_uuid(self):
        result = checker.analyze(link() + "\n" + link(), expect_count=2)
        self.assertIn("DUPLICATE_UUID", codes(result))
        self.assertEqual(result["errors"][0]["index"], 2)

    def test_base64_two_nodes(self):
        plaintext = link() + "\n" + link(UUID_TWO)
        for encode in (base64.b64encode, base64.urlsafe_b64encode):
            encoded = encode(plaintext.encode()).decode()
            self.assertTrue(checker.analyze(encoded, expect_count=2)["ok"])
            self.assertTrue(checker.analyze(encoded.rstrip("="), expect_count=2)["ok"])

    def test_count_mismatch_prevents_multiple_node_import(self):
        result = checker.analyze(link() + "\n" + link(UUID_TWO))
        self.assertIn("COUNT_MISMATCH", codes(result))
        self.assertEqual(result["count"], 2)

    def test_corrupt_uri(self):
        for source in (link().replace(":443", ":broken-secret"),
                       link().replace("synthetic.example.invalid", "[broken-secret"),
                       link().replace("fp=chrome", "fp=%secret"),
                       link().replace("fp=chrome", "fp=chro\tme")):
            with self.subTest(source_kind="malformed synthetic URI"):
                self.assertIn("MALFORMED_URI", codes(checker.analyze(source)))

    def test_private_key_and_duplicates_rejected(self):
        self.assertIn("PRIVATE_KEY_PRESENT", codes(checker.analyze(
            link().replace("#", "&privateKey=synthetic-secret#"))))
        self.assertIn("PRIVATE_KEY_PRESENT", codes(checker.analyze(
            link().replace("#", "&Private_Key=synthetic-secret#"))))
        self.assertIn("DUPLICATE_PARAMETER", codes(checker.analyze(
            link().replace("#", "&fp=firefox#"))))
        self.assertIn("DUPLICATE_PARAMETER", codes(checker.analyze(
            link().replace("#", "&FP=firefox#"))))

    def test_uuid_host_and_port(self):
        for source, expected in (
            (link().replace(UUID_ONE, "synthetic-secret"), "INVALID_UUID"),
            (link().replace("synthetic.example.invalid", ""), "MISSING_HOST"),
            (link().replace(":443", ":0"), "INVALID_PORT"),
            (link().replace(":443", ""), "INVALID_PORT"),
            (link().replace(":443", ":65536"), "MALFORMED_URI"),
        ):
            self.assertIn(expected, codes(checker.analyze(source)))

    def test_profile_constraints(self):
        for key, original, invalid in (
            ("encryption", "none", "aes"), ("type", "tcp", "ws"),
            ("security", "reality", "tls"), ("flow", "xtls-rprx-vision", "other"),
            ("pbk", PUBLIC_KEY, "too-short"), ("sid", SHORT_ID, "f"),
            ("sid", SHORT_ID, "gg"), ("sid", SHORT_ID, "0" * 18),
            ("fp", "chrome", "%00"), ("sni", "synthetic-sni.example.invalid", "%20"),
        ):
            result = checker.analyze(link().replace(f"{key}={original}", f"{key}={invalid}"))
            self.assertFalse(result["ok"])
            self.assertIn("INVALID_" + key.upper() if invalid != "%20" else "MISSING_SNI", codes(result))

    def test_non_vless_and_damaged_subscription(self):
        self.assertIn("UNSUPPORTED_SCHEME", codes(checker.analyze("https://synthetic.example.invalid/private-token")))
        self.assertIn("INVALID_SUBSCRIPTION", codes(checker.analyze("bad ! subscription")))
        self.assertIn("EMPTY_INPUT", codes(checker.analyze("\n ")))
        self.assertIn("INVALID_TEXT", codes(checker.analyze("\ud800")))

    def test_limit_applies_to_bytes(self):
        self.assertIn("INPUT_TOO_LARGE", codes(checker.analyze("x" * (checker.MAX_INPUT_BYTES + 1))))
        self.assertIn("INPUT_TOO_LARGE", codes(checker.analyze("\u4e2d" * (checker.MAX_INPUT_BYTES // 3 + 1))))

    def test_expected_count_must_be_positive_integer(self):
        for invalid in (0, -1, True, "2", 1.5):
            self.assertIn("INVALID_EXPECT_COUNT", codes(checker.analyze(link(), invalid)))

    def test_output_never_contains_source_secrets(self):
        source = link().replace("#", "&privateKey=synthetic-private-secret&token=synthetic-subscription-token#")
        output = json.dumps(checker.analyze(source))
        for secret in (UUID_ONE, "synthetic.example.invalid", "synthetic-sni.example.invalid",
                       PUBLIC_KEY, SHORT_ID, "synthetic-private-secret", "synthetic-subscription-token", source):
            self.assertNotIn(secret, output)
        self.assertNotIn("broken-secret", json.dumps(checker.analyze(link().replace(":443", ":broken-secret"))))


class CliTests(unittest.TestCase):
    def run_cli(self, *args, source=b""):
        return subprocess.run([sys.executable, "-B", str(SCRIPT), *args], input=source,
                              capture_output=True, check=False)

    def test_stdin_and_file(self):
        result = self.run_cli(source=link().encode())
        self.assertEqual(result.returncode, 0)
        self.assertTrue(json.loads(result.stdout)["ok"])
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", prefix=".vless-test-", suffix=".txt",
            dir=Path(__file__).resolve().parent, delete=False,
        ) as handle:
            handle.write(link())
            source = Path(handle.name)
        try:
            result = self.run_cli("--input", str(source))
        finally:
            source.unlink()
        self.assertEqual(result.returncode, 0)
        self.assertTrue(json.loads(result.stdout)["ok"])

    def test_file_error_is_generic(self):
        result = self.run_cli("--input", "missing-synthetic-secret-file")
        self.assertEqual(result.returncode, 1)
        self.assertIn("INPUT_READ_FAILED", codes(json.loads(result.stdout)))
        self.assertNotIn(b"missing-synthetic-secret-file", result.stdout + result.stderr)

    def test_large_stream_and_invalid_utf8(self):
        result = self.run_cli(source=b"x" * (checker.MAX_INPUT_BYTES + 1))
        self.assertIn("INPUT_TOO_LARGE", codes(json.loads(result.stdout)))
        result = self.run_cli(source=b"\xffsynthetic-secret")
        self.assertIn("INVALID_TEXT", codes(json.loads(result.stdout)))
        self.assertNotIn(b"synthetic-secret", result.stdout + result.stderr)

    def test_argument_errors_are_generic(self):
        result = self.run_cli("--expect-count", "synthetic-secret")
        self.assertEqual(result.returncode, 2)
        self.assertIn("INVALID_ARGUMENTS", codes(json.loads(result.stdout)))
        self.assertNotIn(b"synthetic-secret", result.stdout + result.stderr)


if __name__ == "__main__":
    unittest.main()
