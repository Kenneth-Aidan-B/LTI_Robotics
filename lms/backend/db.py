"""SQLite store + seed for LTI Robotics LMS. Grades 4+, 9+ builds, L3 Coding with Arduino."""
import sqlite3, os, json
from pathlib import Path

DB_PATH = Path(os.getenv("LTI_DB", str(Path(__file__).parent / "lti.db")))

SCHEMA = """
CREATE TABLE IF NOT EXISTS users(
 id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, phone TEXT DEFAULT '',
 password_hash TEXT NOT NULL, role TEXT NOT NULL DEFAULT 'learner',
 grade TEXT DEFAULT '', school TEXT DEFAULT '', created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS courses(
 id TEXT PRIMARY KEY, title TEXT NOT NULL, subtitle TEXT DEFAULT '',
 duration_weeks INTEGER, sessions INTEGER, coding TEXT DEFAULT '',
 kit TEXT DEFAULT '', eligibility TEXT DEFAULT '', builds TEXT DEFAULT '[]',
 learn TEXT DEFAULT '[]', weeks TEXT DEFAULT '[]', outcome TEXT DEFAULT '',
 active INTEGER DEFAULT 1
);
CREATE TABLE IF NOT EXISTS enrollments(
 id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, course_id TEXT NOT NULL,
 status TEXT DEFAULT 'active', progress TEXT DEFAULT '[]', created_at TEXT DEFAULT (datetime('now')),
 UNIQUE(user_id, course_id)
);
CREATE TABLE IF NOT EXISTS leads(
 id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, phone TEXT NOT NULL, email TEXT NOT NULL,
 grade TEXT DEFAULT '', level TEXT DEFAULT '', school TEXT DEFAULT '', message TEXT DEFAULT '',
 status TEXT DEFAULT 'new', created_at TEXT DEFAULT (datetime('now'))
);
CREATE TABLE IF NOT EXISTS announcements(
 id INTEGER PRIMARY KEY AUTOINCREMENT, title TEXT NOT NULL, body TEXT DEFAULT '', created_at TEXT DEFAULT (datetime('now'))
);
"""

SEED_COURSES = [
 {"id":"lvl1","title":"Level 1 — Sensor Robotics with L293N","subtitle":"Foundation — Electronics to First Robot",
  "duration_weeks":12,"sessions":12,"coding":"None","kit":"Rs 2,000+ value robotics kit FREE","eligibility":"Grade 4+, no prerequisites",
  "builds":["Simple LED Circuit","Motor Spin Test","IR Sensor Test","Sensor+Motor Dry Run","Line Following Robot","Obstacle Avoiding Robot","Edge Avoiding Robot","Wall Following Robot","Object Following Robot"],
  "learn":["Current, voltage, complete circuits","Conductors vs insulators","DC motors + L293N","IR HIGH/LOW logic","Sensor-to-motor logic","Wiring & troubleshooting"],
  "weeks":["Orientation, safety, kit walkthrough","LED circuit","Motor spin test — L293N intro","IR sensor logic","Sensor+motor dry run","Chassis + Line start","Line finish + Obstacle start","Obstacle finish + Edge start","Edge finish + Wall start","Wall finish + Object start","Object full build & test","Showcase + Certificates"],
  "outcome":"Showcase 1 robot · Certificate + Badges: Circuit Builder, Motor Control, Sensor Specialist, Robot Builder"},
 {"id":"lvl2","title":"Level 2 — Breadboard Logic & Robotics","subtitle":"Real Circuits. Real Logic. Real Innovators.",
  "duration_weeks":12,"sessions":12,"coding":"None — logic ICs","kit":"Breadboard + L293D + 7404/7400 + HT12E/HT12D + 433MHz RF","eligibility":"Completion of Level 1",
  "builds":["Discrete IR circuit","Line (breadboard)","Obstacle (breadboard)","Edge (breadboard)","Wall (breadboard)","Object (breadboard)","7404 bidirectional upgrade","Robo Shuttler 2x7400","Wireless RC Car"],
  "learn":["Breadboard building","L293D from scratch","IC 7404 NOT","IC 7400 NAND latch","HT12E/HT12D + RF","Real-circuit debugging"],
  "weeks":["Discrete IR from scratch","Breadboard + L293D + chassis","Line (breadboard)","Obstacle","Edge","Wall","Object","7404 upgrade","Robo Shuttler 7400","RC TX HT12E","RC RX HT12D + integration","Showcase + Certificates"],
  "outcome":"Showcase wireless RC car · Certificate + Badges: Logic Builder, Circuit Designer, Problem Solver, Wireless Innovator"},
 {"id":"lvl3","title":"Level 3 — Coding Robotics with Arduino","subtitle":"Code. Innovate. Automate.",
  "duration_weeks":16,"sessions":16,"coding":"Arduino C/C++","kit":"Arduino UNO + sensors + HC-05 + remote + TSOP1738 + servo/LCD/relay","eligibility":"Completion of Level 2",
  "builds":["Line (Arduino coded)","Obstacle (Arduino coded)","TV Remote Controlled Robot","Bluetooth Controlled Robot","Line-Following Automation System"],
  "learn":["IDE, setup/loop, variables","Digital/analog + Serial","Ultrasonic/IR/temp/sound","Buzzer/servo/LCD/relay/HC-05","Coded L293D functions","TSOP1738 decode"],
  "weeks":["IDE + Blink","C basics + LEDs","Pushbutton + conditionals","Analog + Serial","Ultrasonic","IR with Arduino","Temp logic","Sound/buzzer/servo","LCD/relay/HC-05","Coded motors","Line rebuild","Obstacle rebuild","TV remote decode","TV robot wiring","Buffer/troubleshoot","Showcase + Certificates"],
  "outcome":"Showcase TV-remote robot · Certificate + Badges: Arduino Coder, Automation Specialist, Problem Solver, Innovator"},
]

