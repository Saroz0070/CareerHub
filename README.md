# CareerHub

A complete **student–organization career and vacancy matching platform**, built with Flask, SQLAlchemy and Jinja2, with a premium, modern SaaS-style UI (no frontend framework — plain HTML/CSS/JS).

Three roles:

- **Student / Job Seeker** — register, build a profile, upload a resume, browse & search vacancies, see a skill-match score, apply, and track application status.
- **Organization / Employer** — register (reviewed by an admin before posting), post/edit/delete vacancies, review applicants with match scores and resumes, accept/reject applications.
- **Administrator** — verifies or rejects organizations so only trustworthy employers can post vacancies.

---

## 1. Tech Stack

| Layer      | Technology |
|------------|------------|
| Backend    | Python + Flask |
| ORM        | Flask-SQLAlchemy |
| Database   | SQLite by default (zero config) — MySQL supported via `DATABASE_URL` |
| Templates  | Jinja2 |
| Frontend   | HTML5 + CSS3 + vanilla JS (no build step, no framework) |
| Auth       | Flask sessions + Werkzeug password hashing |
| Email      | Optional Gmail SMTP (app works fully without it) |

No React, Vue, PHP, Django, Bootstrap or Tailwind — the whole UI is a hand-built design system in `static/css/style.css`.

---

## 2. Features

- Separate registration / login for students, organizations and admin, with duplicate-email validation and clear success/error messaging.
- Secure password hashing (Werkzeug) — passwords are never stored or displayed in plain text.
- Split-screen auth pages with password visibility toggles and smooth entrance animation.
- Student profile with **resume upload** (PDF/DOC/DOCX), profile completion meter, and skill/interest chips.
- **Vacancy feed** with search (title/skills/description), location filter, and type filter, plus a "Recommended" tab.
- **Smart matching** — `Skills (70%) + Experience (30%)` score shown on every vacancy card and application.
- Expired vacancies are clearly marked and can no longer be applied to (past applications remain visible).
- Apply flow with **duplicate-application prevention** (application-level check + database unique constraint).
- **My Applications** page with live status: `Pending / Shortlisted / Accepted / Rejected`.
- Organization **verification workflow** — new organizations start `Pending`; an admin can `Verify` / `Reject` with an optional note. Only verified organizations can post vacancies.
- Organizations can only manage **their own** vacancies and applicants (ownership enforced server-side).
- Admin dashboard with real, database-derived platform statistics (no fabricated numbers anywhere in the UI).
- Custom, on-brand 403 / 404 / 500 error pages.
- Fully responsive from 320px mobile up through large desktop, with a collapsible sidebar app-shell for dashboards and an animated mobile navigation drawer.
- `prefers-reduced-motion` respected throughout.

---

## 3. Directory Structure

```
CareerHub/
├── app.py                        # application factory + all routes
├── config.py                     # configuration (env-var driven)
├── requirements.txt
├── README.md
├── models/
│   ├── __init__.py               # db instance
│   ├── student.py
│   ├── organization.py
│   ├── opportunity.py
│   └── application.py
├── templates/
│   ├── base.html                 # global layout: navbar, flashes, footer
│   ├── app_base.html             # dashboard shell: sidebar + main content
│   ├── _icons.html               # shared inline SVG icon macro
│   ├── home.html                 # landing page
│   ├── login.html / register.html
│   ├── organization_login.html / organization_register.html
│   ├── admin_login.html
│   ├── dashboard.html / profile.html / manage_profile.html
│   ├── opportunities.html / opportunity_detail.html / applications.html
│   ├── organization_dashboard.html / organization_profile.html
│   ├── post_opportunity.html / manage_opportunities.html / applicants.html
│   ├── admin_dashboard.html / admin_organizations.html
│   └── errors/
│       ├── 403.html / 404.html / 500.html
├── static/
│   ├── css/style.css             # complete design system
│   └── js/main.js                # nav, password toggle, flashes, reveal animations
└── uploads/                      # uploaded resumes / verification docs (auto-created)
```

