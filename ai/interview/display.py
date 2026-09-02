# Owner: Nikki
"""How an extracted value is SHOWN to the patient, as opposed to what it is.

The understanding panel is the screen that tells a patient the kiosk heard
them. It was rendering canonical tokens — "1_day", "male", "throbbing" — so a
Telugu speaker read English, and in the worst case read an underscore.

The split this module exists to keep:

  value    canonical, English, machine-readable. Red-flag rules, the summary,
           storage and the FHIR builder all read this and nothing else, which
           is why a chest-pain red flag fires identically in all seven
           languages. It must never change to make a screen read better.

  display  the same answer as the patient should see it, in their language.
           For anything the patient tapped, that string already exists: it is
           the label of the option they touched, which the model wrote in
           their language and which danger_symptoms.py translates for the
           safety tiles. There is nothing to translate here, only to keep.

Free speech has no option list to borrow from, so the value is opened out
rather than invented: "1_day" -> "1 day". Honest about being the raw value,
without showing the patient a token.
"""

from typing import Any, Iterable, Optional

# Values that are already ordinary words in any language are left alone; there
# is nothing to open out and sentence-casing them only makes them shoutier.
_ALREADY_READABLE = {"yes", "no"}


def humanise(value: Any) -> str:
    """Open a canonical token out into something a person can read.

    Not a translation and not claiming to be one: this is the fallback for a
    field filled from free speech, where no label was ever generated. It fixes
    the part that is indefensible in any language — the underscores — and
    leaves the rest.
    """
    if value is None:
        return ""
    if isinstance(value, bool):
        return "yes" if value else "no"
    if isinstance(value, (list, tuple)):
        return ", ".join(humanise(v) for v in value if v is not None and v != "")

    text = str(value).strip()
    if not text:
        return ""
    text = text.replace("_", " ")
    if text.lower() in _ALREADY_READABLE:
        return text
    # Sentence case, not .capitalize(): that lowercases everything after the
    # first letter and would turn "MRI scan" into "Mri scan". Scripts without
    # case are unaffected either way.
    return text[0].upper() + text[1:]


def label_for(value: Any, options: Optional[Iterable] = None) -> Optional[str]:
    """The patient-language label for a value, from the options we sent.

    Covers the tapped answer and the spoken one that happens to match an
    option we offered — the user said "mild" and mild was on screen — because
    in both cases the translated string already exists and the only mistake
    available to us is to throw it away.

    Returns None when there is no option list or nothing matches, which is the
    caller's signal to fall back to `humanise`.
    """
    if value is None or not options:
        return None

    index = {}
    for opt in options:
        opt_value = opt.get("value") if isinstance(opt, dict) else getattr(opt, "value", None)
        opt_label = opt.get("label") if isinstance(opt, dict) else getattr(opt, "label", None)
        if opt_value is None or not opt_label:
            continue
        index[str(opt_value)] = opt_label

    if isinstance(value, (list, tuple)):
        labels = [index.get(str(v)) for v in value]
        # All or nothing. A half-translated list reads as a bug rather than as
        # an answer, so if any element is unknown the caller falls back for
        # the whole field.
        if labels and all(labels):
            return ", ".join(labels)
        return None

    return index.get(str(value))


def inherited_label(name: str, value: Any, values: dict, labels: dict) -> Optional[str]:
    """The label of another field holding this exact answer.

    reconcile.py fills symptom_onset from symptom_duration: one answer, two
    fields, the same value. Only one of them was ever put on screen as options,
    so only one has a label — and without this the other renders the raw token
    beside its translated twin ("ఒక రోజు" on one row, "1 day" on the next).
    """
    if value is None or value == "":
        return None
    for other, other_value in values.items():
        if other != name and other_value == value and labels.get(other):
            return labels[other]
    return None


def display_for(value: Any, options: Optional[Iterable] = None) -> str:
    """The string the panel should render for this value. Never a raw token."""
    return label_for(value, options) or humanise(value)
