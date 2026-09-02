#!/usr/bin/env python3
# Owner: Nikki
"""Call Google once per key and report which ones actually work.

`./dev.sh --check` counts the keys in app/.env. It cannot tell you whether
they are real, because it makes no network call. That gap is not theoretical:
a rehearsal had five keys present, five slots reported by the preflight, and
all five rejected by Google as API_KEY_INVALID. The preflight was green the
whole time.

An invalid key is worse than a missing one. The pool fails over on QUOTA
errors, and an invalid key is an auth error, so it does NOT step past it —
one bad key in slot 1 fails every request while four good keys sit unused.
Run this before a demo.

Key values are never printed, and are stripped out of any error text before
it is shown.

    python3 scripts/check_keys.py
"""

import pathlib
import re
import sys

ROOT = pathlib.Path(__file__).resolve().parents[1]
ENV_FILE = ROOT / "app/.env"
KEY_NAMES = ("GEMINI_API_KEY", *[f"GEMINI_API_KEY_{n}" for n in range(1, 6)])


def read_env(path: pathlib.Path) -> dict:
    values: dict[str, str] = {}
    if not path.is_file():
        return values
    for line in path.read_text().splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        name, value = line.split("=", 1)
        values[name.strip()] = value.strip().strip('"').strip("'")
    return values


def scrub(text: str, secrets) -> str:
    """Never let a key reach the terminal, even inside an error message."""
    for secret in secrets:
        if secret:
            text = text.replace(secret, "<redacted>")
    text = re.sub(r"(?i)(api[_-]?key\s*[=:]\s*)\S+", r"\1<redacted>", text)
    return " ".join(text.split())


def main() -> int:
    env = read_env(ENV_FILE)
    if not env:
        print(f"cannot read {ENV_FILE}")
        return 2

    model = env.get("GEMINI_MODEL")
    if not model:
        print("GEMINI_MODEL is not set in app/.env")
        return 2

    secrets = [env.get(n) for n in KEY_NAMES]
    slots = [(n, env.get(n)) for n in KEY_NAMES if env.get(n)]
    if not slots:
        print("no Gemini keys set in app/.env")
        return 2

    try:
        import google.generativeai as genai
    except ImportError:
        print("google-generativeai is not installed; run ./dev.sh --check first")
        return 2

    print(f"testing {len(slots)} key(s) against {model}\n")
    working = 0
    for name, key in slots:
        try:
            genai.configure(api_key=key)
            genai.GenerativeModel(model).generate_content("Say OK")
            print(f"  {name:18} WORKS")
            working += 1
        except Exception as exc:  # the SDK raises its own exception types
            print(f"  {name:18} FAILS  {scrub(str(exc), secrets)[:88]}")

    print(f"\n{working} of {len(slots)} key(s) usable.")
    if working == 0:
        print("NOTHING WILL WORK LIVE. Fix the keys, or demo with ./dev.sh --replay.")
        return 1
    if working < len(slots):
        print("Blank the failing lines in app/.env so the pool does not waste a call on them.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
