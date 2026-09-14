# LTI_Robotics

LTI Technology — Robotics Program: **Robots Today. Innovators Tomorrow.**
Single combined portal — marketing site + LMS login + learner dashboard + admin
command center in one frontend (`lms/frontend`), served by the FastAPI backend
(`lms/backend`, which mounts the frontend at `/`).

Hands-on robotics program for Grades 4+. 3 levels, 40 sessions, 9+ real robots.
Electronics → Circuits & Logic → Arduino Coding.

## Structure

- `lms/frontend/` — combined single portal (hosted on Netlify, publish dir = `lms/frontend`)
  - `index.html` — marketing site with LMS Login link
  - `auth.html` — learner & admin login / register
  - `dashboard.html` — learner dashboard (courses, enrollments, progress, certificates)
  - `admin.html` — admin command center (leads, enrollments, users, announcements)
  - `lms.js`, `app.js`, `config.js`, `styles.css`
  - No build step. API calls use relative `/api/*` (same-origin via backend).
- `lms/backend/` — FastAPI + SQLite (`main.py`, `auth.py`, `db.py`, `requirements.txt`)
  - Run: `uvicorn main:app --port 8902` from `lms/backend` (see `lms/.env.example`)
- `LTI_Robotics_Full_Course_Marketing.docx`, `LTI_Robotics_Pamphlets (1).pdf` — marketing docs

## Setup

1. Backend: copy `lms/.env.example` to `.env`, set `LTI_JWT_SECRET` + admin creds, run uvicorn.
2. Frontend lead routing: fill keys in `lms/frontend/config.js` if posting leads externally.
3. Deploy: Netlify publish directory = `lms/frontend`, build command empty.

## Live

- GitHub: https://github.com/Kenneth-Aidan-B/LTI_Robotics
- Netlify: https://lti-robotics-lms.netlify.app (team `kenneth-aidan-b`)
