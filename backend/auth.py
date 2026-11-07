"""One passphrase locks the site. Not production auth, just a door (see the plan)."""

import hmac
import os
from typing import Annotated

from fastapi import Depends, Header, HTTPException, status


def require_passphrase(x_passphrase: Annotated[str | None, Header()] = None) -> None:
    expected = os.environ.get("SITE_PASSPHRASE", "")
    if not expected:
        # Fail closed: a missing env var must never mean "open to everyone".
        raise HTTPException(status.HTTP_503_SERVICE_UNAVAILABLE, "SITE_PASSPHRASE is not configured")
    if not hmac.compare_digest((x_passphrase or "").encode(), expected.encode()):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "wrong passphrase")


Locked = [Depends(require_passphrase)]
