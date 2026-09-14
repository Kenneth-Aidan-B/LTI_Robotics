"""LTI Robotics LMS — production-ready FastAPI backend + static frontend host."""
import os, json, re, secrets, sqlite3, threading, urllib.request, urllib.parse
from pathlib import Path
from fastapi import FastAPI, HTTPException, Depends, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, field_validator
from db import conn, init_db
from auth import hash_pw, check_pw, make_token, parse_token

init_db()
if os.getenv("LTI_JWT_SECRET", "lti-dev-secret-change-in-prod") == "lti-dev-secret-change-in-prod":
    print("WARNING: LTI_JWT_SECRET not set — using dev default. Set a 32+ char secret in production.")
app = FastAPI(title="LTI Robotics LMS", version="1.1.0")
app.add_middleware(CORSMiddleware, allow_origins=os.getenv("LTI_CORS_ORIGINS", "*").split(","), allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"])

# ---------- helpers ----------
def row(d): return dict(d) if d else None
def need_auth(req: Request):
    h = req.headers.get("authorization", "")
    if not h.lower().startswith("bearer "): raise HTTPException(401, "Missing token")
    payload = parse_token(h.split(" ",1)[1].strip())
    if not payload or "sub" not in payload: raise HTTPException(401, "Invalid/expired token")
    u = row(conn().execute("SELECT id,name,email,phone,role,grade,school,created_at FROM users WHERE id=?", (payload["sub"],)).fetchone())
    if not u: raise HTTPException(401, "User gone")
    return u
def need_admin(u=Depends(need_auth)):
    if u["role"] != "admin": raise HTTPException(403, "Admin only")
    return u

def notify_lead(lead: dict):
    """Fire-and-forget mail/Telegram hooks (configured later via env). Never breaks the request."""
    def _send(d: dict):
        try:
            tok, chat = os.getenv("TELEGRAM_BOT_TOKEN",""), os.getenv("TELEGRAM_CHAT_ID","")
            if tok and chat:
                txt = f"NEW LEAD: {d['name']} | {d['phone']} | {d['email']} | {d.get('grade','')} | {d.get('level','')}"
                data = urllib.parse.urlencode({"chat_id": chat, "text": txt}).encode()
                urllib.request.urlopen(urllib.request.Request(f"https://api.telegram.org/bot{tok}/sendMessage", data=data), timeout=6)
        except Exception as e: print("telegram hook failed:", e)
    threading.Thread(target=_send, args=(dict(lead),), daemon=True).start()

# ---------- models ----------
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
def _email(v: str) -> str:
    v = (v or "").strip().lower()
    if not EMAIL_RE.match(v): raise ValueError("bad email")
    return v

PHONE_RE = re.compile(r"^[+0-9][0-9\s\-()+]{5,19}$")
def _phone(v: str) -> str:
    v = (v or "").strip()
    if v:
        d = re.sub(r"\D", "", v)
        if len(d) < 7 or len(d) > 15 or re.search(r"[\"'<>`]", v) or not PHONE_RE.match(v):
            raise ValueError("bad phone")
    return v

class Register(BaseModel):
    name: str; email: str; password: str; phone: str = ""; grade: str = ""; school: str = ""; admin_code: str = ""
    @field_validator("name")
    @classmethod
    def nm(cls, v):
        v = (v or "").strip()
        if len(v) < 2: raise ValueError("name required")
        return v
    @field_validator("phone")
    @classmethod
    def rp(cls, v): return _phone(v)
    @field_validator("email")
    @classmethod
    def em(cls, v): return _email(v)
    @field_validator("password")
    @classmethod
    def pw(cls, v):
        if len(v) < 6: raise ValueError("min 6 chars")
        return v
class Login(BaseModel):
    email: str; password: str
    @field_validator("email")
    @classmethod
    def em(cls, v): return _email(v)
class LeadIn(BaseModel):
    name: str; phone: str; email: str; grade: str = ""; level: str = ""; school: str = ""; message: str = ""
    @field_validator("name")
    @classmethod
    def nn(cls, v):
        v = (v or "").strip()
        if len(v) < 2: raise ValueError("bad name")
        return v
    @field_validator("email")
    @classmethod
    def em(cls, v): return _email(v)
    @field_validator("phone")
    @classmethod
    def ph(cls, v): return _phone(v)
class CourseIn(BaseModel):
    id: str; title: str; subtitle: str = ""; duration_weeks: int = 12; sessions: int = 12
    coding: str = ""; kit: str = ""; eligibility: str = ""; builds: list = []; learn: list = []; weeks: list = []; outcome: str = ""
    @field_validator("id")
    @classmethod
    def cid(cls, v):
        v = (v or "").strip().lower()
        if not v or len(v) > 32 or not re.match(r"^[a-z0-9-]+$", v): raise ValueError("bad id")
        return v
    @field_validator("title")
    @classmethod
    def ti(cls, v):
        v = (v or "").strip()
        if len(v) < 3: raise ValueError("title required")
        return v
class EnrollIn(BaseModel): course_id: str
class ProgressIn(BaseModel): done: list[int]
class LeadStatus(BaseModel): status: str
class AnnounceIn(BaseModel): title: str; body: str = ""

# ---------- auth ----------
@app.post("/api/register")
def register(b: Register):
    role = "learner"
    _code = os.getenv("LTI_ADMIN_CODE", "")
    if b.admin_code and _code and secrets.compare_digest(b.admin_code, _code): role = "admin"
    c = conn()
    if c.execute("SELECT id FROM users WHERE email=?", (b.email.lower(),)).fetchone(): raise HTTPException(409, "Email exists")
    c.execute("INSERT INTO users(name,email,phone,password_hash,role,grade,school) VALUES(?,?,?,?,?,?,?)",
              (b.name.strip(), b.email.lower(), b.phone, hash_pw(b.password), role, b.grade, b.school))
    c.commit()
    u = row(c.execute("SELECT id,name,email,phone,role,grade,school,created_at FROM users WHERE email=?", (b.email.lower(),)).fetchone())
    c.close(); return {"token": make_token(u), "user": u}

@app.post("/api/login")
def login(b: Login):
    c = conn(); r = c.execute("SELECT * FROM users WHERE email=?", (b.email.lower(),)).fetchone(); c.close()
    if not r or not check_pw(b.password, r["password_hash"]): raise HTTPException(401, "Bad credentials")
    u = {k: r[k] for k in ("id","name","email","phone","role","grade","school","created_at")}
    return {"token": make_token(u), "user": u}

@app.get("/api/me")
def me(u=Depends(need_auth)): return u

# ---------- courses ----------
@app.get("/api/courses")
def courses():
    c = conn(); rows = c.execute("SELECT * FROM courses WHERE active=1 ORDER BY id").fetchall(); c.close()
    out = []
    for r in rows:
        d = row(r)
        for k in ("builds","learn","weeks"): d[k] = json.loads(d[k] or "[]")
        out.append(d)
    return out

@app.post("/api/courses")
def upsert_course(b: CourseIn, _=Depends(need_admin)):
    c = conn()
    payload = {"id": b.id.strip(), "title": b.title, "subtitle": b.subtitle, "duration_weeks": b.duration_weeks,
      "sessions": b.sessions, "coding": b.coding, "kit": b.kit, "eligibility": b.eligibility,
      "builds": json.dumps(b.builds), "learn": json.dumps(b.learn), "weeks": json.dumps(b.weeks), "outcome": b.outcome}
    if c.execute("SELECT id FROM courses WHERE id=?", (payload["id"],)).fetchone():
        c.execute("UPDATE courses SET title=:title,subtitle=:subtitle,duration_weeks=:duration_weeks,sessions=:sessions,coding=:coding,kit=:kit,eligibility=:eligibility,builds=:builds,learn=:learn,weeks=:weeks,outcome=:outcome WHERE id=:id", payload)
    else: c.execute("INSERT INTO courses(id,title,subtitle,duration_weeks,sessions,coding,kit,eligibility,builds,learn,weeks,outcome) VALUES(:id,:title,:subtitle,:duration_weeks,:sessions,:coding,:kit,:eligibility,:builds,:learn,:weeks,:outcome)", payload)
    c.commit(); c.close(); return {"ok": True}

# ---------- enroll + progress ----------
@app.post("/api/enroll")
def enroll(b: EnrollIn, u=Depends(need_auth)):
    cid = (b.course_id or "").strip()
    if not cid: raise HTTPException(422, "course_id required")
    c = conn()
    if not c.execute("SELECT id FROM courses WHERE id=?", (cid,)).fetchone(): raise HTTPException(404, "No course")
    try:
        c.execute("INSERT INTO enrollments(user_id,course_id) VALUES(?,?)", (u["id"], cid)); c.commit()
    except sqlite3.IntegrityError:
        pass
    e = row(c.execute("SELECT * FROM enrollments WHERE user_id=? AND course_id=?", (u["id"], cid)).fetchone()); c.close()
    e["progress"] = json.loads(e["progress"] or "[]"); return e

@app.get("/api/my-enrollments")
def mine(u=Depends(need_auth)):
    c = conn(); rows = c.execute("SELECT e.*, c.title, c.sessions, c.weeks FROM enrollments e JOIN courses c ON c.id=e.course_id WHERE e.user_id=?", (u["id"],)).fetchall(); c.close()
    out = []
    for r in rows:
        d = row(r); d["progress"] = json.loads(d["progress"] or "[]"); d["weeks"] = json.loads(d["weeks"] or "[]")
        d["pct"] = round(100*len(d["progress"])/max(1,d["sessions"]))
        d["certificate"] = d["pct"] == 100
        out.append(d)
    return out

@app.post("/api/enrollments/{eid}/progress")
def progress(eid: int, b: ProgressIn, u=Depends(need_auth)):
    c = conn(); e = c.execute("SELECT * FROM enrollments WHERE id=?", (eid,)).fetchone()
    if not e: raise HTTPException(404, "No enrollment")
    if u["role"] != "admin" and e["user_id"] != u["id"]: raise HTTPException(403, "Not yours")
    sess = c.execute("SELECT sessions FROM courses WHERE id=?", (e["course_id"],)).fetchone()["sessions"]
    try: idx = [int(x) for x in b.done]
    except Exception: raise HTTPException(422, "bad indices")
    bad = [x for x in idx if not 0 <= x < sess]
    if bad: raise HTTPException(422, f"bad indices {bad} for sessions={sess}")
    done = sorted(set(idx))
    c.execute("UPDATE enrollments SET progress=? WHERE id=?", (json.dumps(done), eid)); c.commit(); c.close()
    return {"ok": True, "done": done, "pct": round(100*len(done)/max(1,sess))}

@app.get("/api/admin/enrollments")
def all_enroll(_=Depends(need_admin)):
    c = conn(); rows = c.execute("SELECT e.*, u.name, u.email, c.title FROM enrollments e JOIN users u ON u.id=e.user_id JOIN courses c ON c.id=e.course_id ORDER BY e.id DESC").fetchall(); c.close()
    return [row(r) for r in rows]

# ---------- leads ----------
@app.post("/api/leads")
def create_lead(b: LeadIn):
    c = conn()
    cur = c.execute("INSERT INTO leads(name,phone,email,grade,level,school,message) VALUES(?,?,?,?,?,?,?)",
              (b.name.strip(), b.phone.strip(), str(b.email).lower(), b.grade, b.level, b.school, b.message))
    c.commit(); lid = cur.lastrowid; c.close()
    lead = {"id": lid, **b.model_dump()}
    notify_lead(lead); return {"ok": True, "id": lid}

@app.get("/api/admin/leads")
def leads(_=Depends(need_admin)):
    c = conn(); rows = c.execute("SELECT * FROM leads ORDER BY id DESC").fetchall(); c.close()
    return [row(r) for r in rows]

@app.post("/api/admin/leads/{lid}")
def lead_status(lid: int, b: LeadStatus, _=Depends(need_admin)):
    if b.status not in ("new","contacted","enrolled","closed"): raise HTTPException(400, "bad status")
    c = conn(); cur = c.execute("UPDATE leads SET status=? WHERE id=?", (b.status, lid)); c.commit()
    if cur.rowcount == 0: c.close(); raise HTTPException(404, "No lead")
    c.close(); return {"ok": True}

# ---------- users + announcements + stats ----------
@app.get("/api/admin/users")
def users(_=Depends(need_admin)):
    c = conn(); rows = c.execute("SELECT id,name,email,phone,role,grade,school,created_at FROM users ORDER BY id").fetchall(); c.close()
    return [row(r) for r in rows]

@app.get("/api/announcements")
def ann_list(u=Depends(need_auth)):
    c = conn(); rows = c.execute("SELECT * FROM announcements ORDER BY id DESC LIMIT 20").fetchall(); c.close()
    return [row(r) for r in rows]

@app.post("/api/announcements")
def ann_add(b: AnnounceIn, _=Depends(need_admin)):
    if not (b.title or "").strip(): raise HTTPException(422, "title required")
    c = conn(); c.execute("INSERT INTO announcements(title,body) VALUES(?,?)", (b.title.strip(), b.body)); c.commit(); c.close()
    return {"ok": True}

@app.get("/api/admin/stats")
def stats(_=Depends(need_admin)):
    c = conn()
    s = {"users": c.execute("SELECT COUNT(*) n FROM users").fetchone()["n"],
         "learners": c.execute("SELECT COUNT(*) n FROM users WHERE role='learner'").fetchone()["n"],
         "enrollments": c.execute("SELECT COUNT(*) n FROM enrollments").fetchone()["n"],
         "leads": c.execute("SELECT COUNT(*) n FROM leads").fetchone()["n"],
         "new_leads": c.execute("SELECT COUNT(*) n FROM leads WHERE status='new'").fetchone()["n"]}
    c.close(); return s

@app.get("/api/health")
def health(): return {"ok": True, "app": "LTI Robotics LMS"}

# ---------- frontend host ----------
FRONT = Path(__file__).parent.parent / "frontend"
if FRONT.exists():
    app.mount("/", StaticFiles(directory=FRONT, html=True), name="front")
