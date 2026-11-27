import os
from typing import Annotated

from fastapi import Depends, Request

COOKIE_JETON = "access_token"
# true par défaut : un oubli de config donne un cookie trop protégé, pas l'inverse
COOKIE_SECURE = os.environ.get("COOKIE_SECURE", "true").lower() == "true"


def get_token(request: Request) -> str | None:
    return request.cookies.get(COOKIE_JETON)


Token = Annotated[str | None, Depends(get_token)]
