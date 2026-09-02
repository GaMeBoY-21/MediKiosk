# Owner: Nikki
"""Only one file in the kiosk may produce sound.

This is a frontend rule enforced from the Python suite because that is the
suite that actually runs (`python3 -m unittest discover -s ai`). There is no
JS test runner in this repo, and a rule nothing checks is a rule that lasts
until the next person adds a component.

The rule: the Web Speech API is reachable from exactly one file,
frontend/src/speech/useSpeechSynthesis.js. Everything else goes through the
`useSpeech()` hook, and the only control wired to it is the speaker button.

Why it needs a guard rather than a code review: sound that plays by itself is
invisible in a screenshot, in a diff, and in every test that stubs
speechSynthesis. It is only ever found by a person sitting in front of the
kiosk hearing something they did not ask for. Five call sites had accumulated
that way — tile taps, the consent toggles, the interview option tiles, the
idle-timeout warning and the language tiles — each one individually defensible
and collectively a kiosk that talks at a patient in a shared OPD hall.
"""

import pathlib
import re
import unittest

FRONTEND = pathlib.Path(__file__).resolve().parents[1] / "frontend/src"

# The single file allowed to touch the browser API.
OWNER = "speech/useSpeechSynthesis.js"

# The raw API. A component reaching for any of these is going around the hook.
RAW_API = re.compile(r"\b(speechSynthesis|SpeechSynthesisUtterance)\b")

# Call sites of the hook's speak(). Deliberate exceptions are listed here by
# file, and the list is the point: adding to it should take an argument.
#
#   Language.jsx   the only screen shown before a language exists, so it is the
#                  only place a patient who cannot read can discover that the
#                  speaker button exists at all. Once, guarded by hasSpoken.
#   Emergency.jsx  an alert, not an audio preference.
#   ListenButton   the speaker button itself: the one control that makes sound.
MAY_SPEAK = {
    "screens/Language.jsx",
    "screens/Emergency.jsx",
    "components/ListenButton.jsx",
}

SPEAK_CALL = re.compile(r"(?<![\w.])speak\s*\(")


def _sources():
    for path in sorted(FRONTEND.rglob("*.js*")):
        yield path, path.relative_to(FRONTEND).as_posix()


def _code_only(text: str) -> str:
    """Strip comments, so prose about speech does not count as speech."""
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.S)
    return "\n".join(re.sub(r"//.*$", "", line) for line in text.splitlines())


class TestOnlyOneFileTouchesTheSpeechAPI(unittest.TestCase):
    def test_raw_api_appears_in_exactly_one_file(self):
        offenders = []
        for path, rel in _sources():
            if rel == OWNER:
                continue
            if RAW_API.search(_code_only(path.read_text(encoding="utf-8"))):
                offenders.append(rel)
        self.assertEqual(
            offenders,
            [],
            f"these files reach the Web Speech API directly instead of going "
            f"through {OWNER}: {offenders}",
        )

    def test_the_owner_file_still_exists(self):
        """Otherwise the test above passes by finding nothing anywhere."""
        owner = FRONTEND / OWNER
        self.assertTrue(owner.is_file(), f"{OWNER} is gone; this guard is checking nothing")
        self.assertRegex(owner.read_text(encoding="utf-8"), RAW_API)


class TestOnlyTheButtonSpeaks(unittest.TestCase):
    def test_no_new_speak_call_sites(self):
        callers = set()
        for path, rel in _sources():
            if rel.startswith("speech/"):
                continue
            if SPEAK_CALL.search(_code_only(path.read_text(encoding="utf-8"))):
                callers.add(rel)
        self.assertEqual(
            callers,
            MAY_SPEAK,
            "the set of files that can produce sound changed. Adding one means "
            "the kiosk speaks without being asked to; removing one means a "
            "deliberate exception was lost.",
        )

    def test_tapping_a_tile_is_silent(self):
        """The specific regression: tiles used to read themselves back."""
        for rel in ("components/IconTile.jsx", "components/Toggle.jsx"):
            with self.subTest(component=rel):
                code = _code_only((FRONTEND / rel).read_text(encoding="utf-8"))
                self.assertNotIn("speak(", code, f"{rel} speaks when it is tapped")
                self.assertNotIn("useSpeech", code, f"{rel} still has a way to make sound")


if __name__ == "__main__":
    unittest.main()
