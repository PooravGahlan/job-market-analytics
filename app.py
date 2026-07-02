"""
╔══════════════════════════════════════════════════════════════╗
║              JOB MARKET AI  —  job.py  (Streamlit)           ║
║   Full web rewrite of the desktop app — deployable as a      ║
║   website with:  streamlit run job.py                        ║
║                                                                ║
║   Features:                                                   ║
║     • Login / Register (Seeker & Employer roles)              ║
║     • Job browsing, search & filters                          ║
║     • Apply with resume upload                                ║
║     • AI match scoring (skill/exp/location/salary)            ║
║     • Employer job CRUD + application review                  ║
║     • Analytics charts                                        ║
║     • Profile page                                            ║
║     • CSV import / export                                     ║
║     • Emerald & Gold premium theme, high-contrast buttons     ║
╚══════════════════════════════════════════════════════════════╝

Run locally:
    pip install -r requirements.txt
    streamlit run job.py

MySQL:
    Same schema as before. Configure via environment variables or
    Streamlit secrets (recommended for deployment) — see DB CONFIG
    section below. Falls back to localhost/root for local dev.
"""

import os
import re
import csv
import io
import uuid
from datetime import datetime

import streamlit as st

try:
    import mysql.connector
    from mysql.connector import IntegrityError
except ImportError:
    st.error("mysql-connector-python not installed. Run: pip install mysql-connector-python")
    st.stop()

import pandas as pd

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


# ════════════════════════════════════════════════════════════════
# DB CONFIG
# ════════════════════════════════════════════════════════════════
# For local dev these defaults work out of the box. For deployment
# (Streamlit Community Cloud, Render, etc.) set these in
# .streamlit/secrets.toml instead of hardcoding them, e.g.:
#
#   DB_HOST = "your-remote-mysql-host"
#   DB_PORT = 3306
#   DB_USER = "your_user"
#   DB_PASSWORD = "your_password"
#   DB_NAME = "job_market_db"
#
def _cfg(key, default):
    try:
        return st.secrets[key]
    except Exception:
        return os.environ.get(key, default)

DB_HOST     = _cfg("DB_HOST", "localhost")
DB_PORT     = int(_cfg("DB_PORT", 3306))
DB_USER     = _cfg("DB_USER", "root")
DB_PASSWORD = _cfg("DB_PASSWORD", "1178")
DB_NAME     = _cfg("DB_NAME", "job_market_db")

UPLOAD_DIR = "uploads/resumes"
os.makedirs(UPLOAD_DIR, exist_ok=True)


# ════════════════════════════════════════════════════════════════
# THEME — Emerald & Gold, dark charcoal base for maximum button contrast
# ════════════════════════════════════════════════════════════════
C_BG      = "#121613"
C_PANEL   = "#181D19"
C_CARD    = "#1D231F"
C_BORDER  = "#33413A"
C_ACCENT  = "#22C55E"   # parrot / emerald green — primary buttons
C_ACCENT2 = "#D4AF37"   # gold — secondary highlight
C_TEXT    = "#F3F3EE"
C_MUTED   = "#9BA79E"
C_SUCCESS = "#22C55E"
C_DANGER  = "#EF5350"
C_WARNING = "#D4AF37"

CHART_COLORS = ["#22C55E", "#D4AF37", "#4ADE80", "#B8860B", "#16A34A", "#F5D77E", "#0E9F6E", "#E8C766"]

st.set_page_config(page_title="Job Market AI", page_icon="💼", layout="wide")

