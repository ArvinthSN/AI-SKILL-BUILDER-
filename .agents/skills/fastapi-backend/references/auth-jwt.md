# JWT Authentication

Install: `pip install pyjwt "pwdlib[argon2]"`

## Helpers (`app/core/security.py`)
```python
from datetime import datetime, timedelta, timezone
import jwt
from pwdlib import PasswordHash
from app.core.config import settings

password_hash = PasswordHash.recommended()

def hash_password(p: str) -> str:
    return password_hash.hash(p)

def verify_password(p: str, hashed: str) -> bool:
    return password_hash.verify(p, hashed)

def create_access_token(subject: str, minutes: int = 30) -> str:
    exp = datetime.now(timezone.utc) + timedelta(minutes=minutes)
    return jwt.encode({"sub": subject, "exp": exp}, settings.secret_key, algorithm="HS256")
```

## Protected route dependency
```python
from fastapi import Depends, HTTPException
from fastapi.security import OAuth2PasswordBearer
import jwt

oauth2 = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

def get_current_user_id(token: str = Depends(oauth2)) -> str:
    try:
        return jwt.decode(token, settings.secret_key, algorithms=["HS256"])["sub"]
    except jwt.PyJWTError:
        raise HTTPException(401, "Invalid or expired token")
```

## Rules
- Never store plain passwords.
- `SECRET_KEY` comes from env; generate with `openssl rand -hex 32`.
- Keep token lifetime short; add refresh tokens only if needed.
