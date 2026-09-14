import os, datetime, jwt, bcrypt

SECRET = os.getenv("LTI_JWT_SECRET", "lti-dev-secret-change-in-prod")
ALGO = "HS256"
EXP_HOURS = int(os.getenv("LTI_JWT_HOURS", "72"))

def hash_pw(p: str) -> str:
    return bcrypt.hashpw(p.encode(), bcrypt.gensalt()).decode()

def check_pw(p: str, h: str) -> bool:
    try: return bcrypt.checkpw(p.encode(), h.encode())
    except Exception: return False

def make_token(user: dict) -> str:
    exp = datetime.datetime.utcnow() + datetime.timedelta(hours=EXP_HOURS)
    return jwt.encode({"sub": str(user["id"]), "role": user["role"], "exp": exp}, SECRET, algorithm=ALGO)

def parse_token(t: str):
    try: return jwt.decode(t, SECRET, algorithms=[ALGO])
    except Exception: return None