_APP_CSS = f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
html, body, .stApp, [class*="css"] {{
    font-family:'Plus Jakarta Sans','Segoe UI',sans-serif !important;
}}
.stApp {{ background:radial-gradient(circle at 15% 0%, #17251C 0%, {C_BG} 45%); color:{C_TEXT}; }}
h1,h2,h3,h4,h5,h6, p, span, label, div {{ color:{C_TEXT}; }}
.block-container {{ padding-top:2rem; padding-bottom:3rem; max-width:1200px; }}

/* Sidebar */
[data-testid="stSidebar"] {{
    background:linear-gradient(180deg,#161C18 0%,#101512 100%);
    border-right:1px solid {C_BORDER};
}}
[data-testid="stSidebar"] .block-container {{ padding-top:1.5rem; }}

/* ── Buttons — big, bold, unmistakable emerald ── */
.stButton>button, .stFormSubmitButton>button, .stDownloadButton>button {{
    background:linear-gradient(135deg,#2FE07A 0%,{C_ACCENT} 100%) !important;
    color:#07130C !important;
    border:none !important;
    border-radius:12px !important;
    font-weight:800 !important;
    font-size:1.02rem !important;
    padding:0.85rem 1.6rem !important;
    min-height:3rem;
    width:100%;
    letter-spacing:0.2px;
    box-shadow:0 4px 14px rgba(34,197,94,0.30);
    transition:all .15s ease;
}}
.stButton>button:hover, .stFormSubmitButton>button:hover, .stDownloadButton>button:hover {{
    background:linear-gradient(135deg,#4CF090 0%,#2FE07A 100%) !important;
    box-shadow:0 6px 22px rgba(34,197,94,0.55);
    transform:translateY(-2px);
    color:#04100A !important;
}}
.stButton>button:active {{ transform:translateY(0); }}
.stButton>button p {{ font-size:1.02rem !important; font-weight:800 !important; }}

/* Sidebar nav buttons look like a menu, not a form button */
[data-testid="stSidebar"] .stButton>button {{
    background:transparent !important;
    color:{C_MUTED} !important;
    box-shadow:none !important;
    text-align:left !important;
    justify-content:flex-start !important;
    border-radius:10px !important;
    font-weight:600 !important;
    padding:0.7rem 1rem !important;
    min-height:2.6rem;
}}
[data-testid="stSidebar"] .stButton>button:hover {{
    background:#1B2E22 !important; color:{C_ACCENT} !important;
    box-shadow:none !important; transform:none;
}}
[data-testid="stSidebar"] .stButton>button p {{ text-align:left; font-size:0.95rem !important; }}

/* Forms & cards */
div[data-testid="stForm"] {{
    background:{C_CARD}; border:1px solid {C_BORDER}; border-radius:18px;
    padding:1.8rem 1.8rem; box-shadow:0 8px 30px rgba(0,0,0,0.35);
}}
.jm-card {{
    background:{C_CARD}; border:1px solid {C_BORDER}; border-radius:18px;
    padding:1.4rem 1.6rem; margin-bottom:1rem;
    box-shadow:0 6px 20px rgba(0,0,0,0.28);
    transition:border-color .15s ease, transform .15s ease;
}}
.jm-card:hover {{ border-color:{C_ACCENT}; transform:translateY(-1px); }}
.jm-card h3, .jm-card h4 {{ margin:0 0 .35rem 0; }}
.jm-tag {{
    display:inline-block; background:#17301F; color:{C_ACCENT};
    border:1px solid #2E5C3E; border-radius:20px; padding:4px 14px;
    font-size:12.5px; font-weight:700; margin-right:6px; margin-top:4px;
}}
.jm-gold {{ color:{C_ACCENT2}; font-weight:800; }}
.jm-muted {{ color:{C_MUTED}; font-size:13.5px; }}
.jm-badge-pending  {{ color:{C_WARNING}; font-weight:800; }}
.jm-badge-approved {{ color:{C_SUCCESS}; font-weight:800; }}
.jm-badge-rejected {{ color:{C_DANGER};  font-weight:800; }}

/* Inputs — bigger, clearer */
input, textarea, .stTextInput>div>div>input, .stTextArea textarea {{
    background:#141A16 !important; color:{C_TEXT} !important;
    border:1.5px solid {C_BORDER} !important; border-radius:10px !important;
    font-size:0.98rem !important; padding:0.6rem 0.8rem !important;
}}
input:focus, textarea:focus {{ border-color:{C_ACCENT} !important; box-shadow:0 0 0 3px rgba(34,197,94,0.18) !important; }}
.stSelectbox>div>div, .stMultiSelect>div>div {{
    background:#141A16 !important; border:1.5px solid {C_BORDER} !important; border-radius:10px !important;
}}
label p {{ font-weight:600 !important; color:{C_MUTED} !important; }}

/* Custom stat cards (replace default st.metric) */
.jm-stat {{
    background:linear-gradient(160deg,{C_CARD} 0%,#171D19 100%);
    border:1px solid {C_BORDER}; border-radius:18px; padding:1.3rem 1.4rem;
    box-shadow:0 6px 20px rgba(0,0,0,0.28);
}}
.jm-stat .icon {{ font-size:1.6rem; }}
.jm-stat .value {{ font-size:2rem; font-weight:800; color:{C_ACCENT}; margin:0.2rem 0; }}
.jm-stat .label {{ font-size:0.78rem; color:{C_MUTED}; font-weight:700; letter-spacing:0.6px; text-transform:uppercase; }}

/* Headline / hero */
.jm-hero-title {{
    font-size:3.2rem; font-weight:800; text-align:center;
    background:linear-gradient(135deg,#4CF090 0%,{C_ACCENT2} 100%);
    -webkit-background-clip:text; -webkit-text-fill-color:transparent;
    margin-bottom:0.2rem;
}}
.jm-hero-sub {{ text-align:center; color:{C_MUTED}; font-size:1.15rem; margin-bottom:2.2rem; }}

/* Dataframe */
[data-testid="stDataFrame"] {{ border:1px solid {C_BORDER}; border-radius:14px; overflow:hidden; }}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {{ gap:6px; }}
.stTabs [data-baseweb="tab"] {{
    background:{C_CARD}; border:1px solid {C_BORDER}; border-radius:10px 10px 0 0;
    padding:10px 20px; font-weight:600;
}}
.stTabs [aria-selected="true"] {{ color:{C_ACCENT} !important; border-color:{C_ACCENT} !important; }}

/* Expander */
[data-testid="stExpander"] {{
    background:{C_CARD}; border:1px solid {C_BORDER}; border-radius:14px;
}}

hr {{ border-color:{C_BORDER}; }}
</style>
"""

if hasattr(st, "html"):
    st.html(_APP_CSS)
else:
    st.markdown(_APP_CSS, unsafe_allow_html=True)


def stat_card(icon, value, label, col):
    col.markdown(
        f'<div class="jm-stat"><div class="icon">{icon}</div>'
        f'<div class="value">{value}</div><div class="label">{label}</div></div>',
        unsafe_allow_html=True)


# ════════════════════════════════════════════════════════════════
# DATABASE
# ════════════════════════════════════════════════════════════════
class DB:
    def __init__(self):
        self._cfg = dict(host=DB_HOST, port=DB_PORT, user=DB_USER,
                          password=DB_PASSWORD, database=DB_NAME)
        self._init()

    def _c(self):
        cfg = dict(self._cfg)
        cfg["ssl_disabled"] = False
        cfg["use_pure"] = True
        return mysql.connector.connect(**cfg)



    def _init(self):
        cn = self._c(); cur = cn.cursor()
        cur.execute("""CREATE TABLE IF NOT EXISTS users(
            id INT AUTO_INCREMENT PRIMARY KEY,
            name VARCHAR(255) NOT NULL,
            email VARCHAR(255) UNIQUE NOT NULL,
            password VARCHAR(255) NOT NULL,
            role VARCHAR(50) NOT NULL,
            skills TEXT NULL,
            experience VARCHAR(100) DEFAULT '',
            education VARCHAR(255) DEFAULT '',
            location VARCHAR(255) DEFAULT '',
            bio TEXT NULL,
            salary_exp DOUBLE DEFAULT 0)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS jobs(
            id INT AUTO_INCREMENT PRIMARY KEY,
            title VARCHAR(255) NOT NULL,
            company VARCHAR(255) NOT NULL,
            city VARCHAR(255) NOT NULL,
            salary DOUBLE NOT NULL,
            skill VARCHAR(255) NOT NULL,
            description TEXT NULL,
            job_type VARCHAR(50) DEFAULT 'Full-time',
            remote TINYINT(1) DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            posted_by INT DEFAULT NULL)""")
        cur.execute("""CREATE TABLE IF NOT EXISTS applications(
            id INT AUTO_INCREMENT PRIMARY KEY,
            job_id INT NOT NULL,
            applicant_name VARCHAR(255) NOT NULL,
            applicant_email VARCHAR(255) NOT NULL,
            phone VARCHAR(50) DEFAULT '',
            experience VARCHAR(100) DEFAULT '',
            education VARCHAR(255) DEFAULT '',
            resume_path VARCHAR(500) DEFAULT '',
            cover_letter TEXT NULL,
            applied_on TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status VARCHAR(50) DEFAULT 'Pending')""")
        cn.commit(); cur.close(); cn.close()
        self._migrate()
        if self._empty():
            self._seed()

    def _migrate(self):
        """Adds any columns missing from a pre-existing database so writes
        never fail silently with 'Unknown column' errors."""
        specs = {
            "users": [
                ("skills", "TEXT NULL"), ("experience", "VARCHAR(100) DEFAULT ''"),
                ("education", "VARCHAR(255) DEFAULT ''"), ("location", "VARCHAR(255) DEFAULT ''"),
                ("bio", "TEXT NULL"), ("salary_exp", "DOUBLE DEFAULT 0"),
            ],
            "jobs": [
                ("description", "TEXT NULL"), ("job_type", "VARCHAR(50) DEFAULT 'Full-time'"),
                ("remote", "TINYINT(1) DEFAULT 0"), ("posted_by", "INT DEFAULT NULL"),
            ],
            "applications": [
                ("phone", "VARCHAR(50) DEFAULT ''"), ("experience", "VARCHAR(100) DEFAULT ''"),
                ("education", "VARCHAR(255) DEFAULT ''"), ("resume_path", "VARCHAR(500) DEFAULT ''"),
                ("cover_letter", "TEXT NULL"), ("status", "VARCHAR(50) DEFAULT 'Pending'"),
            ],
        }
        cn = self._c(); cur = cn.cursor()
        for table, cols in specs.items():
            try:
                cur.execute(
                    "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s",
                    (DB_NAME, table))
                existing = {r[0] for r in cur.fetchall()}
            except Exception:
                continue
            for col, ddl in cols:
                if col not in existing:
                    try:
                        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")
                    except Exception:
                        pass
        cn.commit(); cur.close(); cn.close()

    def _empty(self):
        cn = self._c(); cur = cn.cursor()
        cur.execute("SELECT COUNT(*) FROM jobs")
        n = cur.fetchone()[0]; cur.close(); cn.close(); return n == 0

    def _seed(self):
        rows = [
            ("Data Scientist","Alpha AI","New York",125000,"Python","Build and deploy ML models for production.","Full-time",0),
            ("Software Engineer","Beta Tech","San Francisco",140000,"Java","Design scalable backend services.","Full-time",0),
            ("Cloud Architect","CloudCorp","Seattle",155000,"AWS","Architect multi-region cloud solutions.","Full-time",1),
            ("Frontend Developer","Designly","New York",95000,"React","Create pixel-perfect UI components.","Full-time",0),
            ("Data Analyst","FinMetrics","Chicago",85000,"Python","Analyse financial datasets and produce reports.","Full-time",0),
            ("DevOps Engineer","Beta Tech","San Francisco",130000,"Docker","Build CI/CD pipelines and infrastructure.","Full-time",1),
            ("Backend Developer","Alpha AI","Austin",115000,"Python","Develop REST APIs and microservices.","Full-time",0),
            ("Product Manager","SaaSify","Seattle",120000,"Agile","Own the product roadmap.","Full-time",0),
            ("Cybersecurity Specialist","SecureNet","Washington",135000,"Linux","Security audits and penetration testing.","Full-time",0),
            ("AI Research Engineer","DeepMindset","San Francisco",175000,"Python","Research and publish state-of-the-art models.","Full-time",1),
            ("Full Stack Developer","WebFlows","Austin",110000,"React","Own features end-to-end from DB to UI.","Full-time",0),
            ("Database Administrator","DataKeep","Chicago",98000,"SQL","Manage and optimise production databases.","Full-time",0),
            ("Mobile Engineer","AppStudio","Los Angeles",120000,"Swift","Build iOS applications for millions of users.","Full-time",0),
            ("BI Developer","FinMetrics","New York",102000,"SQL","Build dashboards and data pipelines.","Full-time",0),
            ("Systems Engineer","CloudCorp","Seattle",125000,"Linux","Maintain and evolve large-scale systems.","Full-time",0),
            ("Machine Learning Engineer","Alpha AI","San Francisco",160000,"Python","Train and deploy production ML models.","Full-time",1),
            ("Scrum Master","SaaSify","Boston",105000,"Agile","Facilitate agile ceremonies and remove blockers.","Full-time",0),
            ("UI/UX Developer","Designly","Los Angeles",90000,"React","Design and implement user-centred interfaces.","Full-time",1),
            ("Solutions Architect","CloudCorp","New York",150000,"AWS","Design enterprise cloud architectures.","Full-time",0),
            ("Security Consultant","SecureNet","Washington",128000,"Linux","Advise clients on security posture.","Full-time",0),
            ("QA Automation Engineer","WebFlows","Chicago",92000,"Java","Write automated test suites for web apps.","Full-time",0),
            ("Data Engineer","FinMetrics","Austin",130000,"Python","Build and maintain data pipelines.","Full-time",1),
            ("Network Administrator","DataKeep","Boston",88000,"Linux","Manage network infrastructure.","Full-time",0),
            ("Cloud Security Engineer","SecureNet","San Francisco",145000,"AWS","Secure cloud workloads.","Full-time",0),
            ("Applications Developer","Beta Tech","Los Angeles",112000,"Java","Develop enterprise Java applications.","Full-time",0),
        ]
        cn = self._c(); cur = cn.cursor()
        cur.executemany(
            "INSERT INTO jobs(title,company,city,salary,skill,description,job_type,remote) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
            rows)
        cn.commit(); cur.close(); cn.close()

    # ── auth ─────────────────────────────────────────────────────
    def register(self, name, email, pwd, role):
        try:
            cn = self._c(); cur = cn.cursor()
            cur.execute("INSERT INTO users(name,email,password,role) VALUES(%s,%s,%s,%s)", (name, email, pwd, role))
            cn.commit(); cur.close(); cn.close(); return True
        except IntegrityError:
            return False

    def login(self, email, pwd):
        cn = self._c(); cur = cn.cursor()
        cur.execute("SELECT id,name,email,role FROM users WHERE email=%s AND password=%s", (email, pwd))
        r = cur.fetchone(); cur.close(); cn.close(); return r

    def get_user(self, uid):
        cn = self._c(); cur = cn.cursor()
        cur.execute("SELECT id,name,email,role,skills,experience,education,location,bio,salary_exp FROM users WHERE id=%s", (uid,))
        r = cur.fetchone(); cur.close(); cn.close(); return r

    def update_profile(self, uid, name, skills, exp, edu, loc, bio, sal):
        cn = self._c(); cur = cn.cursor()
        cur.execute("""UPDATE users SET name=%s, skills=%s, experience=%s,
                   education=%s, location=%s, bio=%s, salary_exp=%s WHERE id=%s""",
                    (name, skills, exp, edu, loc, bio, float(sal), uid))
        cn.commit(); cur.close(); cn.close(); return True

    def change_password(self, uid, new_pwd):
        cn = self._c(); cur = cn.cursor()
        cur.execute("UPDATE users SET password=%s WHERE id=%s", (new_pwd, uid))
        cn.commit(); cur.close(); cn.close()

    # ── jobs ─────────────────────────────────────────────────────
    def all_jobs(self):
        cn = self._c(); cur = cn.cursor()
        cur.execute("SELECT id,title,company,city,salary,skill,description,job_type,remote FROM jobs ORDER BY created_at DESC")
        r = cur.fetchall(); cur.close(); cn.close(); return r

    def add_job(self, title, company, city, salary, skill, desc="", jtype="Full-time", remote=0, posted_by=None):
        cn = self._c(); cur = cn.cursor()
        cur.execute("INSERT INTO jobs(title,company,city,salary,skill,description,job_type,remote,posted_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (title, company, city, float(salary), skill, desc, jtype, remote, posted_by))
        cn.commit(); cur.close(); cn.close()

    def update_job(self, jid, title, company, city, salary, skill, desc="", jtype="Full-time", remote=0):
        cn = self._c(); cur = cn.cursor()
        cur.execute("UPDATE jobs SET title=%s,company=%s,city=%s,salary=%s,skill=%s,description=%s,job_type=%s,remote=%s WHERE id=%s",
                    (title, company, city, float(salary), skill, desc, jtype, remote, jid))
        cn.commit(); cur.close(); cn.close()

    def delete_job(self, jid):
        cn = self._c(); cur = cn.cursor()
        cur.execute("DELETE FROM jobs WHERE id=%s", (jid,))
        cn.commit(); cur.close(); cn.close()

    def jobs_by_employer(self, uid):
        cn = self._c(); cur = cn.cursor()
        cur.execute("SELECT id,title,company,city,salary,skill,description,job_type,remote FROM jobs WHERE posted_by=%s ORDER BY created_at DESC", (uid,))
        r = cur.fetchall(); cur.close(); cn.close(); return r

    # ── applications ─────────────────────────────────────────────
    def apply(self, job_id, name, email, phone, exp, edu, resume, cover=""):
        cn = self._c(); cur = cn.cursor()
        cur.execute("INSERT INTO applications(job_id,applicant_name,applicant_email,phone,experience,education,resume_path,cover_letter) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                    (job_id, name, email, phone, exp, edu, resume, cover))
        cn.commit(); cur.close(); cn.close()

    def get_applications(self, search="", status="All"):
        cn = self._c(); cur = cn.cursor()
        q = ("SELECT a.id,j.title,j.company,a.applicant_name,a.applicant_email,"
             "a.resume_path,a.applied_on,a.status FROM applications a JOIN jobs j ON a.job_id=j.id WHERE 1=1")
        p = []
        if search:
            q += " AND (a.applicant_name LIKE %s OR a.applicant_email LIKE %s OR j.title LIKE %s)"
            p += [f"%{search}%", f"%{search}%", f"%{search}%"]
        if status != "All":
            q += " AND a.status=%s"; p.append(status)
        q += " ORDER BY a.applied_on DESC"
        cur.execute(q, p); r = cur.fetchall(); cur.close(); cn.close(); return r

    def my_applications(self, email):
        cn = self._c(); cur = cn.cursor()
        cur.execute("""SELECT j.title, j.company, a.applied_on, a.status, a.id
                   FROM applications a JOIN jobs j ON a.job_id=j.id
                   WHERE a.applicant_email=%s ORDER BY a.applied_on DESC""", (email,))
        r = cur.fetchall(); cur.close(); cn.close(); return r

    def approve_app(self, aid):
        cn = self._c(); cur = cn.cursor()
        cur.execute("UPDATE applications SET status='Approved' WHERE id=%s", (aid,))
        cn.commit(); cur.close(); cn.close()

    def reject_app(self, aid):
        cn = self._c(); cur = cn.cursor()
        cur.execute("UPDATE applications SET status='Rejected' WHERE id=%s", (aid,))
        cn.commit(); cur.close(); cn.close()

    def app_stats(self):
        cn = self._c(); cur = cn.cursor()
        d = {}
        for k, q in [("total", ""), ("approved", "WHERE status='Approved'"),
                     ("rejected", "WHERE status='Rejected'"), ("pending", "WHERE status='Pending'")]:
            cur.execute(f"SELECT COUNT(*) FROM applications {q}"); d[k] = cur.fetchone()[0]
        cur.close(); cn.close(); return d

    # ── analytics ────────────────────────────────────────────────
    def analytics(self):
        cn = self._c(); cur = cn.cursor()
        cur.execute("SELECT COUNT(*),AVG(salary),MAX(salary) FROM jobs")
        t, a, m = cur.fetchone()
        cur.execute("SELECT skill FROM jobs GROUP BY skill ORDER BY COUNT(*) DESC LIMIT 1")
        ts = cur.fetchone()
        cur.execute("SELECT city FROM jobs GROUP BY city ORDER BY COUNT(*) DESC LIMIT 1")
        tc = cur.fetchone()
        cur.close(); cn.close()
        return {"total_jobs": t or 0, "avg_salary": a or 0, "max_salary": m or 0,
                "top_skill": ts[0] if ts else "N/A", "top_city": tc[0] if tc else "N/A"}

    def chart_skills(self):
        cn = self._c(); cur = cn.cursor()
        cur.execute("SELECT skill,COUNT(*) FROM jobs GROUP BY skill ORDER BY COUNT(*) DESC")
        r = cur.fetchall(); cur.close(); cn.close(); return r

    def chart_cities(self):
        cn = self._c(); cur = cn.cursor()
        cur.execute("SELECT city,COUNT(*) FROM jobs GROUP BY city ORDER BY COUNT(*) DESC")
        r = cur.fetchall(); cur.close(); cn.close(); return r

    def chart_salary(self):
        cn = self._c(); cur = cn.cursor()
        cur.execute("SELECT skill,AVG(salary) FROM jobs GROUP BY skill ORDER BY AVG(salary) DESC")
        r = cur.fetchall(); cur.close(); cn.close(); return r

    def chart_companies(self):
        cn = self._c(); cur = cn.cursor()
        cur.execute("SELECT company,COUNT(*) cnt FROM jobs GROUP BY company ORDER BY cnt DESC LIMIT 6")
        r = cur.fetchall(); cur.close(); cn.close(); return r

    # ── csv ──────────────────────────────────────────────────────
    def export_csv_bytes(self):
        rows = self.all_jobs()
        buf = io.StringIO()
        w = csv.writer(buf)
        w.writerow(["ID", "Title", "Company", "City", "Salary", "Skill", "Description", "JobType", "Remote"])
        w.writerows(rows)
        return buf.getvalue().encode("utf-8")

    def import_csv_bytes(self, data: bytes):
        cn = self._c(); cur = cn.cursor(); count = 0
        text = data.decode("utf-8", errors="ignore")
        for row in csv.reader(io.StringIO(text)):
            if len(row) >= 5:
                try:
                    t, c, ci = (row[1], row[2], row[3]) if len(row) >= 6 else (row[0], row[1], row[2])
                    sal = float((row[4] if len(row) >= 6 else row[3]).strip() or 0)
                    sk = (row[5] if len(row) >= 6 else row[4]).strip()
                    cur.execute("INSERT INTO jobs(title,company,city,salary,skill) VALUES(%s,%s,%s,%s,%s)",
                                (t.strip(), c.strip(), ci.strip(), sal, sk))
                    count += 1
                except Exception:
                    pass
        cn.commit(); cur.close(); cn.close(); return count


@st.cache_resource
def get_db():
    return DB()


# ════════════════════════════════════════════════════════════════
# AI MATCH SCORE
# ════════════════════════════════════════════════════════════════
def _parse_yrs(text):
    m = re.search(r"(\d+)", str(text)); return int(m.group(1)) if m else 0

def _parse_yrs_desc(desc):
    m = re.search(r"(\d+)\+?\s*year", desc.lower()); return int(m.group(1)) if m else 0

def match_score(job, profile):
    score = 0.0
    j_skill = (job[5] or "").lower()
    j_city = (job[3] or "").lower()
    j_sal = float(job[4] or 0)
    j_desc = (job[6] or "").lower()
    j_remote = job[8] if len(job) > 8 else 0

    u_skills = [s.strip().lower() for s in (profile.get("skills") or "").split(",") if s.strip()]
    u_loc = (profile.get("location") or "").lower()
    u_sal = float(profile.get("salary_exp") or 0)
    u_exp = _parse_yrs(profile.get("experience") or "")

    if u_skills:
        sk = 0
        for us in u_skills:
            if us in j_skill or j_skill in us: sk = 100; break
            for w in j_skill.split():
                if w and w in us: sk = max(sk, 55)
        score += sk * 0.40
    else:
        score += 20

    req = _parse_yrs_desc(j_desc)
    if req == 0: score += 25
    elif u_exp >= req: score += 25
    elif u_exp > 0: score += max(0, 25 * (u_exp / req))

    if not u_loc or j_remote: score += 20
    elif u_loc in j_city or j_city in u_loc: score += 20
    else: score += 5

    if u_sal == 0: score += 10
    elif j_sal >= u_sal: score += 15
    elif j_sal >= u_sal * 0.8: score += 8
    else: score += 2

    return min(int(score), 99)


# ════════════════════════════════════════════════════════════════
# SESSION STATE
# ════════════════════════════════════════════════════════════════
db = get_db()

if "user" not in st.session_state: st.session_state.user = None            # (id,name,email,role)
if "screen" not in st.session_state: st.session_state.screen = "start"     # start/login/register
if "role_hint" not in st.session_state: st.session_state.role_hint = "Seeker"
if "job_detail_id" not in st.session_state: st.session_state.job_detail_id = None
if "apply_job_id" not in st.session_state: st.session_state.apply_job_id = None


def logout():
    st.session_state.user = None
    st.session_state.screen = "start"


# ════════════════════════════════════════════════════════════════
# UI HELPERS
# ════════════════════════════════════════════════════════════════
def job_card(job, show_apply, key_prefix, match=None):
    jid, title, company, city, salary, skill, desc, jtype, remote = (
        job[0], job[1], job[2], job[3], job[4], job[5],
        job[6] if len(job) > 6 else "", job[7] if len(job) > 7 else "", job[8] if len(job) > 8 else 0)
    with st.container():
        badges = ""
        if match is not None:
            colr = "jm-badge-approved" if match >= 80 else "jm-badge-pending" if match >= 60 else "jm-muted"
            badges += f'&nbsp;&nbsp;<span class="{colr}">🤖 {match}% match</span>'
        if remote:
            badges += '&nbsp;&nbsp;<span class="jm-badge-approved">🌐 Remote</span>'
        tags = "".join(f'<span class="jm-tag">{t.strip()}</span>' for t in (skill or "").split(",") if t.strip())

        st.markdown(
            f'<div class="jm-card">'
            f'<h3 style="margin:0;">{title}{badges}</h3>'
            f'<div class="jm-muted" style="margin-top:0.35rem;">🏢 {company} &nbsp;&nbsp; 📍 {city} &nbsp;&nbsp; '
            f'<span class="jm-gold">💰 ${int(salary):,}/yr</span> &nbsp;&nbsp; {jtype}</div>'
            f'<div style="margin-top:0.6rem;">{tags}</div>'
            f'</div>',
            unsafe_allow_html=True)

        if desc:
            with st.expander("About the role"):
                st.write(desc)
        if show_apply:
            c1, _ = st.columns([1, 3])
            if c1.button("Apply Now →", key=f"{key_prefix}_apply_{jid}"):
                st.session_state.apply_job_id = jid
                st.rerun()
        st.write("")


def apply_form(job):
    st.markdown(f"#### Apply — {job[1]}")
    st.caption(f"{job[2]} · {job[3]}")
    u = st.session_state.user
    with st.form(f"apply_form_{job[0]}"):
        name = st.text_input("Full Name *", value=u[1] if u else "")
        email = st.text_input("Email *", value=u[2] if u else "")
        phone = st.text_input("Phone")
        exp = st.text_input("Experience (e.g. '3 years')")
        edu = st.text_input("Education")
        cover = st.text_area("Cover Letter (optional)", height=100)
        resume = st.file_uploader("Resume (PDF) *", type=["pdf"])
        submitted = st.form_submit_button("Submit Application")
        if submitted:
            if not name or not email:
                st.error("Name and Email are required."); return
            if not resume:
                st.error("Please attach your resume (PDF)."); return
            try:
                fname = f"{uuid.uuid4().hex}_{resume.name}"
                fpath = os.path.join(UPLOAD_DIR, fname)
                with open(fpath, "wb") as f:
                    f.write(resume.getbuffer())
                db.apply(job[0], name, email, phone, exp, edu, fpath, cover)
            except Exception as e:
                st.error(f"Could not submit application:\n{e}")
                return
            st.success("Application submitted successfully!")
            st.session_state.apply_job_id = None
            st.rerun()
    if st.button("Cancel", key=f"cancel_apply_{job[0]}"):
        st.session_state.apply_job_id = None
        st.rerun()


def chart(chart_type):
    if not HAS_MPL:
        st.info("matplotlib not installed."); return
    fig, ax = plt.subplots(figsize=(6, 3.6), dpi=110)
    fig.patch.set_facecolor(C_CARD); ax.set_facecolor(C_CARD)
    for s in ["top", "right", "left", "bottom"]: ax.spines[s].set_visible(False)
    ax.tick_params(colors=C_MUTED, labelsize=8)

    if chart_type == "skills":
        data = db.chart_skills()
        if data:
            labs, vals = zip(*data)
            ax.pie(vals, labels=labs, autopct='%1.0f%%', colors=CHART_COLORS[:len(labs)],
                   startangle=140, textprops=dict(fontsize=8, color=C_TEXT))
            ax.set_title("Skills Demand", fontsize=11, weight="bold", color=C_TEXT, pad=8)
    elif chart_type == "city":
        data = db.chart_cities()
        if data:
            cities, counts = zip(*data)
            bars = ax.bar(cities, counts, color=C_ACCENT, width=0.55)
            ax.set_title("Jobs by City", fontsize=11, weight="bold", color=C_TEXT, pad=8)
            for b in bars:
                ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.1, str(int(b.get_height())),
                        ha="center", fontsize=8, color=C_TEXT)
            ax.tick_params(axis="x", labelrotation=30); ax.yaxis.set_visible(False)
    elif chart_type == "salary":
        data = db.chart_salary()
        if data:
            skills, avgs = zip(*data); avgs = [a / 1000 for a in avgs]
            bars = ax.bar(skills, avgs, color=C_ACCENT2, width=0.55)
            ax.set_title("Avg Salary by Skill ($K)", fontsize=11, weight="bold", color=C_TEXT, pad=8)
            for b in bars:
                ax.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.5, f"${b.get_height():.0f}k",
                        ha="center", fontsize=8, color=C_TEXT)
            ax.tick_params(axis="x", labelrotation=30); ax.yaxis.set_visible(False)
    elif chart_type == "company":
        data = db.chart_companies()
        if data:
            cos, counts = zip(*data)
            ax.barh(range(len(cos)), counts, color=C_ACCENT, height=0.55)
            ax.set_yticks(range(len(cos))); ax.set_yticklabels(cos, fontsize=8, color=C_TEXT)
            ax.set_title("Top Companies", fontsize=11, weight="bold", color=C_TEXT, pad=8)
            ax.xaxis.set_visible(False); ax.invert_yaxis()

    fig.tight_layout(pad=1.0)
    st.pyplot(fig, use_container_width=True)
    plt.close(fig)


# ════════════════════════════════════════════════════════════════
# AUTH SCREENS
# ════════════════════════════════════════════════════════════════
def start_screen():
    st.write("")
    st.markdown('<div class="jm-hero-title">Job Market AI</div>', unsafe_allow_html=True)
    st.markdown('<div class="jm-hero-sub">Find the right role, or the right hire, powered by AI matching.</div>', unsafe_allow_html=True)
    st.write("")
    c1, c2 = st.columns(2, gap="large")
    with c1:
        st.markdown(
            '<div class="jm-card" style="text-align:center;padding:2.2rem 1.6rem;">'
            '<div style="font-size:2.6rem;">💼</div>'
            '<h2 style="margin:0.4rem 0 0.2rem 0;">Employer</h2>'
            f'<p class="jm-muted">Post jobs, review applicants, and manage your listings.</p>'
            '</div>', unsafe_allow_html=True)
        a, b = st.columns(2)
        if a.button("Login", key="emp_login", use_container_width=True):
            st.session_state.role_hint = "Employer"; st.session_state.screen = "login"; st.rerun()
        if b.button("Register", key="emp_register", use_container_width=True):
            st.session_state.screen = "register"; st.rerun()
    with c2:
        st.markdown(
            '<div class="jm-card" style="text-align:center;padding:2.2rem 1.6rem;">'
            '<div style="font-size:2.6rem;">🔍</div>'
            '<h2 style="margin:0.4rem 0 0.2rem 0;">Job Seeker</h2>'
            f'<p class="jm-muted">Discover roles matched to your skills and apply in minutes.</p>'
            '</div>', unsafe_allow_html=True)
        a, b = st.columns(2)
        if a.button("Login", key="seek_login", use_container_width=True):
            st.session_state.role_hint = "Seeker"; st.session_state.screen = "login"; st.rerun()
        if b.button("Register", key="seek_register", use_container_width=True):
            st.session_state.screen = "register"; st.rerun()


def login_screen():
    _, mid, _ = st.columns([1, 1.3, 1])
    with mid:
        st.markdown(
            f'<div style="text-align:center;margin-bottom:1.2rem;">'
            f'<div style="font-size:2.4rem;">⬡</div>'
            f'<h1 style="color:{C_ACCENT};margin:0;">Job Market AI</h1>'
            f'<p class="jm-muted">Logging in as <span class="jm-gold">{st.session_state.role_hint}</span></p>'
            f'</div>', unsafe_allow_html=True)
        with st.form("login_form"):
            email = st.text_input("Email address")
            pwd = st.text_input("Password", type="password")
            ok = st.form_submit_button("Sign In", use_container_width=True)
            if ok:
                if not email or not pwd:
                    st.error("Please fill in all fields.")
                else:
                    try:
                        u = db.login(email, pwd)
                    except Exception as e:
                        st.error(f"Could not sign in:\n{e}"); u = None
                    if not u:
                        st.error("Invalid email or password.")
                    else:
                        st.session_state.user = u
                        st.session_state.screen = "app"
                        st.rerun()
        st.write("")
        c1, c2 = st.columns(2)
        if c1.button("Register instead", key="go_register", use_container_width=True):
            st.session_state.screen = "register"; st.rerun()
        if c2.button("← Back", key="login_back", use_container_width=True):
            st.session_state.screen = "start"; st.rerun()


def register_screen():
    _, mid, _ = st.columns([1, 1.3, 1])
    with mid:
        st.markdown(
            f'<div style="text-align:center;margin-bottom:1.2rem;">'
            f'<h1 style="margin:0;">Create Account</h1>'
            f'<p class="jm-muted">Join Job Market AI</p></div>', unsafe_allow_html=True)
        with st.form("register_form"):
            name = st.text_input("Full Name")
            email = st.text_input("Email Address")
            pwd = st.text_input("Password", type="password")
            role = st.radio("I am a:", ["Job Seeker", "Employer"], horizontal=True)
            ok = st.form_submit_button("Create Account", use_container_width=True)
            if ok:
                if not all([name, email, pwd]):
                    st.error("All fields are required.")
                else:
                    r = "Employer" if role == "Employer" else "Seeker"
                    try:
                        success = db.register(name, email, pwd, r)
                    except Exception as e:
                        st.error(f"Could not register:\n{e}"); success = False
                    if not success:
                        st.error("Email already registered.")
                    else:
                        st.success(f"Welcome, {name}! You can now log in.")
                        st.session_state.screen = "login"
                        st.rerun()
        st.write("")
        c1, c2 = st.columns(2)
        if c1.button("Sign in instead", key="go_login", use_container_width=True):
            st.session_state.screen = "login"; st.rerun()
        if c2.button("← Back", key="register_back", use_container_width=True):
            st.session_state.screen = "start"; st.rerun()


# ════════════════════════════════════════════════════════════════
# APP PAGES
# ════════════════════════════════════════════════════════════════
def page_dashboard():
    u = st.session_state.user
    st.markdown(f"## Welcome back, {u[1]} 👋")
    st.caption("Here's what's happening in your job market.")
    a = db.analytics()
    stats = db.app_stats()
    c1, c2, c3, c4 = st.columns(4)
    stat_card("💼", f"{a['total_jobs']:,}", "Total Jobs", c1)
    stat_card("💰", f"${a['avg_salary']:,.0f}", "Avg Salary", c2)
    stat_card("📄", stats["total"], "Applications", c3)
    stat_card("📍", a["top_city"], "Top City", c4)
    st.markdown(
        f'<div class="jm-card">🛠 Top Skill: <span class="jm-gold">{a["top_skill"]}</span>'
        f'&nbsp;&nbsp;&nbsp;🏆 Peak Salary: <span class="jm-gold">${a["max_salary"]:,.0f}</span>'
        f'&nbsp;&nbsp;&nbsp;⏳ Pending Apps: <span class="jm-gold">{stats["pending"]}</span></div>',
        unsafe_allow_html=True)
    st.markdown("### Recent Job Postings")
    for j in db.all_jobs()[:6]:
        job_card(j, show_apply=(u[3] == "Seeker"), key_prefix="dash")


def page_jobs():
    u = st.session_state.user
    st.markdown("## Browse Jobs")
    c1, c2, c3, c4 = st.columns([2, 1, 1, 0.6])
    kw = c1.text_input("🔍 Search jobs, companies…", key="jobs_kw")
    city = c2.text_input("📍 City", key="jobs_city")
    skill = c3.text_input("🛠 Skill", key="jobs_skill")
    if c4.button("Reset"):
        st.session_state.jobs_kw = ""; st.session_state.jobs_city = ""; st.session_state.jobs_skill = ""
        st.rerun()

    jobs = db.all_jobs()
    kw_l, city_l, skill_l = kw.strip().lower(), city.strip().lower(), skill.strip().lower()
    filtered = [j for j in jobs if
                (not kw_l or kw_l in j[1].lower() or kw_l in j[2].lower()) and
                (not city_l or city_l in j[3].lower()) and
                (not skill_l or skill_l in j[5].lower())]
    st.caption(f"{len(filtered)} job{'s' if len(filtered) != 1 else ''} found")
    for j in filtered:
        job_card(j, show_apply=(u[3] == "Seeker"), key_prefix="jobs")


def page_applications():
    u = st.session_state.user
    if u[3] == "Employer":
        st.markdown("## Application Management")
        c1, c2 = st.columns([2, 1])
        search = c1.text_input("🔍 Search applicants…", key="app_search")
        status = c2.selectbox("Status", ["All", "Pending", "Approved", "Rejected"], key="app_status")
        try:
            stats = db.app_stats()
            rows = db.get_applications(search, status)
        except Exception as e:
            st.error(f"Could not load applications:\n{e}"); return
        c1, c2, c3, c4 = st.columns(4)
        stat_card("📋", stats["total"], "Total", c1)
        stat_card("✅", stats["approved"], "Approved", c2)
        stat_card("❌", stats["rejected"], "Rejected", c3)
        stat_card("⏳", stats["pending"], "Pending", c4)

        if not rows:
            st.info("No applications found."); return
        df = pd.DataFrame(rows, columns=["ID", "Job Title", "Company", "Applicant", "Email", "Resume", "Applied On", "Status"])
        st.dataframe(df.drop(columns=["Resume"]), use_container_width=True, hide_index=True)

        st.markdown("#### Manage an application")
        labels = [f"#{r[0]} — {r[3]} → {r[1]} ({r[7]})" for r in rows]
        pick = st.selectbox("Select application", labels, key="app_pick")
        sel = rows[labels.index(pick)]
        c1, c2, c3 = st.columns(3)
        if c1.button("✓ Approve", key="approve_btn"):
            try:
                db.approve_app(sel[0]); st.success("Approved."); st.rerun()
            except Exception as e:
                st.error(f"Could not approve:\n{e}")
        if c2.button("✗ Reject", key="reject_btn"):
            try:
                db.reject_app(sel[0]); st.warning("Rejected."); st.rerun()
            except Exception as e:
                st.error(f"Could not reject:\n{e}")
        resume_path = sel[5]
        if resume_path and os.path.exists(resume_path):
            with open(resume_path, "rb") as f:
                c3.download_button("📄 Download Resume", f, file_name=os.path.basename(resume_path), key="dl_resume")
        else:
            c3.caption("No resume on file.")
    else:
        st.markdown("## My Applications")
        try:
            apps = db.my_applications(u[2])
        except Exception as e:
            st.error(f"Could not load your applications:\n{e}"); return
        if not apps:
            st.info("No applications yet. Start applying!"); return
        badge = {"Approved": "jm-badge-approved", "Rejected": "jm-badge-rejected", "Pending": "jm-badge-pending"}
        for title, company, applied, status, aid in apps:
            st.markdown(
                f'<div class="jm-card"><b>{title}</b><br>'
                f'<span class="jm-muted">{company} · Applied {str(applied)[:10]}</span><br>'
                f'<span class="{badge.get(status,"jm-muted")}">{status}</span></div>',
                unsafe_allow_html=True)


def page_analytics():
    st.markdown("## Analytics Dashboard")
    a = db.analytics()
    c1, c2, c3, c4 = st.columns(4)
    stat_card("📊", f"{a['total_jobs']:,}", "Total Jobs", c1)
    stat_card("💰", f"${a['avg_salary']:,.0f}", "Avg Salary", c2)
    stat_card("🏆", f"${a['max_salary']:,.0f}", "Peak Salary", c3)
    stat_card("🛠", a["top_skill"], "Top Skill", c4)
    tabs = st.tabs(["Skills", "Cities", "Salaries", "Companies"])
    with tabs[0]: chart("skills")
    with tabs[1]: chart("city")
    with tabs[2]: chart("salary")
    with tabs[3]: chart("company")


def page_ai_match():
    u = st.session_state.user
    st.markdown("## 🤖 AI Job Match")
    st.caption("Jobs ranked by how well they match your profile.")
    full = db.get_user(u[0])
    profile = {}
    if full and len(full) >= 10:
        profile = {"skills": full[4] or "", "experience": full[5] or "", "location": full[7] or "", "salary_exp": full[9] or 0}
    if not profile.get("skills", "").strip():
        st.warning("Complete your Profile to get personalised matches →")
    jobs = db.all_jobs()
    scored = sorted([(j, match_score(j, profile)) for j in jobs], key=lambda x: x[1], reverse=True)
    for j, sc in scored[:15]:
        job_card(j, show_apply=True, key_prefix="match", match=sc)


def page_profile():
    u = st.session_state.user
    st.markdown("## My Profile")
    st.markdown(
        f'<div class="jm-card" style="text-align:center;"><h3>👤 {u[1]}</h3>'
        f'<span class="jm-muted">{u[2]}</span><br>'
        f'<span class="jm-gold">{"Employer" if u[3]=="Employer" else "Job Seeker"}</span></div>',
        unsafe_allow_html=True)
    try:
        full = db.get_user(u[0])
    except Exception as e:
        st.error(f"Could not load profile:\n{e}"); return
    if not full: return
    with st.form("profile_form"):
        st.markdown("#### Edit Profile")
        name = st.text_input("Display Name", value=full[1] or "")
        skills = st.text_input("Skills (comma-separated)", value=full[4] or "", placeholder="Python, SQL, React…")
        exp = st.text_input("Years of Experience", value=full[5] or "", placeholder="e.g. 3 years")
        edu = st.text_input("Education", value=full[6] or "", placeholder="e.g. B.Sc Computer Science")
        loc = st.text_input("Location / City", value=full[7] or "")
        sal = st.text_input("Expected Salary ($)", value=str(int(full[9])) if full[9] else "")
        bio = st.text_area("Bio", value=full[8] or "", height=90)
        ok = st.form_submit_button("Save Profile")
        if ok:
            try:
                sal_val = float(sal.strip() or 0)
            except ValueError:
                sal_val = 0
            try:
                db.update_profile(u[0], name.strip() or u[1], skills.strip(), exp.strip(), edu.strip(), loc.strip(), bio.strip(), sal_val)
            except Exception as e:
                st.error(f"Could not save profile:\n{e}"); return
            st.success("Profile updated successfully.")
            row = db.get_user(u[0])
            if row:
                st.session_state.user = (row[0], row[1], row[2], row[3])
            st.rerun()


def page_settings():
    u = st.session_state.user
    st.markdown("## Settings")
    st.markdown("#### Change Password")
    with st.form("pwd_form"):
        old = st.text_input("Current password", type="password")
        new = st.text_input("New password", type="password")
        new2 = st.text_input("Confirm new password", type="password")
        ok = st.form_submit_button("Update Password")
        if ok:
            if not all([old, new, new2]):
                st.error("Fill all password fields.")
            elif new != new2:
                st.error("New passwords do not match.")
            else:
                try:
                    check = db.login(u[2], old)
                    if not check:
                        st.error("Current password is incorrect.")
                    else:
                        db.change_password(u[0], new)
                        st.success("Password updated.")
                except Exception as e:
                    st.error(f"Could not update password:\n{e}")

    st.markdown("#### Data Import / Export")
    c1, c2 = st.columns(2)
    try:
        csv_bytes = db.export_csv_bytes()
        c1.download_button("📤 Export Jobs CSV", csv_bytes, file_name="jobs_export.csv", mime="text/csv")
    except Exception as e:
        c1.error(f"Export failed:\n{e}")
    up = c2.file_uploader("📥 Import Jobs CSV", type=["csv"], key="settings_import")
    if up is not None and c2.button("Run Import"):
        try:
            n = db.import_csv_bytes(up.getvalue())
            st.success(f"{n} records imported.")
        except Exception as e:
            st.error(f"Import failed:\n{e}")


def page_employer_jobs():
    u = st.session_state.user
    st.markdown("## My Job Listings")

    with st.expander("+ Post New Job"):
        with st.form("post_job_form"):
            title = st.text_input("Job Title *")
            company = st.text_input("Company *")
            city = st.text_input("City *")
            salary = st.text_input("Annual Salary ($) *")
            skill = st.text_input("Required Skill *")
            desc = st.text_area("Description", height=90)
            jtype = st.selectbox("Job Type", ["Full-time", "Part-time", "Contract", "Internship"])
            remote = st.checkbox("Remote / Hybrid")
            ok = st.form_submit_button("Save Job")
            if ok:
                if not all([title, company, city, salary, skill]):
                    st.error("Fill all required fields.")
                else:
                    try:
                        sal_val = float(salary)
                    except ValueError:
                        st.error("Salary must be a number."); sal_val = None
                    if sal_val is not None:
                        try:
                            db.add_job(title, company, city, sal_val, skill, desc, jtype, 1 if remote else 0, u[0])
                        except Exception as e:
                            st.error(f"Could not post job:\n{e}")
                        else:
                            st.success("Job posted."); st.rerun()

    try:
        rows = db.all_jobs()
    except Exception as e:
        st.error(f"Could not load jobs:\n{e}"); return

    if not rows:
        st.info("No jobs yet."); return

    df = pd.DataFrame([(r[0], r[1], r[2], r[3], f"${int(r[4]):,}", r[5]) for r in rows],
                       columns=["ID", "Title", "Company", "City", "Salary", "Skill"])
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.markdown("#### Edit / Delete a Job")
    labels = [f"#{r[0]} — {r[1]} @ {r[2]}" for r in rows]
    pick = st.selectbox("Select job", labels, key="job_pick")
    sel = rows[labels.index(pick)]

    with st.form("edit_job_form"):
        title = st.text_input("Job Title *", value=sel[1])
        company = st.text_input("Company *", value=sel[2])
        city = st.text_input("City *", value=sel[3])
        salary = st.text_input("Annual Salary ($) *", value=str(int(sel[4])))
        skill = st.text_input("Required Skill *", value=sel[5])
        desc = st.text_area("Description", value=sel[6] or "", height=90)
        jtype_opts = ["Full-time", "Part-time", "Contract", "Internship"]
        jtype = st.selectbox("Job Type", jtype_opts, index=jtype_opts.index(sel[7]) if sel[7] in jtype_opts else 0)
        remote = st.checkbox("Remote / Hybrid", value=bool(sel[8]))
        c1, c2 = st.columns(2)
        save = c1.form_submit_button("💾 Save Changes")
        delete = c2.form_submit_button("🗑 Delete Job")
        if save:
            try:
                db.update_job(sel[0], title, company, city, float(salary), skill, desc, jtype, 1 if remote else 0)
                st.success("Job updated."); st.rerun()
            except Exception as e:
                st.error(f"Could not update job:\n{e}")
        if delete:
            try:
                db.delete_job(sel[0])
                st.success("Job deleted."); st.rerun()
            except Exception as e:
                st.error(f"Could not delete job:\n{e}")

    st.markdown("#### CSV Tools")
    c1, c2 = st.columns(2)
    try:
        csv_bytes = db.export_csv_bytes()
        c1.download_button("📤 Export CSV", csv_bytes, file_name="jobs.csv", mime="text/csv", key="emp_export")
    except Exception as e:
        c1.error(f"Export failed:\n{e}")
    up = c2.file_uploader("📥 Import CSV", type=["csv"], key="emp_import")
    if up is not None and c2.button("Run Import", key="emp_run_import"):
        try:
            n = db.import_csv_bytes(up.getvalue())
            st.success(f"{n} records imported."); st.rerun()
        except Exception as e:
            st.error(f"Import failed:\n{e}")


# ════════════════════════════════════════════════════════════════
# APP SHELL
# ════════════════════════════════════════════════════════════════
NAV_ITEMS = [
    ("Dashboard", "🏠"), ("Jobs", "💼"), ("Applications", "📄"),
    ("Analytics", "📊"), ("AI Match", "🤖"), ("Profile", "👤"), ("Settings", "⚙️"),
]


def app_shell():
    u = st.session_state.user
    is_emp = (u[3] == "Employer")

    if "nav_choice" not in st.session_state:
        st.session_state.nav_choice = "Dashboard"

    with st.sidebar:
        st.markdown(
            f'<div style="text-align:center;padding:0.4rem 0 1rem 0;">'
            f'<div style="font-size:2rem;">⬡</div>'
            f'<div style="font-size:1.15rem;font-weight:800;color:{C_ACCENT};letter-spacing:0.4px;">Job Market AI</div>'
            f'</div>', unsafe_allow_html=True)
        st.markdown(
            f'<div class="jm-card" style="text-align:center;padding:0.8rem;margin-bottom:1.2rem;">'
            f'<div style="font-size:1.6rem;">👤</div>'
            f'<b>{u[1]}</b><br><span class="jm-gold">{"Employer" if is_emp else "Job Seeker"}</span>'
            f'</div>', unsafe_allow_html=True)

        pages = ["Dashboard", "Jobs", "Applications", "Analytics"]
        if not is_emp:
            pages.append("AI Match")
        pages += ["Profile", "Settings"]

        for name, icon in NAV_ITEMS:
            if name not in pages:
                continue
            active = st.session_state.nav_choice == name
            label = f"**{icon}  {name}**" if active else f"{icon}  {name}"
            if st.button(label, key=f"nav_{name}", use_container_width=True):
                st.session_state.nav_choice = name
                st.rerun()

        st.markdown("<div style='margin:1.4rem 0 0.6rem 0;border-top:1px solid " + C_BORDER + ";'></div>", unsafe_allow_html=True)
        if st.button("🚪  Logout", key="nav_logout", use_container_width=True):
            logout(); st.rerun()

    choice = st.session_state.nav_choice

    if st.session_state.apply_job_id is not None:
        jobs = {j[0]: j for j in db.all_jobs()}
        job = jobs.get(st.session_state.apply_job_id)
        if job:
            apply_form(job)
            return
        else:
            st.session_state.apply_job_id = None

    if choice == "Dashboard":
        page_dashboard()
    elif choice == "Jobs":
        page_employer_jobs() if is_emp else page_jobs()
    elif choice == "Applications":
        page_applications()
    elif choice == "Analytics":
        page_analytics()
    elif choice == "AI Match":
        page_ai_match()
    elif choice == "Profile":
        page_profile()
    elif choice == "Settings":
        page_settings()


# ════════════════════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════════════════════
def main():
    if st.session_state.user is not None:
        app_shell()
        return
    if st.session_state.screen == "login":
        login_screen()
    elif st.session_state.screen == "register":
        register_screen()
    else:
        start_screen()


if __name__ == "__main__":
    main()