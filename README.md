# LTI_Robotics

LTI Technology — Robotics Program website: **Robots Today. Innovators Tomorrow.**

Hands-on robotics program for Grades 4+. 3 levels, 40 sessions, 9+ real robots.
Electronics → Circuits & Logic → Arduino Coding.

## Structure

- `website/` — static marketing + admissions site (hosted on Netlify, publish dir = `website`)
  - `index.html`, `styles.css`, `app.js`, `config.js`
  - No build step. Open `website/index.html` directly or serve statically.
- `lms/` — LMS backend + frontend (FastAPI + static frontend, not hosted on Netlify)
- `LTI_Robotics_Full_Course_Marketing.docx`, `LTI_Robotics_Pamphlets (1).pdf` — marketing docs

## Website setup

1. Fill lead-routing keys in `website/config.js` (`ADMISSIONS_EMAIL`, `TELEGRAM_BOT_TOKEN`, `TELEGRAM_CHAT_ID`, `BACKEND_URL`). Site works without them (local save + mail draft fallback).
2. Deploy: Netlify publish directory = `website`, build command empty.

## Live

- GitHub: https://github.com/Kenneth-Aidan-B/LTI_Robotics
- Netlify: see project URL in Netlify dashboard (team `kenneth-aidan-b`)
