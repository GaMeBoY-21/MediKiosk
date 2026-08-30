# Owner: Tharun
"""ABHA verification — MOCKED.

THIS PERFORMS NO REAL VERIFICATION. There is no ABDM gateway call, no network
request, and no check that the number belongs to anybody. It accepts any
14-digit number and returns a fabricated patient record after a short delay.

The word MOCKED appears in this docstring, in every response payload, in the
`mocked: true` flag and in a server log line on every call, so that:
  - nobody downstream mistakes a demo response for a verified identity, and
  - the pitch can say "ABHA verification is mocked" and be demonstrably honest.

Real integration requires ABDM sandbox credentials and an auth flow (the patient
authorises via OTP against their own ABHA); the kiosk would never hold the
number itself. Wiring that is out of scope until we have gateway access.
"""

from __future__ import annotations

import asyncio
import logging
import re

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session as DbSession

from app import models
from app.database import get_db
from app.schemas import AbhaVerifyRequest, AbhaVerifyResponse, Identity, Sex

log = logging.getLogger(__name__)
router = APIRouter(prefix="/identity", tags=["identity"])

MOCK_DELAY_SECONDS = 0.5
ABHA_DIGITS = 14

NOTICE = "MOCKED: no ABDM gateway call was made. This identity is fabricated."

# Returned for any well-formed number. Obviously fictitious on purpose.
_DEMO_IDENTITY = Identity(
    name="Lakshmi Devi",
    age=65,
    sex=Sex.female,
)


def _normalise(abha_id: str) -> str:
    """Strip the separators people type: 14-1234-5678-9012 -> 14123456789012."""
    return re.sub(r"[^0-9]", "", abha_id or "")


@router.post("/abha/verify", response_model=AbhaVerifyResponse)
async def verify_abha(payload: AbhaVerifyRequest, db: DbSession = Depends(get_db)):
    """Pretend to verify an ABHA number. MOCKED — see the module docstring.

    Accepts any 14-digit number. The delay exists so the kiosk's "Checking"
    state is visible during a demo, not because work is happening.
    """
    digits = _normalise(payload.abha_id)
    verified = len(digits) == ABHA_DIGITS

    await asyncio.sleep(MOCK_DELAY_SECONDS)

    log.warning("MOCKED ABHA verification for ****%s -> %s", digits[-4:] or "????", verified)

    identity = None
    if verified:
        identity = _DEMO_IDENTITY.model_copy(update={"abha_id": digits})

    # Audited like any other identity lookup. Only the last four digits are
    # written; the full number never reaches the audit trail.
    models.write_audit(
        db,
        action="identity.abha_verify_mocked",
        actor="kiosk",
        detail={"last4": digits[-4:], "verified": verified, "mocked": True},
    )
    db.commit()

    return AbhaVerifyResponse(
        mocked=True,
        verified=verified,
        abha_id=digits if verified else None,
        identity=identity,
        notice=NOTICE,
    )
