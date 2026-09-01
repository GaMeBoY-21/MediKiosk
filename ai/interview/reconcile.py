# Owner: Nikki
"""Fill in fields that are already implicit in ones the patient has answered.

Runs after every extraction and BEFORE the state machine decides what is still
unfilled. Without it the kiosk asked "where on your body?" of a patient who had
just said "back pain": the model folds the site into chief_complaint,
symptom_site stays empty, the state machine sees a required field missing and
re-asks, and the model folds it in again. Same question, same answer, forever —
until a follow-up cap happens to break the tie.

The cap is the seatbelt, not the fix. The fix is that "back pain" answers
"where" and something has to say so before anyone decides to ask.

Deterministic. No model call. Every derivation here comes from
ai/knowledge/body_regions.py, so it behaves the same on every turn of every
session, which is exactly what the model could not be relied on to do.

Two rules hold everywhere in this module:

  1. Never overwrite. A value the patient gave — spoken or tapped — always
     beats one we inferred. Derivation only ever fills a hole.
  2. Never guess. A complaint that does not name a region derives no region.
     "joint pain" leaves symptom_site empty on purpose, because "which joint?"
     is a question worth asking. An absent field is recoverable; a confidently
     wrong one is read by the physician as fact.
"""

import logging

from ai.knowledge.body_regions import duration_token, site_for_complaint

log = logging.getLogger(__name__)

# Fields that may carry a duration the patient has already stated. Ordered:
# the first one that yields a token wins, so an explicit duration answer beats
# a duration mentioned in passing inside the complaint.
_DURATION_SOURCES = ("symptom_duration", "symptom_onset", "chief_complaint")

# Fields that may name the body region. symptom_site itself is excluded — it is
# the thing being derived.
_SITE_SOURCES = ("chief_complaint",)


def derive_fields(fields: dict) -> dict:
    """Fields implicit in `fields` that are not yet recorded.

    Returns only the NEW values, so the caller can attribute them separately
    (source=derived) and log them. Returns {} when nothing can be derived.
    """
    derived: dict = {}

    site = _derive_site(fields)
    if site:
        derived["symptom_site"] = site

    duration = _derive_duration(fields)
    if duration:
        # A patient saying "back pain since today" has answered both "how
        # long?" and "when did it start?" — they are the same sentence to them,
        # and asking twice is the same re-ask loop wearing a different label.
        # symptom_duration gates the chief_complaint node, symptom_onset gates
        # hpi, so filling only one still leaves the patient asked twice.
        for name in ("symptom_duration", "symptom_onset"):
            if not _has(fields, name):
                derived[name] = duration

    if derived:
        log.info("reconciled %s from fields already captured", sorted(derived))
    return derived


def reconcile(fields: dict) -> dict:
    """`fields` with its implicit values filled in. Does not mutate the input."""
    merged = dict(fields)
    merged.update(derive_fields(fields))
    return merged


def _has(fields: dict, name: str) -> bool:
    """True when a field carries a real value.

    "" and [] are holes, not answers: extraction drops empty values, but a
    seeded or tapped field can still arrive empty, and treating one as filled
    would suppress a question that genuinely needs asking.
    """
    value = fields.get(name)
    if value is None:
        return False
    if isinstance(value, (str, list, tuple, dict)):
        return len(value) > 0
    return True


def _derive_site(fields: dict) -> str:
    if _has(fields, "symptom_site"):
        return ""
    for name in _SITE_SOURCES:
        if not _has(fields, name):
            continue
        site = site_for_complaint(fields[name])
        if site:
            return site
    return ""


def _derive_duration(fields: dict) -> str:
    if _has(fields, "symptom_duration") and _has(fields, "symptom_onset"):
        return ""
    for name in _DURATION_SOURCES:
        if not _has(fields, name):
            continue
        token = duration_token(fields[name])
        if token:
            return token
    return ""