---

## 4. Installation & Setup

### 4.1 Prerequisites
Python 3.9+.

### 4.2 Virtual environment

**Linux / macOS:**
```bash
cd CareerHub
python3 -m venv venv
source venv/bin/activate
```

**Windows (PowerShell):**
```powershell
cd CareerHub
python -m venv venv
venv\Scripts\activate
```

### 4.3 Install requirements
```bash
pip install -r requirements.txt
```

### 4.4 Database setup
By default the app uses a local SQLite file (`careerhub.db`), created automatically on first run — nothing to configure.

**To use MySQL instead**, create a database and set `DATABASE_URL` before running:
```bash
export DATABASE_URL="mysql+pymysql://username:password@localhost:3306/careerhub"
```
`PyMySQL` is already listed in `requirements.txt`. Tables are created automatically via `db.create_all()` on startup either way.

To start fresh with SQLite at any time:
```bash
rm -f careerhub.db
```

### 4.5 Run the application
```bash
python app.py
```
Then open **http://127.0.0.1:5000**

---

## 5. Using the Application

### 5.1 Admin login
Go to the footer link **Admin Portal** (or `/admin/login`) and sign in with:
```
Email:    admin@careerhub.com
Password: admin123
```
> Change these via the `ADMIN_EMAIL` / `ADMIN_PASSWORD` environment variables before any real deployment.

### 5.2 Student flow
Register → complete your profile (skills, education, experience, resume) → browse or search vacancies → apply → track status in **My Applications**.

### 5.3 Organization flow
Register with an optional verification document → wait for admin approval (status starts `Pending`) → once `Verified`, post vacancies, manage them, and review/accept/reject applicants from **Applicants**.

### 5.4 Admin verification
Log in as admin → **Organizations** → open a pending organization → **Verify** or **Reject** (with an optional note). Only verified organizations can post vacancies.

---

## 6. Configuration

All configuration lives in `config.py` and can be overridden with environment variables.

```bash
export SECRET_KEY="change-me-in-production"
export DATABASE_URL="mysql+pymysql://user:pass@localhost:3306/careerhub"   # or leave unset for SQLite
export ADMIN_EMAIL="your-admin-email"
export ADMIN_PASSWORD="your-strong-password"
# Optional Gmail SMTP — applications submit fine without this

```

Email is only sent if `MAIL_USERNAME` and `MAIL_PASSWORD` are both set; a failed send never blocks an application.

---

## 7. Security Notes

- Passwords hashed with Werkzeug (`generate_password_hash` / `check_password_hash`).
- Session-based auth with per-role decorators (`login_required_student`, `login_required_org`, `login_required_admin`).
- Ownership checks everywhere: a student can only edit their own profile and applications; an organization can only edit/delete its own vacancies and view applicants who applied to them.
- Resume downloads are protected — a student can always download their own resume; an organization can only download a resume for a student who applied to one of its vacancies.
- File uploads are restricted to PDF/DOC/DOCX, filenames sanitized (`secure_filename`), and a max upload size is enforced.
- Duplicate applications are blocked at both the application layer and the database (unique constraint on `student_id + opportunity_id`).
- Custom error handlers for 403/404/500 avoid leaking stack traces to end users.

---

## 8. Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Run `pip install -r requirements.txt` inside the activated virtual environment. |
| Port 5000 already in use | Edit `app.run(port=...)` at the bottom of `app.py`. |
| Can't upload a resume | Ensure the `uploads/` folder exists (created automatically) and is writable. |
| Fonts/icons look plain | The design pulls Inter/Sora from Google Fonts over the network — everything still works offline, just with system font fallbacks. |
| MySQL connection errors | Double check `DATABASE_URL` and that the database itself already exists (Flask creates tables, not the database). |

---

© CareerHub. Built with Flask, Flask-SQLAlchemy and a hand-built design system.
