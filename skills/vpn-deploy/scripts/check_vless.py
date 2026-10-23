#!/usr/bin/env python3
"""Offline, non-disclosing checks for the VLESS + REALITY + Vision profile.

Read a local file or standard input. No network calls are made. This is a
distribution sanity check, not a connectivity test or a universal VLESS parser.
"""

import argparse
import base64
import binascii
import json
import re
import sys
import uuid
from urllib.parse import parse_qsl, unquote, urlsplit

MAX_INPUT_BYTES = 1024 * 1024
LIMITATIONS = [
    "Offline syntax checks cannot prove connectivity or server configuration.",
    "Only VLESS + REALITY + Vision over TCP/raw is supported.",
    "Duplicate UUIDs are rejected for this distribution-checking workflow.",
]


def _error(code, message, index=None):
    error = {"code": code, "message": message}
    if index is not None:
        error["index"] = index
    return error


def _result(count, errors):
    return {
        "ok": not errors,
        "count": count,
        "errors": errors,
        "limitations": list(LIMITATIONS),
    }


def _failure(code, message):
    return _result(0, [_error(code, message)])


def _decode_subscription(text):
    compact = "".join(text.split())
    if not compact or not re.fullmatch(r"[A-Za-z0-9+/_-]+={0,2}", compact):
        return None
    if len(compact) % 4 == 1:
        return None
    try:
        decoded = base64.b64decode(
            compact + "=" * (-len(compact) % 4), altchars=b"-_", validate=True
        )
        return decoded.decode("utf-8-sig")
    except (ValueError, binascii.Error, UnicodeError):
        return None


def _valid_public_key(value):
    if not re.fullmatch(r"[A-Za-z0-9_-]{43}=?", value):
        return False
    try:
        decoded = base64.b64decode(
            value.rstrip("=") + "=", altchars=b"-_", validate=True
        )
        return len(decoded) == 32 and (
            base64.urlsafe_b64encode(decoded).decode("ascii").rstrip("=")
            == value.rstrip("=")
        )
    except (ValueError, binascii.Error):
        return False


def _check_node(line, index, seen_uuids):
    errors = []

    def fail(code, message):
        errors.append(_error(code, message, index))

    # urlsplit otherwise silently strips some control characters.
    if any(ord(char) <= 32 or ord(char) == 127 for char in line) or re.search(
        r"%(?![0-9A-Fa-f]{2})", line
    ):
        fail("MALFORMED_URI", "A node is not a well-formed URI.")
        return errors
    try:
        parsed = urlsplit(line)
        if parsed.scheme.lower() != "vless":
            fail("UNSUPPORTED_SCHEME", "Only VLESS nodes are supported.")
            return errors
        if not line.lower().startswith("vless://") or parsed.path not in ("", "/"):
            fail("MALFORMED_URI", "A node is not a well-formed URI.")
            return errors
        hostname = parsed.hostname
        port = parsed.port
        username = parsed.username
        password = parsed.password
    except (ValueError, UnicodeError):
        fail("MALFORMED_URI", "A node is not a well-formed URI.")
        return errors

    if not hostname:
        fail("MISSING_HOST", "A node requires a host.")
    if port is None or not 1 <= port <= 65535:
        fail("INVALID_PORT", "A node requires a port between 1 and 65535.")
    try:
        if username is None or password is not None or parsed.netloc.count("@") != 1:
            raise ValueError
        node_uuid = uuid.UUID(unquote(username, errors="strict"))
        if node_uuid in seen_uuids:
            fail("DUPLICATE_UUID", "UUIDs must be unique for this distribution check.")
        seen_uuids.add(node_uuid)
    except (ValueError, UnicodeError):
        fail("INVALID_UUID", "A node requires a valid UUID.")

    try:
        pairs = parse_qsl(
            parsed.query, keep_blank_values=True, strict_parsing=True,
            encoding="utf-8", errors="strict", max_num_fields=128,
        )
    except (ValueError, UnicodeError):
        fail("MALFORMED_QUERY", "A node has an invalid parameter list.")
        return errors

    params = {}
    seen_keys = set()
    duplicate = False
    private_key = False
    for key, value in pairs:
        normalized_key = key.casefold()
        if normalized_key in seen_keys:
            duplicate = True
        seen_keys.add(normalized_key)
        if normalized_key.replace("_", "").replace("-", "") == "privatekey":
            private_key = True
        params[key] = value
    if duplicate:
        fail("DUPLICATE_PARAMETER", "A node contains repeated parameters.")
    if private_key:
        fail("PRIVATE_KEY_PRESENT", "A client link must not contain a private key.")

    required_values = {
        "encryption": {"none"},
        "type": {"tcp", "raw"},
        "security": {"reality"},
        "flow": {"xtls-rprx-vision"},
    }
    for key, allowed in required_values.items():
        if not params.get(key):
            fail("MISSING_" + key.upper(), "A required profile parameter is missing.")
        elif params[key] not in allowed:
            fail("INVALID_" + key.upper(), "A parameter does not match this profile.")
    for key in ("sni", "fp"):
        if not params.get(key) or not params[key].strip():
            fail("MISSING_" + key.upper(), "A required profile parameter is missing.")
        elif any(ord(char) <= 32 or ord(char) == 127 for char in params[key]):
            fail("INVALID_" + key.upper(), "A profile parameter contains invalid characters.")
    if not params.get("pbk"):
        fail("MISSING_PBK", "A required profile parameter is missing.")
    elif not _valid_public_key(params["pbk"]):
        fail("INVALID_PBK", "The public key must encode exactly 32 bytes as base64url.")
    if not params.get("sid"):
        fail("MISSING_SID", "A required profile parameter is missing.")
    elif not re.fullmatch(r"(?:[0-9A-Fa-f]{2}){1,8}", params["sid"]):
        fail("INVALID_SID", "The short ID must be nonempty, even-length hex of at most 16 characters.")
    return errors


