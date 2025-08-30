import os, time
from typing import Optional
from fastapi import Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import jwt, JWTError

SECRET_KEY = os.getenv("SECRET_KEY", "change-this-in-prod")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_SECONDS = int(os.getenv("ACCESS_TOKEN_EXPIRE_SECONDS", str(7*24*3600)))
AUTH_REQUIRED = os.getenv("AUTH_REQUIRED", "false").lower() == "true"

bearer = HTTPBearer(auto_error=False)

def create_access_token(sub: str, expires_seconds: int = ACCESS_TOKEN_EXPIRE_SECONDS) -> str:
    now = int(time.time())
    payload = {"sub": sub, "iat": now, "exp": now + expires_seconds}
    return jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)

def _decode_token(token: str) -> Optional[dict]:
    try:
        return jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return None

def ensure_auth(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> Optional[str]:
    if not AUTH_REQUIRED:
        return None  # open mode
    if creds is None or not creds.scheme.lower().startswith("bearer"):
        raise HTTPException(status_code=401, detail="Not authenticated")
    payload = _decode_token(creds.credentials)
    if not payload:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return payload.get("sub") or "user"
