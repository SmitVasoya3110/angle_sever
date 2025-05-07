from datetime import datetime, timedelta
from jose import jwt

SECRET_KEY = "your-very-secret-key"
ALGORITHM = "HS256"
TOKEN_EXPIRY_DAYS = 30

def create_jwt_tokens(user_id: str):
    now = datetime.now()
    expire = now + timedelta(days=TOKEN_EXPIRY_DAYS)

    access_payload = {
        "sub": user_id,
        "exp": expire
    }

    refresh_payload = {
        "sub": user_id,
        "exp": expire
    }

    access_token = jwt.encode(access_payload, SECRET_KEY, algorithm=ALGORITHM)
    refresh_token = jwt.encode(refresh_payload, SECRET_KEY, algorithm=ALGORITHM)

    return access_token, refresh_token