def analyze(text, expect_count=1):
    """Return sanitized JSON-compatible results; never echo source values."""
    if isinstance(expect_count, bool) or not isinstance(expect_count, int) or expect_count < 1:
        return _failure("INVALID_EXPECT_COUNT", "The expected count must be a positive integer.")
    if not isinstance(text, str):
        return _failure("INVALID_TEXT", "Input must be UTF-8 text.")
    try:
        if len(text.encode("utf-8")) > MAX_INPUT_BYTES:
            return _failure("INPUT_TOO_LARGE", "Input exceeds the 1 MiB limit.")
    except UnicodeError:
        return _failure("INVALID_TEXT", "Input must be UTF-8 text.")
    text = text.lstrip("\ufeff").strip()
    if not text:
        return _failure("EMPTY_INPUT", "Input contains no nodes.")
    if "://" not in text:
        decoded = _decode_subscription(text)
        if decoded is None:
            return _failure("INVALID_SUBSCRIPTION", "Input is neither a plain URI list nor a valid base64 subscription.")
        text = decoded.strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    if not lines:
        return _failure("EMPTY_INPUT", "Input contains no nodes.")
    errors = []
    if len(lines) != expect_count:
        errors.append(_error("COUNT_MISMATCH", "The number of nodes does not match the expected count."))
    seen_uuids = set()
    for index, line in enumerate(lines, start=1):
        errors.extend(_check_node(line, index, seen_uuids))
    return _result(len(lines), errors)


class _ArgumentParser(argparse.ArgumentParser):
    def error(self, message):
        # argparse's original error can contain user-supplied argument values.
        print(json.dumps(_failure("INVALID_ARGUMENTS", "Invalid command-line arguments. Use --help.")))
        self.exit(2)


def main(argv=None):
    parser = _ArgumentParser(
        description=("Offline syntax checks for VLESS + REALITY + Vision over TCP/raw. "
                     "Cannot prove connectivity; other VLESS profiles are unsupported. "
                     "Reads a plain URI list or base64 subscription from a local file or stdin. "
                     "Never contacts a server or prints source credentials. Input limit: 1 MiB.")
    )
    parser.add_argument("--input", metavar="FILE", help="Read a UTF-8 local file instead of stdin.")
    parser.add_argument("--expect-count", type=int, default=1, metavar="N",
                        help="Expected node count; default: 1. Specify explicitly for multiple nodes.")
    args = parser.parse_args(argv)
    try:
        if args.input is not None:
            with open(args.input, "rb") as source:
                raw = source.read(MAX_INPUT_BYTES + 1)
        else:
            raw = sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    except (OSError, ValueError):
        result = _failure("INPUT_READ_FAILED", "Unable to read the input file or stream.")
    else:
        if len(raw) > MAX_INPUT_BYTES:
            result = _failure("INPUT_TOO_LARGE", "Input exceeds the 1 MiB limit.")
        else:
            try:
                result = analyze(raw.decode("utf-8-sig"), args.expect_count)
            except UnicodeError:
                result = _failure("INVALID_TEXT", "Input must be UTF-8 text.")
    print(json.dumps(result, ensure_ascii=True, indent=2))
    return 0 if result["ok"] else 1


if __name__ == "__main__":
    sys.exit(main())