def conn():
    c = sqlite3.connect(DB_PATH); c.row_factory = sqlite3.Row; return c

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    c = conn(); c.executescript(SCHEMA)
    for course in SEED_COURSES:
        row = c.execute("SELECT id FROM courses WHERE id=?", (course["id"],)).fetchone()
        payload = {**course, "builds": json.dumps(course["builds"]), "learn": json.dumps(course["learn"]), "weeks": json.dumps(course["weeks"])}
        if row:
            c.execute("UPDATE courses SET title=:title, subtitle=:subtitle, duration_weeks=:duration_weeks, sessions=:sessions, coding=:coding, kit=:kit, eligibility=:eligibility, builds=:builds, learn=:learn, weeks=:weeks, outcome=:outcome WHERE id=:id", payload)
        else:
            c.execute("INSERT INTO courses(id,title,subtitle,duration_weeks,sessions,coding,kit,eligibility,builds,learn,weeks,outcome) VALUES(:id,:title,:subtitle,:duration_weeks,:sessions,:coding,:kit,:eligibility,:builds,:learn,:weeks,:outcome)", payload)
    # seed admin + demo learner (idempotent)
    import bcrypt
    admin_email = os.getenv("LTI_ADMIN_EMAIL", "admin@lti.local")
    if not c.execute("SELECT id FROM users WHERE email=?", (admin_email,)).fetchone():
        pw = bcrypt.hashpw(os.getenv("LTI_ADMIN_PASSWORD", "Admin@123").encode(), bcrypt.gensalt()).decode()
        c.execute("INSERT INTO users(name,email,phone,password_hash,role,grade,school) VALUES(?,?,?,?,?,?,?)",
                  ("LTI Admin", admin_email, "+918610621246", pw, "admin", "", "DMI College of Engineering"))
    if not c.execute("SELECT id FROM users WHERE email=?", ("demo@learner.local",)).fetchone():
        pw = bcrypt.hashpw(b"Demo@123", bcrypt.gensalt()).decode()
        c.execute("INSERT INTO users(name,email,phone,password_hash,role,grade,school) VALUES(?,?,?,?,?,?,?)",
                  ("Demo Learner", "demo@learner.local", "+910000000000", pw, "learner", "Grade 6", "Demo School"))
    c.commit(); c.close()
