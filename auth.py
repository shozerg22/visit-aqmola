import os, jwt, time, uuid
from fastapi import Header, HTTPException, Request, Depends
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from database import get_session
from sqlalchemy.future import select
import models

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret")
JWT_TTL_SECONDS = int(os.getenv("JWT_TTL_SECONDS", "3600"))
REVOKED_JTIS: set[str] = set()


def issue_jwt(user: models.User):
    now = int(time.time())
    jti = uuid.uuid4().hex
    payload = {
        "sub": str(user.id),
        "role": user.role,
        "iat": now,
        "exp": now + JWT_TTL_SECONDS,
        "jti": jti,
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm="HS256")
    return token


async def resolve_user_from_jwt(token: str, db: AsyncSession) -> Optional[models.User]:
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
    except Exception:
        return None
    uid = data.get("sub")
    if not uid:
        return None
    res = await db.execute(select(models.User).where(models.User.id == int(uid)))
    return res.scalars().first()


from database import get_session


def _extract_token(auth_header: str | None) -> str | None:
    if auth_header and auth_header.startswith("Bearer "):
        return auth_header.split(" ", 1)[1].strip()
    return None

async def admin_required(request: Request, x_admin_token: str | None = Header(default=None), db: AsyncSession = Depends(get_session)):
    expected = os.getenv("ADMIN_TOKEN")
    auth_header = request.headers.get("Authorization")
    if expected and x_admin_token == expected:
        return True
    token = _extract_token(auth_header)
    if token:
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            if data.get("jti") in REVOKED_JTIS:
                raise HTTPException(status_code=401, detail="Token revoked")
            uid = data.get("sub")
            if uid:
                res = await db.execute(select(models.User).where(models.User.id == int(uid)))
                user = res.scalars().first()
                if user and user.role == 'admin':
                    return True
        except Exception:
            pass
    raise HTTPException(status_code=403, detail="Forbidden")

def roles_required(allowed: set[str]):
    async def _dep(request: Request, db: AsyncSession = Depends(get_session), x_admin_token: str | None = Header(default=None)):
        expected = os.getenv("ADMIN_TOKEN")
        auth_header = request.headers.get("Authorization")
        # Admin token bypass
        if expected and x_admin_token == expected:
            return True
        token = _extract_token(auth_header)
        if not token:
            raise HTTPException(status_code=403, detail="Forbidden")
        try:
            data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
            if data.get("jti") in REVOKED_JTIS:
                raise HTTPException(status_code=401, detail="Token revoked")
            uid = data.get("sub")
            if not uid:
                raise HTTPException(status_code=403, detail="Forbidden")
            res = await db.execute(select(models.User).where(models.User.id == int(uid)))
            user = res.scalars().first()
            if user and user.role in allowed:
                return True
        except HTTPException:
            raise
        except Exception:
            pass
        raise HTTPException(status_code=403, detail="Forbidden")
    return _dep
def revoke_jwt(token: str) -> bool:
    try:
        data = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        jti = data.get("jti")
        if jti:
            REVOKED_JTIS.add(jti)
            return True
    except Exception:
        return False
    return False

