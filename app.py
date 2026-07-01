"""
╔══════════════════════════════════════════════════════════════╗
║              JOB MARKET AI  —  job_market_ai.py             ║
║   Full PySide6 rewrite of job_market_dashboard.py           ║
║   All original features preserved + major upgrades:         ║
║     • Notion-style collapsible sidebar                       ║
║     • Modern card-based job browser                          ║
║     • AI match scoring (skill/exp/location/salary)           ║
║     • Animated stat cards                                    ║
║     • Matplotlib charts embedded in Qt                       ║
║     • Employer job CRUD + application management             ║
║     • Profile page                                           ║
║     • CSV import / export                                    ║
║     • Premium Ivory & Emerald theme via QSS                  ║
╚══════════════════════════════════════════════════════════════╝

Requirements:
    pip install PySide6 mysql-connector-python matplotlib

MySQL: same credentials as original (host=localhost, user=root,
       password=1178, database=job_market_db)
       Change DB_PASSWORD below if yours differs.
"""

# ── stdlib ──────────────────────────────────────────────────────
import csv
import os
import re
import sys

# ── third-party ─────────────────────────────────────────────────
try:
    import mysql.connector
    from mysql.connector import IntegrityError  # type: ignore[import]
except ImportError:
    sys.exit("mysql-connector-python not found.  pip install mysql-connector-python")

try:
    from PySide6.QtWidgets import (
        QApplication, QMainWindow, QWidget, QFrame, QDialog,
        QVBoxLayout, QHBoxLayout, QGridLayout, QFormLayout,
        QLabel, QPushButton, QLineEdit, QTextEdit, QComboBox,
        QScrollArea, QFileDialog, QMessageBox, QCheckBox,
        QStackedWidget, QSizePolicy, QSplitter, QTableWidget,
        QTableWidgetItem, QHeaderView, QAbstractItemView,
        QRadioButton, QButtonGroup, QSlider, QTabWidget,
        QGraphicsDropShadowEffect, QGraphicsOpacityEffect,
        QProgressBar, QSpacerItem
    )
    from PySide6.QtCore import (
        Qt, Signal, QPropertyAnimation, QEasingCurve,
        QTimer, QSize, QPoint, QRect
    )
    from PySide6.QtGui import (
        QFont, QColor, QPalette, QIcon, QPixmap,
        QPainter, QPen, QBrush, QLinearGradient, QFontMetrics,
        QCursor
    )
except ImportError:
    sys.exit("PySide6 not found.  pip install PySide6")

try:
    import matplotlib
    matplotlib.use("QtAgg")
    import matplotlib.pyplot as plt
    from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
    HAS_MPL = True
except ImportError:
    HAS_MPL = False

# ════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════
DB_HOST     = "localhost"
DB_PORT     = 3306
DB_USER     = "root"
DB_PASSWORD = "1178"
DB_NAME     = "job_market_db"

# ════════════════════════════════════════════════════════════════
# THEME — colours referenced throughout
# ════════════════════════════════════════════════════════════════
# Premium "Ivory & Emerald" theme — light, upscale, no dark/navy/yellow base
C_BG        = "#FAF7F1"   # warm ivory background
C_PANEL     = "#FFFFFF"
C_SIDEBAR   = "#F4EFE4"   # soft champagne sidebar
C_CARD      = "#FFFFFF"
C_CARD2     = "#F6F2E9"
C_BORDER    = "#E6DCC6"   # soft gold-beige border
C_ACCENT    = "#0E6F4F"   # deep emerald — primary button colour, pops against ivory
C_ACCENT2   = "#B4884A"   # warm bronze/gold accent
C_GLOW      = "#C9A24B"   # muted gold highlight
C_TEXT      = "#20261F"   # deep charcoal-green text
C_MUTED     = "#8A8272"
C_SUCCESS   = "#1E8F5C"
C_DANGER    = "#B84C3E"
C_WARNING   = "#C08A2E"

CHART_COLORS = ["#0E6F4F","#B4884A","#1E8F5C","#C08A2E","#3E7C5C","#8A6D3B","#5FA37D","#C9A24B"]

# ════════════════════════════════════════════════════════════════
# GLOBAL QSS
# ════════════════════════════════════════════════════════════════
GLOBAL_QSS = f"""
/* ── base ── */
QMainWindow, QDialog {{ background:{C_BG}; }}
QWidget {{ background:transparent; color:{C_TEXT};
          font-family:'Inter','Segoe UI',system-ui,-apple-system,sans-serif; font-size:13px; }}


/* ── scrollbars ── */
QScrollBar:vertical   {{ background:{C_PANEL}; width:6px; border-radius:3px; margin:0; }}
QScrollBar::handle:vertical {{ background:{C_BORDER}; border-radius:3px; min-height:30px; }}
QScrollBar::handle:vertical:hover {{ background:{C_ACCENT}; }}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{ height:0; }}
QScrollBar:horizontal {{ background:{C_PANEL}; height:6px; border-radius:3px; }}
QScrollBar::handle:horizontal {{ background:{C_BORDER}; border-radius:3px; min-width:30px; }}
QScrollBar::handle:horizontal:hover {{ background:{C_ACCENT}; }}
QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {{ width:0; }}

/* ── inputs ── */
QLineEdit, QTextEdit, QPlainTextEdit {{
    background:{C_CARD2}; border:1px solid {C_BORDER};
    border-radius:8px; padding:9px 14px; color:{C_TEXT}; font-size:13px; }}
QLineEdit:focus, QTextEdit:focus {{ border-color:{C_ACCENT}; background:#FFFFFF; }}
QLineEdit::placeholder, QTextEdit::placeholder {{ color:#A79E8C; }}

QComboBox {{
    background:{C_CARD2}; border:1px solid {C_BORDER}; border-radius:8px;
    padding:8px 14px; color:{C_TEXT}; }}
QComboBox:focus {{ border-color:{C_ACCENT}; }}
QComboBox::drop-down {{ border:none; width:0; }}
QComboBox QAbstractItemView {{
    background:{C_CARD2}; border:1px solid {C_BORDER};
    color:{C_TEXT}; selection-background-color:{C_ACCENT}; selection-color:white; border-radius:6px; padding:4px; }}

/* ── buttons ── */
QPushButton {{
    background:{C_ACCENT}; color:white; border:none; border-radius:8px;
    padding:9px 20px; font-weight:600; font-size:13px; }}
QPushButton:hover   {{ background:#12855F; }}
QPushButton:pressed {{ background:#0A5A3F; }}
QPushButton:disabled{{ background:{C_BORDER}; color:#A79E8C; }}

QPushButton#secondary {{
    background:{C_CARD2}; border:1px solid {C_BORDER}; color:{C_MUTED}; }}
QPushButton#secondary:hover {{ border-color:{C_ACCENT}; color:{C_ACCENT}; background:#EFF6F1; }}

QPushButton#danger {{ background:{C_DANGER}; }}
QPushButton#danger:hover {{ background:#9E3C30; }}

QPushButton#success {{ background:{C_SUCCESS}; color:white; font-weight:700; }}
QPushButton#success:hover {{ background:#177247; }}

QPushButton#ghost {{
    background:transparent; border:none; color:{C_ACCENT2}; padding:6px 10px; font-weight:700; }}
QPushButton#ghost:hover {{ color:{C_ACCENT}; background:{C_CARD2}; border-radius:6px; }}

/* ── tables ── */
QTableWidget {{
    background:{C_CARD}; alternate-background-color:{C_CARD2};
    gridline-color:{C_BORDER}; border:none; selection-background-color:#DDEEE3;
    selection-color:{C_TEXT}; }}
QTableWidget::item {{ padding:8px 12px; border:none; }}
QHeaderView::section {{
    background:{C_SIDEBAR}; color:{C_MUTED}; padding:10px 12px;
    border:none; border-bottom:1px solid {C_BORDER};
    font-weight:600; font-size:11px; letter-spacing:0.5px; }}

/* ── tabs ── */
QTabWidget::pane {{ background:{C_CARD}; border:1px solid {C_BORDER}; border-radius:0 8px 8px 8px; }}
QTabBar::tab {{
    background:{C_PANEL}; color:{C_MUTED}; padding:9px 20px;
    border:1px solid {C_BORDER}; border-bottom:none; border-radius:8px 8px 0 0; margin-right:2px; }}
QTabBar::tab:selected {{ background:{C_CARD}; color:{C_ACCENT}; border-top-color:{C_ACCENT}; }}
QTabBar::tab:hover {{ color:{C_TEXT}; }}

/* ── progress bar ── */
QProgressBar {{
    background:{C_CARD2}; border-radius:4px; text-align:center; color:transparent; max-height:6px; }}
QProgressBar::chunk {{
    background:qlineargradient(x1:0,y1:0,x2:1,y2:0,stop:0 {C_ACCENT},stop:1 {C_ACCENT2});
    border-radius:4px; }}

/* ── checkbox / radio ── */
QCheckBox, QRadioButton {{ spacing:8px; color:{C_TEXT}; }}
QCheckBox::indicator, QRadioButton::indicator {{
    width:16px; height:16px; border:2px solid {C_BORDER}; border-radius:4px; background:{C_CARD2}; }}
QRadioButton::indicator {{ border-radius:8px; }}
QCheckBox::indicator:checked, QRadioButton::indicator:checked {{
    background:{C_ACCENT}; border-color:{C_ACCENT}; }}

/* ── slider ── */
QSlider::groove:horizontal {{ background:{C_BORDER}; height:4px; border-radius:2px; }}
QSlider::handle:horizontal {{
    background:{C_ACCENT}; width:16px; height:16px; border-radius:8px; margin:-6px 0; }}
QSlider::sub-page:horizontal {{ background:{C_ACCENT}; border-radius:2px; }}

/* ── named panels ── */
QWidget#sidebar {{ background:{C_SIDEBAR}; border-right:1px solid {C_BORDER}; }}
QWidget#page    {{ background:{C_BG}; }}
QFrame#card {{
    background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 {C_CARD}, stop:1 #FCFAF5);
    border:1px solid {C_BORDER}; border-radius:14px; padding:4px; }}
QFrame#card:hover {{
    border-color:{C_ACCENT};
    background:qlineargradient(x1:0,y1:0,x2:0,y2:1, stop:0 {C_CARD2}, stop:1 {C_CARD});
}}
QLabel#h1 {{ font-size:22px; font-weight:700; color:{C_TEXT}; }}
QLabel#h2 {{ font-size:16px; font-weight:600; color:{C_TEXT}; }}
QLabel#muted {{ color:{C_MUTED}; font-size:12px; }}
QLabel#accent {{ color:{C_ACCENT}; font-weight:700; }}
QLabel#brand  {{ font-size:16px; font-weight:800; color:{C_ACCENT}; letter-spacing:1px; }}
QLabel#tag {{
    background:#EFF6F1; color:{C_ACCENT}; border:1px solid #CFE6D8;
    border-radius:10px; padding:2px 9px; font-size:11px; font-weight:600; }}
QLabel#statusPending  {{ color:{C_WARNING}; font-weight:700; }}
QLabel#statusApproved {{ color:{C_SUCCESS}; font-weight:700; }}
QLabel#statusRejected {{ color:{C_DANGER};  font-weight:700; }}

QMessageBox {{ background:{C_CARD}; color:{C_TEXT}; }}
QDialog      {{ background:{C_BG}; }}
"""

# ════════════════════════════════════════════════════════════════
# DATABASE
# ════════════════════════════════════════════════════════════════
class DB:
    def __init__(self):
        self._cfg = dict(host=DB_HOST, port=DB_PORT,
                         user=DB_USER, password=DB_PASSWORD,
                         database=DB_NAME)
        self._init()

    def _c(self):
        return mysql.connector.connect(**self._cfg)

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
        # NOTE: CREATE TABLE IF NOT EXISTS does nothing if the table already
        # exists from an older version of the schema — that silently leaves
        # newer columns (skills, bio, salary_exp, phone, resume_path, ...)
        # missing, which is what was breaking "Save Profile" and "Apply Now"
        # (the INSERT/UPDATE would raise "Unknown column" and the app looked
        # like it did nothing). _migrate() patches any existing table so it
        # has every column this version expects.
        self._migrate()
        if self._empty(): self._seed()

    def _migrate(self):
        """Add any columns that are missing on an existing (older) database
        so writes never silently fail because of 'Unknown column' errors."""
        specs = {
            "users": [
                ("skills", "TEXT NULL"),
                ("experience", "VARCHAR(100) DEFAULT ''"),
                ("education", "VARCHAR(255) DEFAULT ''"),
                ("location", "VARCHAR(255) DEFAULT ''"),
                ("bio", "TEXT NULL"),
                ("salary_exp", "DOUBLE DEFAULT 0"),
            ],
            "jobs": [
                ("description", "TEXT NULL"),
                ("job_type", "VARCHAR(50) DEFAULT 'Full-time'"),
                ("remote", "TINYINT(1) DEFAULT 0"),
                ("posted_by", "INT DEFAULT NULL"),
            ],
            "applications": [
                ("phone", "VARCHAR(50) DEFAULT ''"),
                ("experience", "VARCHAR(100) DEFAULT ''"),
                ("education", "VARCHAR(255) DEFAULT ''"),
                ("resume_path", "VARCHAR(500) DEFAULT ''"),
                ("cover_letter", "TEXT NULL"),
                ("status", "VARCHAR(50) DEFAULT 'Pending'"),
            ],
        }
        cn = self._c(); cur = cn.cursor()
        for table, cols in specs.items():
            try:
                cur.execute(
                    "SELECT COLUMN_NAME FROM INFORMATION_SCHEMA.COLUMNS "
                    "WHERE TABLE_SCHEMA=%s AND TABLE_NAME=%s",
                    (DB_NAME, table))
                existing = {r[0] for r in cur.fetchall()}
            except Exception as e:
                print(f"[migrate] could not inspect {table}: {e}")
                continue
            for col, ddl in cols:
                if col not in existing:
                    try:
                        cur.execute(f"ALTER TABLE {table} ADD COLUMN {col} {ddl}")
                        print(f"[migrate] added {table}.{col}")
                    except Exception as e:
                        print(f"[migrate] could not add {table}.{col}: {e}")
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

    # ── auth ──────────────────────────────────────────────────────
    def register(self, name, email, pwd, role):
        try:
            cn = self._c(); cur = cn.cursor()
            cur.execute("INSERT INTO users(name,email,password,role) VALUES(%s,%s,%s,%s)",
                        (name,email,pwd,role))
            cn.commit(); cur.close(); cn.close(); return True
        except IntegrityError: return False

    def login(self, email, pwd):
        cn = self._c(); cur = cn.cursor()
        cur.execute("SELECT id,name,email,role FROM users WHERE email=%s AND password=%s",(email,pwd))
        r = cur.fetchone(); cur.close(); cn.close(); return r

    def get_user(self, uid):
        cn = self._c(); cur = cn.cursor()
        cur.execute("SELECT id,name,email,role,skills,experience,education,location,bio,salary_exp FROM users WHERE id=%s",(uid,))
        r = cur.fetchone(); cur.close(); cn.close(); return r

    def update_profile(self, uid, name, skills, exp, edu, loc, bio, sal):
        cn = self._c(); cur = cn.cursor()
        cur.execute("""UPDATE users SET name=%s, skills=%s, experience=%s, 
                   education=%s, location=%s, bio=%s, salary_exp=%s 
                   WHERE id=%s""",
                (name, skills, exp, edu, loc, bio, float(sal), uid))
        cn.commit(); cur.close(); cn.close()
        return True


    # ── jobs ──────────────────────────────────────────────────────
    def all_jobs(self):
        cn = self._c(); cur = cn.cursor()
        cur.execute("SELECT id,title,company,city,salary,skill,description,job_type,remote FROM jobs ORDER BY created_at DESC")
        r = cur.fetchall(); cur.close(); cn.close(); return r

    def search_jobs(self, keyword="", city="", skill="", company="", min_sal=0, max_sal=9999999):
        cn = self._c(); cur = cn.cursor()
        q = ("SELECT id,title,company,city,salary,skill,description,job_type,remote "
             "FROM jobs WHERE salary BETWEEN %s AND %s")
        p = [min_sal, max_sal]
        if keyword:
            q += " AND (title LIKE %s OR company LIKE %s)"; p += [f"%{keyword}%",f"%{keyword}%"]
        if city:
            q += " AND city LIKE %s"; p.append(f"%{city}%")
        if skill:
            q += " AND skill LIKE %s"; p.append(f"%{skill}%")
        if company:
            q += " AND company LIKE %s"; p.append(f"%{company}%")
        q += " ORDER BY created_at DESC"
        cur.execute(q,p); r = cur.fetchall(); cur.close(); cn.close(); return r

    def add_job(self, title, company, city, salary, skill, desc="", jtype="Full-time", remote=0, posted_by=None):
        cn = self._c(); cur = cn.cursor()
        cur.execute("INSERT INTO jobs(title,company,city,salary,skill,description,job_type,remote,posted_by) VALUES(%s,%s,%s,%s,%s,%s,%s,%s,%s)",
                    (title,company,city,float(salary),skill,desc,jtype,remote,posted_by))
        cn.commit(); cur.close(); cn.close()

    def update_job(self, jid, title, company, city, salary, skill, desc="", jtype="Full-time", remote=0):
        cn = self._c(); cur = cn.cursor()
        cur.execute("UPDATE jobs SET title=%s,company=%s,city=%s,salary=%s,skill=%s,description=%s,job_type=%s,remote=%s WHERE id=%s",
                    (title,company,city,float(salary),skill,desc,jtype,remote,jid))
        cn.commit(); cur.close(); cn.close()

    def delete_job(self, jid):
        cn = self._c(); cur = cn.cursor()
        cur.execute("DELETE FROM jobs WHERE id=%s",(jid,)); cn.commit(); cur.close(); cn.close()

    def jobs_by_employer(self, uid):
        cn = self._c(); cur = cn.cursor()
        cur.execute("SELECT id,title,company,city,salary,skill,description,job_type,remote FROM jobs WHERE posted_by=%s ORDER BY created_at DESC",(uid,))
        r = cur.fetchall(); cur.close(); cn.close(); return r

    # ── applications ──────────────────────────────────────────────
    def apply(self, job_id, name, email, phone, exp, edu, resume, cover=""):
        cn = self._c(); cur = cn.cursor()
        cur.execute("INSERT INTO applications(job_id,applicant_name,applicant_email,phone,experience,education,resume_path,cover_letter) VALUES(%s,%s,%s,%s,%s,%s,%s,%s)",
                    (job_id,name,email,phone,exp,edu,resume,cover))
        cn.commit(); cur.close(); cn.close()

    def get_applications(self, search="", status="All"):
        cn = self._c(); cur = cn.cursor()
        q = ("SELECT a.id,j.title,j.company,a.applicant_name,a.applicant_email,"
             "a.resume_path,a.applied_on,a.status "
             "FROM applications a JOIN jobs j ON a.job_id=j.id WHERE 1=1")
        p = []
        if search:
            q += " AND (a.applicant_name LIKE %s OR a.applicant_email LIKE %s OR j.title LIKE %s)"
            p += [f"%{search}%",f"%{search}%",f"%{search}%"]
        if status != "All":
            q += " AND a.status=%s"; p.append(status)
        q += " ORDER BY a.applied_on DESC"
        cur.execute(q,p); r = cur.fetchall(); cur.close(); cn.close(); return r

    def my_applications(self, email):
        cn = self._c(); cur = cn.cursor()
        cur.execute("""SELECT j.title, j.company, a.applied_on, a.status, a.id 
                   FROM applications a 
                   JOIN jobs j ON a.job_id=j.id 
                   WHERE a.applicant_email=%s 
                   ORDER BY a.applied_on DESC""", (email,))
        r = cur.fetchall(); cur.close(); cn.close(); return r


    def approve_app(self, aid):
        cn = self._c(); cur = cn.cursor()
        cur.execute("UPDATE applications SET status='Approved' WHERE id=%s",(aid,))
        cn.commit(); cur.close(); cn.close()

    def reject_app(self, aid):
        cn = self._c(); cur = cn.cursor()
        cur.execute("UPDATE applications SET status='Rejected' WHERE id=%s",(aid,))
        cn.commit(); cur.close(); cn.close()

    def app_stats(self):
        cn = self._c(); cur = cn.cursor()
        d = {}
        for k,q in [("total",""),("approved","WHERE status='Approved'"),
                    ("rejected","WHERE status='Rejected'"),("pending","WHERE status='Pending'")]:
            cur.execute(f"SELECT COUNT(*) FROM applications {q}"); d[k]=cur.fetchone()[0]
        cur.close(); cn.close(); return d

    # ── analytics ─────────────────────────────────────────────────
    def analytics(self):
        cn = self._c(); cur = cn.cursor()
        cur.execute("SELECT COUNT(*),AVG(salary),MAX(salary) FROM jobs")
        t,a,m = cur.fetchone()
        cur.execute("SELECT skill FROM jobs GROUP BY skill ORDER BY COUNT(*) DESC LIMIT 1")
        ts = cur.fetchone()
        cur.execute("SELECT city FROM jobs GROUP BY city ORDER BY COUNT(*) DESC LIMIT 1")
        tc = cur.fetchone()
        cur.close(); cn.close()
        return {"total_jobs":t or 0,"avg_salary":a or 0,"max_salary":m or 0,
                "top_skill":ts[0] if ts else "N/A","top_city":tc[0] if tc else "N/A"}

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

    # ── csv ───────────────────────────────────────────────────────
    def export_csv(self, path):
        rows = self.all_jobs()
        with open(path,"w",newline="",encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(["ID","Title","Company","City","Salary","Skill","Description","JobType","Remote"])
            w.writerows(rows)

    def import_csv(self, path):
        cn = self._c(); cur = cn.cursor(); count = 0
        with open(path,newline="",encoding="utf-8") as f:
            for row in csv.reader(f):
                if len(row) >= 5:
                    try:
                        t,c,ci = (row[1],row[2],row[3]) if len(row)>=6 else (row[0],row[1],row[2])
                        sal = float((row[4] if len(row)>=6 else row[3]).strip() or 0)
                        sk  = (row[5] if len(row)>=6 else row[4]).strip()
                        cur.execute("INSERT INTO jobs(title,company,city,salary,skill) VALUES(%s,%s,%s,%s,%s)",
                                    (t.strip(),c.strip(),ci.strip(),sal,sk)); count+=1
                    except Exception: pass
        cn.commit(); cur.close(); cn.close(); return count


# ════════════════════════════════════════════════════════════════
# AI RECOMMENDATION ENGINE
# ════════════════════════════════════════════════════════════════
def _parse_yrs(text):
    m = re.search(r"(\d+)", str(text)); return int(m.group(1)) if m else 0

def _parse_yrs_desc(desc):
    m = re.search(r"(\d+)\+?\s*year", desc.lower()); return int(m.group(1)) if m else 0

def match_score(job, profile):
    """Returns 0-99 match score for (job, user_profile dict)."""
    score = 0.0
    j_skill = (job[5] or "").lower()
    j_city  = (job[3] or "").lower()
    j_sal   = float(job[4] or 0)
    j_desc  = (job[6] or "").lower()
    j_remote= job[8] if len(job)>8 else 0

    u_skills = [s.strip().lower() for s in (profile.get("skills") or "").split(",") if s.strip()]
    u_loc    = (profile.get("location") or "").lower()
    u_sal    = float(profile.get("salary_exp") or 0)
    u_exp    = _parse_yrs(profile.get("experience") or "")

    # Skills 40 %
    if u_skills:
        sk = 0
        for us in u_skills:
            if us in j_skill or j_skill in us: sk = 100; break
            for w in j_skill.split():
                if w and w in us: sk = max(sk, 55)
        score += sk * 0.40
    else:
        score += 20

    # Experience 25 %
    req = _parse_yrs_desc(j_desc)
    if req == 0:      score += 25
    elif u_exp >= req: score += 25
    elif u_exp > 0:   score += max(0, 25*(u_exp/req))

    # Location 20 %
    if not u_loc or j_remote:    score += 20
    elif u_loc in j_city or j_city in u_loc: score += 20
    else:                        score += 5

    # Salary 15 %
    if u_sal == 0:         score += 10
    elif j_sal >= u_sal:   score += 15
    elif j_sal >= u_sal*0.8: score += 8
    else:                  score += 2

    return min(int(score), 99)


# ════════════════════════════════════════════════════════════════
# REUSABLE WIDGET HELPERS
# ════════════════════════════════════════════════════════════════
def _shadow(widget, blur=18, offset=(0,4), alpha=40):
    sh = QGraphicsDropShadowEffect()
    sh.setBlurRadius(blur); sh.setOffset(*offset)
    sh.setColor(QColor(0,0,0,alpha)); widget.setGraphicsEffect(sh)

def _lbl(text, size=13, bold=False, color=C_TEXT, obj=None):
    l = QLabel(text)
    style = f"color:{color}; font-size:{size}px;"
    if bold: style += " font-weight:700;"
    l.setStyleSheet(style)
    if obj: l.setObjectName(obj)
    return l


class AnimatedButton(QPushButton):
    """A QPushButton with a soft glow animation on hover and a quick
    press animation, giving buttons a bit of life without touching
    layout geometry (Qt/QSS alone has no transition support)."""
    def __init__(self, text="", parent=None):
        super().__init__(text, parent)
        self.setCursor(Qt.PointingHandCursor)
        self._glow = QGraphicsDropShadowEffect(self)
        self._glow.setBlurRadius(0)
        self._glow.setOffset(0, 2)
        self._glow.setColor(QColor(C_ACCENT))
        self.setGraphicsEffect(self._glow)
        self._anim = QPropertyAnimation(self._glow, b"blurRadius", self)
        self._anim.setDuration(220)
        self._anim.setEasingCurve(QEasingCurve.OutCubic)

    def _animate_to(self, value):
        self._anim.stop()
        self._anim.setStartValue(self._glow.blurRadius())
        self._anim.setEndValue(value)
        self._anim.start()

    def enterEvent(self, e):
        self._animate_to(24)
        super().enterEvent(e)

    def leaveEvent(self, e):
        self._animate_to(0)
        super().leaveEvent(e)

    def mousePressEvent(self, e):
        self._animate_to(6)
        super().mousePressEvent(e)

    def mouseReleaseEvent(self, e):
        self._animate_to(24 if self.underMouse() else 0)
        super().mouseReleaseEvent(e)


def _btn(text, obj=None, fixed_h=None):
    b = AnimatedButton(text)
    if obj: b.setObjectName(obj)
    if fixed_h: b.setFixedHeight(fixed_h)
    return b

def _sep(horizontal=True):
    f = QFrame()
    f.setFrameShape(QFrame.HLine if horizontal else QFrame.VLine)
    f.setStyleSheet(f"color:{C_BORDER};")
    return f


# ════════════════════════════════════════════════════════════════
# SIDEBAR
# ════════════════════════════════════════════════════════════════
class Sidebar(QWidget):
    page_changed = Signal(str)
    NAV = [("🏠","Dashboard"),("💼","Jobs"),("📄","Applications"),
           ("📊","Analytics"),("🤖","AI Match"),("👤","Profile"),("⚙","Settings")]

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("sidebar")
        self.setFixedWidth(220)
        self._expanded = True
        self._btns = {}
        self._build()

    def _build(self):
        root = QVBoxLayout(self); root.setContentsMargins(0,0,0,0); root.setSpacing(0)

        # header
        hdr = QWidget(); hdr.setFixedHeight(64)
        hdr.setStyleSheet(f"background:{C_SIDEBAR}; border-bottom:1px solid {C_BORDER};")
        hl = QHBoxLayout(hdr); hl.setContentsMargins(18,0,14,0)
        self._brand = QLabel("Job Market AI")
        self._brand.setObjectName("brand")
        self._brand.setStyleSheet(f"font-size:15px;font-weight:800;color:{C_ACCENT};letter-spacing:1px;")
        hl.addWidget(self._brand)
        hl.addStretch()
        tog = QPushButton("☰"); tog.setFixedSize(30,30)
        tog.setCursor(Qt.PointingHandCursor)
        tog.setStyleSheet(f"QPushButton{{background:{C_CARD2};border:1px solid {C_BORDER};border-radius:6px;color:{C_MUTED};font-size:15px;}}"
                          f"QPushButton:hover{{background:#EFF6F1;color:{C_ACCENT};border-color:{C_ACCENT};}}")
        tog.clicked.connect(self.toggle)
        hl.addWidget(tog)
        root.addWidget(hdr)

        # nav
        nav_w = QWidget(); nav_w.setStyleSheet("background:transparent;")
        self._nav_lay = QVBoxLayout(nav_w)
        self._nav_lay.setContentsMargins(10,14,10,0); self._nav_lay.setSpacing(3)
        for icon,name in self.NAV:
            b = self._nav_btn(icon, name)
            self._nav_lay.addWidget(b); self._btns[name] = b
        self._nav_lay.addStretch()
        root.addWidget(nav_w, 1)

        # footer
        ft = QWidget()
        ft.setStyleSheet(f"background:transparent; border-top:1px solid {C_BORDER};")
        fl = QVBoxLayout(ft); fl.setContentsMargins(10,10,10,18)
        lo = self._nav_btn("🚪","Logout", danger=True)
        fl.addWidget(lo)
        root.addWidget(ft)

        self.set_active("Dashboard")

    def _nav_btn(self, icon, name, danger=False):
        b = QPushButton(f"  {icon}  {name}")
        b.setFixedHeight(42); b.setCheckable(True); b.setCursor(Qt.PointingHandCursor)
        ac = C_DANGER if danger else C_ACCENT
        hbg = "#FBEAE7" if danger else "#EAF4EC"
        b.setStyleSheet(f"""
            QPushButton{{background:transparent;border:none;border-radius:8px;
                text-align:left;padding-left:10px;color:{C_MUTED};font-size:13px;font-weight:500;}}
            QPushButton:hover{{background:{hbg};color:{C_TEXT};}}
            QPushButton:checked{{background:{hbg};color:{ac};font-weight:700;
                border-left:3px solid {ac};}}""")
        b.clicked.connect(lambda _=False, n=name: self._click(n))
        return b

    def _click(self, name):
        if name != "Logout": self.set_active(name)
        self.page_changed.emit(name)

    def set_active(self, name):
        for n,b in self._btns.items(): b.setChecked(n == name)

    def show_items(self, names):
        for n,b in self._btns.items(): b.setVisible(n in names)

    def toggle(self):
        self._expanded = not self._expanded
        tw = 220 if self._expanded else 60
        for prop in (b"minimumWidth", b"maximumWidth"):
            a = QPropertyAnimation(self, prop)
            a.setDuration(200); a.setEndValue(tw)
            a.setEasingCurve(QEasingCurve.OutCubic); a.start()
        self._brand.setVisible(self._expanded)
        if not hasattr(self,"_anims"): self._anims=[]
        self._anims.clear()


# ════════════════════════════════════════════════════════════════
# STAT CARD
# ════════════════════════════════════════════════════════════════
class StatCard(QFrame):
    def __init__(self, title, value, subtitle="", icon="💡", color=C_ACCENT):
        super().__init__()
        self.setObjectName("card"); self.setMinimumSize(160,110)
        lay = QVBoxLayout(self); lay.setContentsMargins(18,16,18,16); lay.setSpacing(4)
        top = QHBoxLayout()
        ic = QLabel(icon); ic.setStyleSheet(f"font-size:20px;")
        top.addWidget(ic); top.addStretch()
        lay.addLayout(top)
        self._v = QLabel(str(value))
        self._v.setStyleSheet(f"font-size:26px;font-weight:800;color:{color};")
        lay.addWidget(self._v)
        tl = QLabel(title.upper())
        tl.setStyleSheet(f"font-size:11px;color:{C_MUTED};font-weight:600;letter-spacing:0.5px;")
        lay.addWidget(tl)
        if subtitle:
            sl = QLabel(subtitle); sl.setStyleSheet(f"font-size:11px;color:{C_SUCCESS};")
            lay.addWidget(sl)
        _shadow(self)

    def set_value(self, v):
        self._v.setText(str(v))
        # subtle fade-in whenever the value refreshes
        eff = QGraphicsOpacityEffect(self._v)
        self._v.setGraphicsEffect(eff)
        anim = QPropertyAnimation(eff, b"opacity", self._v)
        anim.setDuration(380)
        anim.setStartValue(0.15)
        anim.setEndValue(1.0)
        anim.setEasingCurve(QEasingCurve.OutCubic)
        anim.start(QPropertyAnimation.DeleteWhenStopped)
        self._v._fade_anim = anim  # keep a reference alive

    def enterEvent(self, e):
        self.setStyleSheet(f"QFrame#card{{background:{C_CARD2};border:1px solid {C_ACCENT};border-radius:14px;}}")
    def leaveEvent(self, e):
        self.setStyleSheet("")


# ════════════════════════════════════════════════════════════════
# JOB CARD
# ════════════════════════════════════════════════════════════════
class JobCard(QFrame):
    apply_clicked = Signal(int)
    view_clicked  = Signal(int)

    def __init__(self, job, show_apply=True, match=None):
        super().__init__()
        # job = (id,title,company,city,salary,skill,description,job_type,remote)
        self._jid = job[0]; self.setObjectName("card"); self.setMinimumHeight(126)
        lay = QVBoxLayout(self); lay.setContentsMargins(18,14,18,14); lay.setSpacing(6)

        # title row
        r1 = QHBoxLayout()
        tl = QLabel(job[1]); tl.setStyleSheet(f"font-size:15px;font-weight:700;color:{C_TEXT};")
        r1.addWidget(tl)
        if match is not None:
            mc = C_SUCCESS if match>=80 else C_WARNING if match>=60 else C_MUTED
            ml = QLabel(f"🤖 {match}% match")
            ml.setStyleSheet(f"font-size:11px;color:{mc};font-weight:700;background:{mc}22;border-radius:8px;padding:2px 8px;")
            r1.addWidget(ml)
        r1.addStretch()
        if len(job)>8 and job[8]:
            rl = QLabel("🌐 Remote")
            rl.setStyleSheet(f"font-size:11px;color:{C_SUCCESS};background:#E7F5EC;border-radius:10px;padding:2px 8px;")
            r1.addWidget(rl)
        lay.addLayout(r1)

        # meta
        r2 = QHBoxLayout(); r2.setSpacing(14)
        for txt in [f"🏢 {job[2]}", f"📍 {job[3]}", f"💰 ${int(job[4]):,}/yr"]:
            l = QLabel(txt); l.setStyleSheet(f"font-size:12px;color:{C_MUTED};")
            r2.addWidget(l)
        if len(job)>7 and job[7]:
            jt = QLabel(job[7]); jt.setStyleSheet(f"font-size:11px;color:{C_MUTED};")
            r2.addWidget(jt)
        r2.addStretch(); lay.addLayout(r2)

        # skill tags
        r3 = QHBoxLayout(); r3.setSpacing(6)
        for tag in (job[5] or "").split(",")[:5]:
            if tag.strip():
                t = QLabel(tag.strip()); t.setObjectName("tag"); r3.addWidget(t)
        r3.addStretch(); lay.addLayout(r3)

        # buttons
        rb = QHBoxLayout(); rb.addStretch()
        vb = _btn("View Details","secondary",34)
        vb.clicked.connect(lambda: self.view_clicked.emit(self._jid)); rb.addWidget(vb)
        if show_apply:
            ab = _btn("Apply Now",fixed_h=34)
            ab.clicked.connect(lambda: self.apply_clicked.emit(self._jid)); rb.addWidget(ab)
        lay.addLayout(rb)
        _shadow(self, blur=14, alpha=30)

    def enterEvent(self, e):
        self.setStyleSheet(f"QFrame#card{{background:{C_CARD2};border:1px solid {C_ACCENT};border-radius:14px;}}")
    def leaveEvent(self, e):
        self.setStyleSheet("")


# ════════════════════════════════════════════════════════════════
# SCROLL CARD CONTAINER
# ════════════════════════════════════════════════════════════════
class CardScroll(QScrollArea):
    def __init__(self):
        super().__init__(); self.setWidgetResizable(True); self.setFrameShape(QFrame.NoFrame)
        self._c = QWidget(); self._l = QVBoxLayout(self._c)
        self._l.setContentsMargins(0,0,6,0); self._l.setSpacing(10)
        self._l.addStretch(); self.setWidget(self._c)

    def clear(self):
        while self._l.count() > 1:
            item = self._l.takeAt(0)
            if item.widget(): item.widget().deleteLater()

    def add(self, w): self._l.insertWidget(self._l.count()-1, w)


# ════════════════════════════════════════════════════════════════
# APPLY DIALOG
# ════════════════════════════════════════════════════════════════
class ApplyDlg(QDialog):
    def __init__(self, job, user, parent=None):
        super().__init__(parent); self.setWindowTitle("Apply for Job")
        self.setMinimumSize(520,560); self._job=job; self._user=user; self._resume=""
        self.setStyleSheet(f"background:{C_CARD};"); self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(28,24,28,24); lay.setSpacing(10)
        lay.addWidget(_lbl(f"Apply — {self._job[1]}",18,True))
        lay.addWidget(_lbl(f"{self._job[2]} · {self._job[3]}",12,color=C_MUTED))
        lay.addWidget(_sep())
        fm = QFormLayout(); fm.setSpacing(10); fm.setLabelAlignment(Qt.AlignLeft)
        self._nm = QLineEdit(); self._em = QLineEdit()
        self._ph = QLineEdit(); self._ex = QLineEdit()
        self._ed = QLineEdit(); self._cv = QTextEdit(); self._cv.setFixedHeight(72)
        self._cv.setPlaceholderText("Brief cover letter (optional)")
        if self._user: self._nm.setText(self._user[1]); self._em.setText(self._user[2])
        for lbl,w in [("Full Name *",self._nm),("Email *",self._em),("Phone",self._ph),
                       ("Experience",self._ex),("Education",self._ed),("Cover Letter",self._cv)]:
            ll = QLabel(lbl); ll.setStyleSheet(f"color:{C_MUTED};font-size:12px;font-weight:600;")
            fm.addRow(ll,w)
        lay.addLayout(fm)
        rr = QHBoxLayout()
        self._rl = QLabel("No file selected"); self._rl.setStyleSheet(f"color:{C_MUTED};font-size:12px;")
        pb = _btn("📎 Choose Resume (PDF)","secondary"); pb.clicked.connect(self._pick)
        rr.addWidget(pb); rr.addWidget(self._rl,1); lay.addLayout(rr)
        lay.addStretch()
        br = QHBoxLayout(); br.addStretch()
        ca = _btn("Cancel","secondary"); ca.clicked.connect(self.reject); br.addWidget(ca)
        ok = _btn("Submit Application"); ok.clicked.connect(self._submit); br.addWidget(ok)
        lay.addLayout(br)

    def _pick(self):
        p,_ = QFileDialog.getOpenFileName(self,"Select Resume","","PDF Files (*.pdf)")
        if p: self._resume=p; self._rl.setText(os.path.basename(p)); self._rl.setStyleSheet(f"color:{C_SUCCESS};font-size:12px;")

    def _submit(self):
        n=self._nm.text().strip(); e=self._em.text().strip()
        if not n or not e: QMessageBox.warning(self,"Required","Name and Email are required."); return
        if not self._resume: QMessageBox.warning(self,"Required","Please select your resume PDF."); return
        self._r={"name":n,"email":e,"phone":self._ph.text().strip(),
                 "exp":self._ex.text().strip(),"edu":self._ed.text().strip(),
                 "cover":self._cv.toPlainText().strip(),"resume":self._resume}
        self.accept()

    def get(self): return getattr(self,"_r",None)


# ════════════════════════════════════════════════════════════════
# JOB FORM DIALOG
# ════════════════════════════════════════════════════════════════
class JobDlg(QDialog):
    def __init__(self, job=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Post Job" if not job else "Edit Job")
        self.setMinimumSize(520,540); self._job=job
        self.setStyleSheet(f"background:{C_CARD};"); self._build()

    def _build(self):
        lay = QVBoxLayout(self); lay.setContentsMargins(28,24,28,24); lay.setSpacing(10)
        lay.addWidget(_lbl("Post a New Job" if not self._job else "Edit Job",18,True))
        fm = QFormLayout(); fm.setSpacing(10)
        self._ti=QLineEdit(); self._co=QLineEdit(); self._ci=QLineEdit()
        self._sa=QLineEdit(); self._sk=QLineEdit()
        self._de=QTextEdit(); self._de.setFixedHeight(88)
        self._jt=QComboBox(); self._jt.addItems(["Full-time","Part-time","Contract","Internship"])
        self._re=QCheckBox("Remote / Hybrid")
        for lbl,w in [("Job Title *",self._ti),("Company *",self._co),("City *",self._ci),
                       ("Annual Salary ($) *",self._sa),("Required Skill *",self._sk),
                       ("Description",self._de),("Job Type",self._jt)]:
            ll=QLabel(lbl); ll.setStyleSheet(f"color:{C_MUTED};font-size:12px;font-weight:600;")
            fm.addRow(ll,w)
        fm.addRow("",self._re); lay.addLayout(fm)
        if self._job:
            self._ti.setText(self._job[1]); self._co.setText(self._job[2])
            self._ci.setText(self._job[3]); self._sa.setText(str(int(self._job[4])))
            self._sk.setText(self._job[5])
            if len(self._job)>6 and self._job[6]: self._de.setPlainText(self._job[6])
            if len(self._job)>7:
                i=self._jt.findText(self._job[7])
                if i>=0: self._jt.setCurrentIndex(i)
            if len(self._job)>8: self._re.setChecked(bool(self._job[8]))
        lay.addStretch()
        br=QHBoxLayout(); br.addStretch()
        ca=_btn("Cancel","secondary"); ca.clicked.connect(self.reject); br.addWidget(ca)
        ok=_btn("Save Job"); ok.clicked.connect(self._save); br.addWidget(ok)
        lay.addLayout(br)

    def _save(self):
        t=self._ti.text().strip(); c=self._co.text().strip(); ci=self._ci.text().strip()
        s=self._sa.text().strip(); sk=self._sk.text().strip()
        if not all([t,c,ci,s,sk]): QMessageBox.warning(self,"Required","Fill all required fields."); return
        try: float(s)
        except ValueError: QMessageBox.warning(self,"Error","Salary must be a number."); return
        self._r={"title":t,"company":c,"city":ci,"salary":float(s),"skill":sk,
                 "desc":self._de.toPlainText().strip(),"jtype":self._jt.currentText(),
                 "remote":1 if self._re.isChecked() else 0}
        self.accept()

    def get(self): return getattr(self,"_r",None)


# ════════════════════════════════════════════════════════════════
# JOB DETAIL DIALOG
# ════════════════════════════════════════════════════════════════
class JobDetailDlg(QDialog):
    apply_clicked = Signal(int)
    def __init__(self, job, parent=None):
        super().__init__(parent); self.setWindowTitle("Job Details")
        self.setMinimumSize(560,480); self._jid=job[0]
        self.setStyleSheet(f"background:{C_CARD};"); self._build(job)

    def _build(self, j):
        lay = QVBoxLayout(self); lay.setContentsMargins(30,26,30,26); lay.setSpacing(10)
        lay.addWidget(_lbl(j[1],22,True))
        meta = QHBoxLayout(); meta.setSpacing(20)
        for txt in [f"🏢 {j[2]}", f"📍 {j[3]}", f"💰 ${int(j[4]):,}/yr"]:
            l=QLabel(txt); l.setStyleSheet(f"font-size:13px;color:{C_MUTED};"); meta.addWidget(l)
        if len(j)>7: jt=QLabel(j[7]); jt.setStyleSheet(f"font-size:12px;color:{C_MUTED};"); meta.addWidget(jt)
        if len(j)>8 and j[8]:
            rl=QLabel("🌐 Remote"); rl.setStyleSheet(f"font-size:12px;color:{C_SUCCESS};font-weight:700;"); meta.addWidget(rl)
        meta.addStretch(); lay.addLayout(meta)
        lay.addWidget(_sep())
        # skills
        sr=QHBoxLayout(); sr.setSpacing(6)
        sl=QLabel("Skills:"); sl.setStyleSheet(f"color:{C_MUTED};font-size:12px;font-weight:600;"); sr.addWidget(sl)
        for tag in (j[5] or "").split(","):
            if tag.strip():
                tl=QLabel(tag.strip()); tl.setObjectName("tag"); sr.addWidget(tl)
        sr.addStretch(); lay.addLayout(sr)
        # description
        if len(j)>6 and j[6]:
            lay.addWidget(_lbl("About the Role",13,True,C_TEXT))
            desc=QLabel(j[6]); desc.setWordWrap(True)
            desc.setStyleSheet(f"color:{C_MUTED};font-size:13px;line-height:1.5;"); lay.addWidget(desc)
        lay.addStretch()
        lay.addWidget(_sep())
        br=QHBoxLayout(); br.addStretch()
        cl=_btn("Close","secondary"); cl.clicked.connect(self.reject); br.addWidget(cl)
        ap=_btn("Apply Now"); ap.clicked.connect(lambda: (self.apply_clicked.emit(self._jid),self.accept())); br.addWidget(ap)
        lay.addLayout(br)


# ════════════════════════════════════════════════════════════════
# CHART HELPER
# ════════════════════════════════════════════════════════════════
class ChartWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self._lay = QVBoxLayout(self); self._lay.setContentsMargins(0,0,0,0)
        self._canvas = None

    def render(self, chart_type, db):
        if not HAS_MPL:
            self._lay.addWidget(_lbl("matplotlib not installed",12,color=C_MUTED)); return
        if self._canvas:
            self._lay.removeWidget(self._canvas); self._canvas.deleteLater(); self._canvas=None

        fig, ax = plt.subplots(figsize=(5.4, 3.2), dpi=96)
        fig.patch.set_facecolor(C_CARD); ax.set_facecolor(C_CARD)
        for s in ["top","right","left","bottom"]: ax.spines[s].set_visible(False)
        ax.tick_params(colors=C_MUTED, labelsize=8)

        if chart_type == "skills":
            data = db.chart_skills()
            if data:
                labs,vals = zip(*data)
                ax.pie(vals, labels=labs, autopct='%1.0f%%',
                       colors=CHART_COLORS[:len(labs)], startangle=140,
                       textprops=dict(fontsize=8,color=C_TEXT))
                ax.set_title("Skills Demand",fontsize=10,weight="bold",color=C_TEXT,pad=8)

        elif chart_type == "city":
            data = db.chart_cities()
            if data:
                cities,counts = zip(*data)
                bars = ax.bar(cities, counts, color=C_ACCENT, width=0.55)
                ax.set_title("Jobs by City",fontsize=10,weight="bold",color=C_TEXT,pad=8)
                for b in bars:
                    ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.1,
                            str(int(b.get_height())),ha="center",fontsize=8,color=C_TEXT)
                ax.tick_params(axis="x",labelrotation=30); ax.yaxis.set_visible(False)

        elif chart_type == "salary":
            data = db.chart_salary()
            if data:
                skills,avgs = zip(*data); avgs=[a/1000 for a in avgs]
                bars = ax.bar(skills, avgs, color=C_ACCENT2, width=0.55)
                ax.set_title("Avg Salary by Skill ($K)",fontsize=10,weight="bold",color=C_TEXT,pad=8)
                for b in bars:
                    ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.5,
                            f"${b.get_height():.0f}k",ha="center",fontsize=8,color=C_TEXT)
                ax.tick_params(axis="x",labelrotation=30); ax.yaxis.set_visible(False)

        elif chart_type == "company":
            data = db.chart_companies()
            if data:
                cos,counts = zip(*data)
                ax.barh(range(len(cos)), counts, color=C_ACCENT, height=0.55)
                ax.set_yticks(range(len(cos))); ax.set_yticklabels(cos,fontsize=8,color=C_TEXT)
                ax.set_title("Top Companies",fontsize=10,weight="bold",color=C_TEXT,pad=8)
                ax.xaxis.set_visible(False); ax.invert_yaxis()

        fig.tight_layout(pad=1.0)
        self._canvas = FigureCanvasQTAgg(fig)
        self._canvas.setStyleSheet("background:transparent;")
        self._lay.addWidget(self._canvas)
        plt.close(fig)


# ════════════════════════════════════════════════════════════════
# PAGE BASE
# ════════════════════════════════════════════════════════════════
class Page(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.setObjectName("page")
        self.setStyleSheet(f"QWidget#page{{background:{C_BG};}}")

    @property
    def db(self): return self.app.db

    @property
    def user(self): return self.app.current_user

    def on_show(self): pass


# ════════════════════════════════════════════════════════════════
# LOGIN PAGE
# ════════════════════════════════════════════════════════════════
class LoginPage(Page):
    def __init__(self, app):
        super().__init__(app)
        outer = QVBoxLayout(self); outer.setAlignment(Qt.AlignCenter)
        card = QFrame(); card.setObjectName("card")
        card.setFixedSize(420,500); card.setStyleSheet(f"QFrame#card{{background:{C_CARD};border:1px solid {C_BORDER};border-radius:16px;}}")
        _shadow(card,30,(0,8),45)
        lay = QVBoxLayout(card); lay.setContentsMargins(40,36,40,36); lay.setSpacing(12)

        brand = QLabel("⬡ Job Market AI"); brand.setAlignment(Qt.AlignCenter)
        brand.setStyleSheet(f"font-size:22px;font-weight:800;color:{C_ACCENT};letter-spacing:1px;")
        lay.addWidget(brand)
        sub = QLabel("Sign in to your account"); sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(f"font-size:13px;color:{C_MUTED};margin-bottom:8px;")
        lay.addWidget(sub)

        self._role_lbl = QLabel("Logging in as: Job Seeker")
        self._role_lbl.setAlignment(Qt.AlignCenter)
        self._role_lbl.setStyleSheet(f"font-size:11px;color:{C_ACCENT2};font-weight:700;")
        lay.addWidget(self._role_lbl)
        lay.addSpacing(4)

        for attr,ph,sec in [("_em","Email address",False),("_pw","Password",True)]:
            e=QLineEdit(); e.setPlaceholderText(ph)
            if sec: e.setEchoMode(QLineEdit.Password)
            e.setFixedHeight(44); setattr(self,attr,e); lay.addWidget(e)

        self._pw.returnPressed.connect(self._login)
        ok=_btn("Sign In",fixed_h=44); ok.clicked.connect(self._login); lay.addWidget(ok)

        hr=QHBoxLayout(); hr.addStretch()
        hr.addWidget(_lbl("Don't have an account?",11,color=C_MUTED))
        reg=QPushButton("Register"); reg.setObjectName("ghost"); reg.setCursor(Qt.PointingHandCursor)
        reg.clicked.connect(lambda: app.show_page("register")); hr.addWidget(reg); hr.addStretch()
        lay.addLayout(hr)

        back=_btn("← Back","secondary",36); back.clicked.connect(lambda: app.show_page("start")); lay.addWidget(back)
        outer.addWidget(card)

    def set_role(self, role):
        self._role_lbl.setText(f"Logging in as: {role}")

    def _login(self):
        em=self._em.text().strip(); pw=self._pw.text().strip()
        if not em or not pw: QMessageBox.warning(self,"Error","Please fill in all fields."); return
        try:
            u=self.db.login(em,pw)
        except Exception as e:
            QMessageBox.critical(self,"Database Error",f"Could not sign in:\n{e}"); return
        if not u: QMessageBox.critical(self,"Failed","Invalid email or password."); return
        self._pw.clear()
        self.app.login_success(u)


# ════════════════════════════════════════════════════════════════
# REGISTER PAGE
# ════════════════════════════════════════════════════════════════
class RegisterPage(Page):
    def __init__(self, app):
        super().__init__(app)
        outer = QVBoxLayout(self); outer.setAlignment(Qt.AlignCenter)
        card = QFrame(); card.setObjectName("card")
        card.setFixedSize(440,560); card.setStyleSheet(f"QFrame#card{{background:{C_CARD};border:1px solid {C_BORDER};border-radius:16px;}}")
        _shadow(card,30,(0,8),45)
        lay = QVBoxLayout(card); lay.setContentsMargins(40,36,40,36); lay.setSpacing(12)

        brand = QLabel("Create Account"); brand.setAlignment(Qt.AlignCenter)
        brand.setStyleSheet(f"font-size:22px;font-weight:800;color:{C_TEXT};")
        lay.addWidget(brand)
        sub=QLabel("Join Job Market AI"); sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(f"font-size:13px;color:{C_MUTED};margin-bottom:8px;"); lay.addWidget(sub)

        for attr,ph in [("_nm","Full Name"),("_em","Email Address"),("_pw","Password")]:
            e=QLineEdit(); e.setPlaceholderText(ph); e.setFixedHeight(44)
            if ph=="Password": e.setEchoMode(QLineEdit.Password)
            setattr(self,attr,e); lay.addWidget(e)

        rl=QLabel("I am a:"); rl.setStyleSheet(f"color:{C_MUTED};font-size:12px;font-weight:600;"); lay.addWidget(rl)
        rr=QHBoxLayout()
        self._r_seeker=QRadioButton("Job Seeker"); self._r_seeker.setChecked(True)
        self._r_emp=QRadioButton("Employer")
        for rb in [self._r_seeker,self._r_emp]: rr.addWidget(rb)
        rr.addStretch(); lay.addLayout(rr)

        ok=_btn("Create Account",fixed_h=44); ok.clicked.connect(self._register); lay.addWidget(ok)
        hr=QHBoxLayout(); hr.addStretch()
        hr.addWidget(_lbl("Already have an account?",11,color=C_MUTED))
        si=QPushButton("Sign in"); si.setObjectName("ghost"); si.setCursor(Qt.PointingHandCursor)
        si.clicked.connect(lambda: app.show_page("login")); hr.addWidget(si); hr.addStretch(); lay.addLayout(hr)
        back=_btn("← Back","secondary",36); back.clicked.connect(lambda: app.show_page("start")); lay.addWidget(back)
        outer.addWidget(card)

    def _register(self):
        n=self._nm.text().strip(); e=self._em.text().strip(); p=self._pw.text().strip()
        if not all([n,e,p]): QMessageBox.warning(self,"Error","All fields are required."); return
        role="Employer" if self._r_emp.isChecked() else "Seeker"
        try:
            ok = self.db.register(n,e,p,role)
        except Exception as ex:
            QMessageBox.critical(self,"Database Error",f"Could not register:\n{ex}"); return
        if not ok:
            QMessageBox.critical(self,"Error","Email already registered."); return
        QMessageBox.information(self,"Success",f"Welcome, {n}!\nYou can now log in.")
        for w in [self._nm,self._em,self._pw]: w.clear()
        self.app.show_page("login")


# ════════════════════════════════════════════════════════════════
# START PAGE
# ════════════════════════════════════════════════════════════════
class StartPage(Page):
    def __init__(self, app):
        super().__init__(app)
        lay = QVBoxLayout(self); lay.setAlignment(Qt.AlignCenter); lay.setSpacing(0)

        brand = QLabel("Job Market AI")
        brand.setAlignment(Qt.AlignCenter)
        brand.setStyleSheet(f"font-size:42px;font-weight:900;color:{C_ACCENT};letter-spacing:2px;")
        lay.addWidget(brand)
        sub=QLabel("The AI-powered job platform")
        sub.setAlignment(Qt.AlignCenter)
        sub.setStyleSheet(f"font-size:16px;color:{C_MUTED};margin-bottom:48px;"); lay.addWidget(sub)

        row=QHBoxLayout(); row.setSpacing(24); row.setAlignment(Qt.AlignCenter)
        for icon,title,desc,role in [
            ("💼","Employer","Post jobs & manage applicants","Employer"),
            ("🔍","Job Seeker","Discover opportunities & apply","Seeker"),
        ]:
            c=QFrame(); c.setObjectName("card")
            c.setFixedSize(220,230)
            c.setStyleSheet(f"QFrame#card{{background:{C_CARD};border:1px solid {C_BORDER};border-radius:16px;}}")
            _shadow(c,24,(0,6),35)
            cl=QVBoxLayout(c); cl.setAlignment(Qt.AlignCenter); cl.setSpacing(10)
            il=QLabel(icon); il.setAlignment(Qt.AlignCenter)
            il.setStyleSheet("font-size:40px;"); cl.addWidget(il)
            tl=QLabel(title); tl.setAlignment(Qt.AlignCenter)
            tl.setStyleSheet(f"font-size:16px;font-weight:700;color:{C_TEXT};"); cl.addWidget(tl)
            dl=QLabel(desc); dl.setAlignment(Qt.AlignCenter); dl.setWordWrap(True)
            dl.setStyleSheet(f"font-size:11px;color:{C_MUTED};"); cl.addWidget(dl)
            br=QHBoxLayout()
            li=_btn("Login","secondary",34); li.setFixedWidth(86)
            li.clicked.connect(lambda _=False,r=role: (app.frames["login"].set_role(r), app.show_page("login")))
            re=_btn("Register",fixed_h=34); re.setFixedWidth(86)
            re.clicked.connect(lambda _=False: app.show_page("register"))
            br.addWidget(li); br.addWidget(re); cl.addLayout(br)
            row.addWidget(c)
        lay.addLayout(row)


# ════════════════════════════════════════════════════════════════
# DASHBOARD HOME PAGE
# ════════════════════════════════════════════════════════════════
class DashPage(Page):
    def __init__(self, app):
        super().__init__(app); self._build()

    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(30,24,30,24); lay.setSpacing(16)
        # greeting
        gr=QHBoxLayout()
        self._greet=_lbl("Welcome back 👋",22,True)
        gr.addWidget(self._greet); gr.addStretch()
        self._role_badge=QLabel()
        self._role_badge.setStyleSheet(f"background:{C_ACCENT};color:white;border-radius:10px;padding:4px 12px;font-size:12px;font-weight:700;")
        gr.addWidget(self._role_badge)
        lay.addLayout(gr)
        self._sub=_lbl("Here's what's happening in your job market.",13,color=C_MUTED)
        lay.addWidget(self._sub)

        # stat cards
        self._card_row=QHBoxLayout(); self._card_row.setSpacing(14)
        self._s1=StatCard("Total Jobs","—","","💼",C_ACCENT)
        self._s2=StatCard("Avg Salary","—","","💰",C_SUCCESS)
        self._s3=StatCard("Applications","—","","📄",C_WARNING)
        self._s4=StatCard("Top City","—","","📍",C_ACCENT2)
        for c in [self._s1,self._s2,self._s3,self._s4]:
            self._card_row.addWidget(c)
        lay.addLayout(self._card_row)

        # market insight strip
        insight=QFrame(); insight.setObjectName("card")
        insight.setStyleSheet(f"QFrame#card{{background:{C_CARD};border:1px solid {C_BORDER};border-radius:12px;}}")
        il=QHBoxLayout(insight); il.setContentsMargins(20,16,20,16); il.setSpacing(32)
        self._ins_skill=self._kv("Top Skill","—"); il.addWidget(self._ins_skill)
        self._ins_sal=self._kv("Peak Salary","—"); il.addWidget(self._ins_sal)
        self._ins_pending=self._kv("Pending Apps","—"); il.addWidget(self._ins_pending)
        il.addStretch()
        lay.addWidget(insight)

        # Recent jobs label
        row=QHBoxLayout()
        row.addWidget(_lbl("Recent Job Postings",16,True)); row.addStretch()
        vb=_btn("Browse All Jobs","secondary",34); vb.clicked.connect(lambda: self.app.nav("Jobs")); row.addWidget(vb)
        lay.addLayout(row)

        # scroll area for recent job cards
        self._scroll=CardScroll(); lay.addWidget(self._scroll,1)

    def _kv(self, label, value):
        w=QWidget(); l=QVBoxLayout(w); l.setContentsMargins(0,0,0,0); l.setSpacing(2)
        l.addWidget(_lbl(label,11,color=C_MUTED)); vl=_lbl(value,16,True,C_ACCENT)
        l.addWidget(vl); w._val=vl; return w

    def on_show(self):
        u=self.user
        if u:
            self._greet.setText(f"Welcome back, {u[1]} 👋")
            self._role_badge.setText("Employer" if u[3]=="Employer" else "Job Seeker")
        a=self.db.analytics()
        self._s1.set_value(f"{a['total_jobs']:,}")
        self._s2.set_value(f"${a['avg_salary']:,.0f}")
        stats=self.db.app_stats()
        self._s3.set_value(str(stats["total"]))
        self._s4.set_value(a["top_city"])
        self._ins_skill._val.setText(a["top_skill"])
        self._ins_sal._val.setText(f"${a['max_salary']:,.0f}")
        self._ins_pending._val.setText(str(stats["pending"]))
        # recent jobs
        self._scroll.clear()
        for j in self.db.all_jobs()[:6]:
            c=JobCard(j, show_apply=(u and u[3]=="Seeker"))
            c.apply_clicked.connect(self._apply); c.view_clicked.connect(self._view)
            self._scroll.add(c)

    def _apply(self, jid):
        jobs={j[0]:j for j in self.db.all_jobs()}
        if jid not in jobs: return
        dlg=ApplyDlg(jobs[jid],self.user,self)
        if dlg.exec()==QDialog.Accepted:
            d=dlg.get()
            try:
                self.db.apply(jid,d["name"],d["email"],d["phone"],d["exp"],d["edu"],d["resume"],d["cover"])
            except Exception as e:
                QMessageBox.critical(self,"Error",f"Could not submit application:\n{e}")
                return
            QMessageBox.information(self,"Applied!","Application submitted successfully.")

    def _view(self, jid):
        jobs={j[0]:j for j in self.db.all_jobs()}
        if jid not in jobs: return
        dlg=JobDetailDlg(jobs[jid],self)
        dlg.apply_clicked.connect(self._apply); dlg.exec()


# ════════════════════════════════════════════════════════════════
# JOBS PAGE  (seeker view)
# ════════════════════════════════════════════════════════════════
class JobsPage(Page):
    def __init__(self, app):
        super().__init__(app); self._jobs=[]; self._build()

    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(28,22,28,22); lay.setSpacing(14)
        lay.addWidget(_lbl("Browse Jobs",22,True))

        # search bar
        sr=QHBoxLayout(); sr.setSpacing(10)
        self._kw=QLineEdit(); self._kw.setPlaceholderText("🔍 Search jobs, companies…")
        self._kw.setObjectName("searchBar"); self._kw.setFixedHeight(42)
        self._kw.textChanged.connect(self._filter)
        self._city=QLineEdit(); self._city.setPlaceholderText("📍 City"); self._city.setFixedHeight(42); self._city.setFixedWidth(130)
        self._city.textChanged.connect(self._filter)
        self._skill=QLineEdit(); self._skill.setPlaceholderText("🛠 Skill"); self._skill.setFixedHeight(42); self._skill.setFixedWidth(130)
        self._skill.textChanged.connect(self._filter)
        reset=_btn("Reset","secondary",42); reset.clicked.connect(self._reset)
        sr.addWidget(self._kw,1); sr.addWidget(self._city); sr.addWidget(self._skill); sr.addWidget(reset)
        lay.addLayout(sr)

        # results label
        rl=QHBoxLayout()
        self._count=_lbl("",12,color=C_MUTED); rl.addWidget(self._count); rl.addStretch()
        lay.addLayout(rl)

        # cards
        self._scroll=CardScroll(); lay.addWidget(self._scroll,1)

    def on_show(self):
        self._jobs=self.db.all_jobs(); self._render(self._jobs)

    def _filter(self):
        kw=self._kw.text().strip().lower()
        city=self._city.text().strip().lower()
        skill=self._skill.text().strip().lower()
        res=[j for j in self._jobs if
             (not kw or kw in j[1].lower() or kw in j[2].lower()) and
             (not city or city in j[3].lower()) and
             (not skill or skill in j[5].lower())]
        self._render(res)

    def _reset(self):
        self._kw.clear(); self._city.clear(); self._skill.clear()
        self._render(self._jobs)

    def _render(self, jobs):
        self._scroll.clear()
        u=self.user; is_seeker=(u and u[3]=="Seeker")
        self._count.setText(f"{len(jobs)} job{'s' if len(jobs)!=1 else ''} found")
        for j in jobs:
            c=JobCard(j,show_apply=is_seeker)
            c.apply_clicked.connect(self._apply); c.view_clicked.connect(self._view)
            self._scroll.add(c)

    def _apply(self, jid):
        jobs={j[0]:j for j in self._jobs}
        if jid not in jobs: return
        dlg=ApplyDlg(jobs[jid],self.user,self)
        if dlg.exec()==QDialog.Accepted:
            d=dlg.get()
            try:
                self.db.apply(jid,d["name"],d["email"],d["phone"],d["exp"],d["edu"],d["resume"],d["cover"])
            except Exception as e:
                QMessageBox.critical(self,"Error",f"Could not submit application:\n{e}")
                return
            QMessageBox.information(self,"Applied!","Application submitted.")

    def _view(self, jid):
        jobs={j[0]:j for j in self._jobs}
        if jid not in jobs: return
        dlg=JobDetailDlg(jobs[jid],self)
        dlg.apply_clicked.connect(self._apply); dlg.exec()


# ════════════════════════════════════════════════════════════════
# APPLICATIONS PAGE  (seeker — my apps; employer — manage all)
# ════════════════════════════════════════════════════════════════
class AppsPage(Page):
    def __init__(self, app):
        super().__init__(app); self._build()

    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(28,22,28,22); lay.setSpacing(14)
        self._title=_lbl("Applications",22,True); lay.addWidget(self._title)

        # employer controls
        self._emp_bar=QWidget()
        eb=QHBoxLayout(self._emp_bar); eb.setContentsMargins(0,0,0,0); eb.setSpacing(10)
        self._search=QLineEdit(); self._search.setPlaceholderText("🔍 Search applicants…")
        self._search.setFixedHeight(40); self._search.textChanged.connect(self._load_employer)
        self._status=QComboBox(); self._status.addItems(["All","Pending","Approved","Rejected"])
        self._status.setFixedHeight(40); self._status.setFixedWidth(130)
        self._status.currentTextChanged.connect(self._load_employer)
        eb.addWidget(self._search,1); eb.addWidget(self._status)
        lay.addWidget(self._emp_bar)

        # stat cards (employer)
        self._stat_row=QHBoxLayout(); self._stat_row.setSpacing(12)
        self._st=StatCard("Total","0","","📋",C_ACCENT)
        self._sa=StatCard("Approved","0","","✅",C_SUCCESS)
        self._sr=StatCard("Rejected","0","","❌",C_DANGER)
        self._sp=StatCard("Pending","0","","⏳",C_WARNING)
        for c in [self._st,self._sa,self._sr,self._sp]: self._stat_row.addWidget(c)
        self._stat_widget=QWidget(); self._stat_widget.setLayout(self._stat_row)
        lay.addWidget(self._stat_widget)

        # table (employer)
        self._table=QTableWidget(); self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setColumnCount(7)
        self._table.setHorizontalHeaderLabels(["ID","Job Title","Company","Applicant","Email","Applied On","Status"])
        lay.addWidget(self._table)

        # action buttons (employer)
        self._act=QHBoxLayout()
        app_btn=_btn("✓ Approve","success",36); app_btn.clicked.connect(self._approve)
        rej_btn=_btn("✗ Reject","danger",36); rej_btn.clicked.connect(self._reject)
        res_btn=_btn("📄 Open Resume","secondary",36); res_btn.clicked.connect(self._open_resume)
        ref_btn=_btn("⟳ Refresh","secondary",36); ref_btn.clicked.connect(self._load_employer)
        for b in [app_btn,rej_btn,res_btn,ref_btn]: self._act.addWidget(b)
        self._act.addStretch()
        self._act_widget=QWidget(); self._act_widget.setLayout(self._act)
        lay.addWidget(self._act_widget)

        # seeker view — card list
        self._seeker_scroll=CardScroll(); lay.addWidget(self._seeker_scroll,1)

        self._all_widgets=[self._emp_bar,self._stat_widget,self._table,self._act_widget]

    def on_show(self):
        u=self.user
        if not u: return
        is_emp=(u[3]=="Employer")
        self._title.setText("Application Management" if is_emp else "My Applications")
        # show/hide correct widgets
        self._emp_bar.setVisible(is_emp)
        self._stat_widget.setVisible(is_emp)
        self._table.setVisible(is_emp)
        self._act_widget.setVisible(is_emp)
        self._seeker_scroll.setVisible(not is_emp)
        if is_emp: self._load_employer()
        else: self._load_seeker()

    def _load_employer(self):
        try:
            stats=self.db.app_stats()
            rows=self.db.get_applications(
                self._search.text().strip() if self._search else "",
                self._status.currentText() if self._status else "All")
        except Exception as e:
            QMessageBox.critical(self,"Database Error",f"Could not load applications:\n{e}")
            return
        self._st.set_value(stats["total"]); self._sa.set_value(stats["approved"])
        self._sr.set_value(stats["rejected"]); self._sp.set_value(stats["pending"])
        self._rows_cache = rows
        self._table.setRowCount(len(rows))
        status_color={"Approved":C_SUCCESS,"Rejected":C_DANGER,"Pending":C_WARNING}
        for i,row in enumerate(rows):
            vals=[str(row[0]),row[1],row[2],row[3],row[4],str(row[6])[:10],row[7]]
            for j,v in enumerate(vals):
                item=QTableWidgetItem(v); item.setTextAlignment(Qt.AlignVCenter|Qt.AlignLeft)
                if j==6:
                    item.setForeground(QColor(status_color.get(v,C_MUTED)))
                self._table.setItem(i,j,item)

    def _load_seeker(self):
        self._seeker_scroll.clear()
        try:
            apps=self.db.my_applications(self.user[2])
        except Exception as e:
            QMessageBox.critical(self,"Database Error",f"Could not load your applications:\n{e}")
            return
        if not apps:
            nl=_lbl("No applications yet. Start applying!",13,color=C_MUTED)
            nl.setAlignment(Qt.AlignCenter); self._seeker_scroll.add(nl); return
        sc={"Approved":C_SUCCESS,"Rejected":C_DANGER,"Pending":C_WARNING}
        for row in apps:
            title,company,applied,status=row[0],row[1],row[2],row[3]
            f=QFrame(); f.setObjectName("card")
            f.setStyleSheet(f"QFrame#card{{background:{C_CARD};border:1px solid {C_BORDER};border-radius:12px;}}")
            fl=QHBoxLayout(f); fl.setContentsMargins(20,14,20,14); fl.setSpacing(0)
            info=QVBoxLayout()
            info.addWidget(_lbl(title,14,True))
            info.addWidget(_lbl(company,12,color=C_MUTED))
            info.addWidget(_lbl(f"Applied: {str(applied)[:10]}",11,color=C_MUTED))
            fl.addLayout(info); fl.addStretch()
            sl=QLabel(status); sl.setStyleSheet(f"color:{sc.get(status,C_MUTED)};font-weight:700;font-size:13px;")
            fl.addWidget(sl)
            self._seeker_scroll.add(f)

    def _selected_row(self):
        rows=self._table.selectedItems()
        if not rows: return None
        return int(self._table.item(self._table.currentRow(),0).text())

    def _approve(self):
        aid=self._selected_row()
        if not aid: return
        try:
            self.db.approve_app(aid)
        except Exception as e:
            QMessageBox.critical(self,"Error",f"Could not approve:\n{e}"); return
        self._load_employer()
        QMessageBox.information(self,"Done","Application approved.")

    def _reject(self):
        aid=self._selected_row()
        if not aid: return
        try:
            self.db.reject_app(aid)
        except Exception as e:
            QMessageBox.critical(self,"Error",f"Could not reject:\n{e}"); return
        self._load_employer()
        QMessageBox.information(self,"Done","Application rejected.")

    def _open_resume(self):
        r=self._table.currentRow()
        rows = getattr(self, "_rows_cache", None)
        if r<0 or not rows or r >= len(rows): return
        resume=str(rows[r][5])
        if resume and os.path.exists(resume):
            os.startfile(resume) if sys.platform=="win32" else os.system(f'xdg-open "{resume}"')
        else:
            QMessageBox.warning(self,"Not Found","Resume file not found on disk.")


# ════════════════════════════════════════════════════════════════
# ANALYTICS PAGE
# ════════════════════════════════════════════════════════════════
class AnalyticsPage(Page):
    def __init__(self, app):
        super().__init__(app); self._build()

    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(28,22,28,22); lay.setSpacing(16)
        lay.addWidget(_lbl("Analytics Dashboard",22,True))

        # stat strip
        sr=QHBoxLayout(); sr.setSpacing(12)
        self._s1=StatCard("Total Jobs","—","","📊",C_ACCENT)
        self._s2=StatCard("Avg Salary","—","","💰",C_SUCCESS)
        self._s3=StatCard("Peak Salary","—","","🏆",C_ACCENT2)
        self._s4=StatCard("Top Skill","—","","🛠",C_WARNING)
        for c in [self._s1,self._s2,self._s3,self._s4]: sr.addWidget(c)
        lay.addLayout(sr)

        # chart tabs
        self._tabs=QTabWidget()
        for label,ctype in [("Skills","skills"),("Cities","city"),("Salaries","salary"),("Companies","company")]:
            tab=QWidget(); tab.setStyleSheet(f"background:{C_CARD};")
            tl=QVBoxLayout(tab); tl.setContentsMargins(8,8,8,8)
            cw=ChartWidget(); cw._type=ctype
            tl.addWidget(cw); self._tabs.addTab(tab,label)
        lay.addWidget(self._tabs,1)
        self._tabs.currentChanged.connect(self._tab_changed)

    def _tab_changed(self, idx):
        tab=self._tabs.widget(idx)
        if tab:
            for w in tab.findChildren(ChartWidget):
                w.render(w._type, self.db)

    def on_show(self):
        a=self.db.analytics()
        self._s1.set_value(f"{a['total_jobs']:,}")
        self._s2.set_value(f"${a['avg_salary']:,.0f}")
        self._s3.set_value(f"${a['max_salary']:,.0f}")
        self._s4.set_value(a["top_skill"])
        # render first tab
        self._tab_changed(self._tabs.currentIndex())


# ════════════════════════════════════════════════════════════════
# AI MATCH PAGE
# ════════════════════════════════════════════════════════════════
class AIMatchPage(Page):
    def __init__(self, app):
        super().__init__(app); self._build()

    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(28,22,28,22); lay.setSpacing(14)
        h=QHBoxLayout()
        h.addWidget(_lbl("🤖 AI Job Match",22,True)); h.addStretch()
        rb=_btn("⟳ Refresh Matches","secondary",36); rb.clicked.connect(self.on_show); h.addWidget(rb)
        lay.addLayout(h)
        lay.addWidget(_lbl("Jobs ranked by how well they match your profile.",13,color=C_MUTED))
        self._no_profile=_lbl("Complete your Profile to get personalised matches →",13,color=C_WARNING)
        lay.addWidget(self._no_profile)
        self._scroll=CardScroll(); lay.addWidget(self._scroll,1)

    def on_show(self):
        u=self.user
        if not u: return
        full=self.db.get_user(u[0])
        profile={}
        if full and len(full)>=10:
            profile={"skills":full[4] or "","experience":full[5] or "","location":full[7] or "","salary_exp":full[9] or 0}
        has_profile=bool(profile.get("skills","").strip())
        self._no_profile.setVisible(not has_profile)
        jobs=self.db.all_jobs()
        scored=sorted([(j,match_score(j,profile)) for j in jobs],key=lambda x:x[1],reverse=True)
        self._scroll.clear()
        for j,sc in scored[:15]:
            c=JobCard(j,show_apply=True,match=sc)
            c.apply_clicked.connect(self._apply); c.view_clicked.connect(self._view)
            self._scroll.add(c)

    def _apply(self,jid):
        jobs={j[0]:j for j in self.db.all_jobs()}
        if jid not in jobs: return
        dlg=ApplyDlg(jobs[jid],self.user,self)
        if dlg.exec()==QDialog.Accepted:
            d=dlg.get()
            try:
                self.db.apply(jid,d["name"],d["email"],d["phone"],d["exp"],d["edu"],d["resume"],d["cover"])
            except Exception as e:
                QMessageBox.critical(self,"Error",f"Could not submit application:\n{e}")
                return
            QMessageBox.information(self,"Applied!","Application submitted.")

    def _view(self,jid):
        jobs={j[0]:j for j in self.db.all_jobs()}
        if jid not in jobs: return
        dlg=JobDetailDlg(jobs[jid],self)
        dlg.apply_clicked.connect(self._apply); dlg.exec()


# ════════════════════════════════════════════════════════════════
# PROFILE PAGE
# ════════════════════════════════════════════════════════════════
class ProfilePage(Page):
    def __init__(self, app):
        super().__init__(app); self._build()

    def _build(self):
        outer=QScrollArea(); outer.setWidgetResizable(True); outer.setFrameShape(QFrame.NoFrame)
        content=QWidget()
        lay=QVBoxLayout(self); lay.setContentsMargins(0,0,0,0); lay.addWidget(outer)
        outer.setWidget(content)
        cl=QVBoxLayout(content); cl.setContentsMargins(28,22,28,28); cl.setSpacing(20)
        cl.addWidget(_lbl("My Profile",22,True))

        # profile card
        pc=QFrame(); pc.setObjectName("card")
        pc.setStyleSheet(f"QFrame#card{{background:{C_CARD};border:1px solid {C_BORDER};border-radius:14px;}}")
        pl=QVBoxLayout(pc); pl.setContentsMargins(28,24,28,24); pl.setSpacing(10)
        avatar=QLabel("👤"); avatar.setAlignment(Qt.AlignCenter)
        avatar.setStyleSheet(f"font-size:52px;background:{C_CARD2};border-radius:40px;padding:10px;max-width:80px;")
        al=QHBoxLayout(); al.addStretch(); al.addWidget(avatar); al.addStretch(); pl.addLayout(al)
        self._name_lbl=_lbl("",18,True); self._name_lbl.setAlignment(Qt.AlignCenter); pl.addWidget(self._name_lbl)
        self._email_lbl=_lbl("",12,color=C_MUTED); self._email_lbl.setAlignment(Qt.AlignCenter); pl.addWidget(self._email_lbl)
        self._role_lbl=_lbl("",12,bold=True,color=C_ACCENT); self._role_lbl.setAlignment(Qt.AlignCenter); pl.addWidget(self._role_lbl)
        cl.addWidget(pc)

        # form
        fc=QFrame(); fc.setObjectName("card")
        fc.setStyleSheet(f"QFrame#card{{background:{C_CARD};border:1px solid {C_BORDER};border-radius:14px;}}")
        fl=QVBoxLayout(fc); fl.setContentsMargins(28,24,28,24); fl.setSpacing(14)
        fl.addWidget(_lbl("Edit Profile",16,True))
        fm=QFormLayout(); fm.setSpacing(12); fm.setLabelAlignment(Qt.AlignLeft)
        self._f_name=QLineEdit(); self._f_skills=QLineEdit()
        self._f_exp=QLineEdit(); self._f_edu=QLineEdit()
        self._f_loc=QLineEdit(); self._f_sal=QLineEdit()
        self._f_bio=QTextEdit(); self._f_bio.setFixedHeight(80)
        for lbl,w,ph in [
            ("Display Name",self._f_name,"Your name"),
            ("Skills (comma-separated)",self._f_skills,"Python, SQL, React…"),
            ("Years of Experience",self._f_exp,"e.g. 3 years"),
            ("Education",self._f_edu,"e.g. B.Sc Computer Science"),
            ("Location / City",self._f_loc,"e.g. San Francisco"),
            ("Expected Salary ($)",self._f_sal,"e.g. 120000"),
            ("Bio",self._f_bio,"Brief professional summary"),
        ]:
            ll=QLabel(lbl); ll.setStyleSheet(f"color:{C_MUTED};font-size:12px;font-weight:600;")
            if hasattr(w,"setPlaceholderText"): w.setPlaceholderText(ph)
            fm.addRow(ll,w)
        fl.addLayout(fm)
        sb=_btn("Save Profile",fixed_h=42); sb.clicked.connect(self._save); fl.addWidget(sb)
        cl.addWidget(fc)

    def on_show(self):
        u=self.user
        if not u: return
        self._name_lbl.setText(u[1]); self._email_lbl.setText(u[2])
        self._role_lbl.setText("Employer" if u[3]=="Employer" else "Job Seeker")
        try:
            full=self.db.get_user(u[0])
        except Exception as e:
            QMessageBox.critical(self,"Database Error",f"Could not load profile:\n{e}")
            return
        if full and len(full)>=10:
            self._f_name.setText(full[1] or "")
            self._f_skills.setText(full[4] or "")
            self._f_exp.setText(full[5] or "")
            self._f_edu.setText(full[6] or "")
            self._f_loc.setText(full[7] or "")
            self._f_bio.setPlainText(full[8] or "")
            self._f_sal.setText(str(int(full[9])) if full[9] else "")

    def _save(self):
        u=self.user
        if not u: return
        try: sal=float(self._f_sal.text().strip() or 0)
        except ValueError: sal=0
        try:
            self.db.update_profile(u[0],
                self._f_name.text().strip() or u[1],
                self._f_skills.text().strip(),
                self._f_exp.text().strip(),
                self._f_edu.text().strip(),
                self._f_loc.text().strip(),
                self._f_bio.toPlainText().strip(),
                sal)
        except Exception as e:
            QMessageBox.critical(self,"Error",f"Could not save profile:\n{e}")
            return
        QMessageBox.information(self,"Saved","Profile updated successfully.")
        # refresh user name in sidebar
        self.app.refresh_user()


# ════════════════════════════════════════════════════════════════
# SETTINGS PAGE
# ════════════════════════════════════════════════════════════════
class SettingsPage(Page):
    def __init__(self, app):
        super().__init__(app); self._build()

    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(28,22,28,28); lay.setSpacing(20)
        lay.addWidget(_lbl("Settings",22,True))

        # change password
        pc=QFrame(); pc.setObjectName("card")
        pc.setStyleSheet(f"QFrame#card{{background:{C_CARD};border:1px solid {C_BORDER};border-radius:14px;}}")
        pl=QVBoxLayout(pc); pl.setContentsMargins(24,20,24,20); pl.setSpacing(12)
        pl.addWidget(_lbl("Change Password",14,True))
        self._old=QLineEdit(); self._old.setPlaceholderText("Current password"); self._old.setEchoMode(QLineEdit.Password); self._old.setFixedHeight(42)
        self._new=QLineEdit(); self._new.setPlaceholderText("New password"); self._new.setEchoMode(QLineEdit.Password); self._new.setFixedHeight(42)
        self._new2=QLineEdit(); self._new2.setPlaceholderText("Confirm new password"); self._new2.setEchoMode(QLineEdit.Password); self._new2.setFixedHeight(42)
        for w in [self._old,self._new,self._new2]: pl.addWidget(w)
        sb=_btn("Update Password",fixed_h=40); sb.clicked.connect(self._change_pwd); pl.addWidget(sb)
        lay.addWidget(pc)

        # CSV tools
        cc=QFrame(); cc.setObjectName("card")
        cc.setStyleSheet(f"QFrame#card{{background:{C_CARD};border:1px solid {C_BORDER};border-radius:14px;}}")
        ck=QVBoxLayout(cc); ck.setContentsMargins(24,20,24,20); ck.setSpacing(10)
        ck.addWidget(_lbl("Data Import / Export",14,True))
        ck.addWidget(_lbl("Export or import job listings as CSV files.",12,color=C_MUTED))
        br=QHBoxLayout()
        ex=_btn("📤 Export Jobs CSV","secondary",40); ex.clicked.connect(self._export)
        im=_btn("📥 Import Jobs CSV","secondary",40); im.clicked.connect(self._import)
        br.addWidget(ex); br.addWidget(im); br.addStretch(); ck.addLayout(br)
        lay.addWidget(cc)
        lay.addStretch()

    def _change_pwd(self):
        u=self.user
        if not u: return
        old=self._old.text().strip(); nw=self._new.text().strip(); nw2=self._new2.text().strip()
        if not all([old,nw,nw2]): QMessageBox.warning(self,"Required","Fill all password fields."); return
        if nw != nw2: QMessageBox.warning(self,"Mismatch","New passwords do not match."); return
        try:
            check=self.db.login(u[2],old)
            if not check: QMessageBox.critical(self,"Error","Current password is incorrect."); return
            cn=self.db._c(); cur=cn.cursor()
            cur.execute("UPDATE users SET password=%s WHERE id=%s",(nw,u[0]))
            cn.commit(); cur.close(); cn.close()
        except Exception as e:
            QMessageBox.critical(self,"Database Error",f"Could not update password:\n{e}")
            return
        for w in [self._old,self._new,self._new2]: w.clear()
        QMessageBox.information(self,"Done","Password updated.")

    def _export(self):
        path,_=QFileDialog.getSaveFileName(self,"Export CSV","jobs_export.csv","CSV (*.csv)")
        if path:
            try:
                self.db.export_csv(path)
            except Exception as e:
                QMessageBox.critical(self,"Error",f"Could not export:\n{e}"); return
            QMessageBox.information(self,"Exported",f"Saved to {path}")

    def _import(self):
        path,_=QFileDialog.getOpenFileName(self,"Import CSV","","CSV (*.csv)")
        if path:
            try:
                n=self.db.import_csv(path)
            except Exception as e:
                QMessageBox.critical(self,"Error",f"Could not import:\n{e}"); return
            QMessageBox.information(self,"Imported",f"{n} records imported.")


# ════════════════════════════════════════════════════════════════
# EMPLOYER JOBS PAGE  (post / edit / delete)
# ════════════════════════════════════════════════════════════════
class EmployerJobsPage(Page):
    def __init__(self, app):
        super().__init__(app); self._build()

    def _build(self):
        lay=QVBoxLayout(self); lay.setContentsMargins(28,22,28,22); lay.setSpacing(14)
        h=QHBoxLayout()
        h.addWidget(_lbl("My Job Listings",22,True)); h.addStretch()
        nb=_btn("+ Post New Job",fixed_h=38); nb.clicked.connect(self._post); h.addWidget(nb)
        ex=_btn("📤 Export CSV","secondary",38); ex.clicked.connect(self._export); h.addWidget(ex)
        im=_btn("📥 Import CSV","secondary",38); im.clicked.connect(self._import_csv); h.addWidget(im)
        lay.addLayout(h)

        self._table=QTableWidget(); self._table.setAlternatingRowColors(True)
        self._table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self._table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self._table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self._table.setColumnCount(6)
        self._table.setHorizontalHeaderLabels(["ID","Title","Company","City","Salary","Skill"])
        lay.addWidget(self._table,1)

        ab=QHBoxLayout()
        eb=_btn("✏ Edit Selected","secondary",36); eb.clicked.connect(self._edit)
        db=_btn("🗑 Delete","danger",36); db.clicked.connect(self._delete)
        ab.addWidget(eb); ab.addWidget(db); ab.addStretch(); lay.addLayout(ab)

    def on_show(self): self._load()

    def _load(self):
        try:
            rows=self.db.all_jobs()
        except Exception as e:
            QMessageBox.critical(self,"Database Error",f"Could not load jobs:\n{e}")
            return
        self._table.setRowCount(len(rows))
        for i,r in enumerate(rows):
            for j,v in enumerate([r[0],r[1],r[2],r[3],f"${int(r[4]):,}",r[5]]):
                item=QTableWidgetItem(str(v)); item.setTextAlignment(Qt.AlignVCenter|Qt.AlignLeft)
                self._table.setItem(i,j,item)
        self._rows=rows

    def _selected_job(self):
        r=self._table.currentRow()
        if r<0 or r>=len(self._rows): return None
        return self._rows[r]

    def _post(self):
        dlg=JobDlg(parent=self)
        if dlg.exec()==QDialog.Accepted:
            d=dlg.get(); u=self.user
            try:
                self.db.add_job(d["title"],d["company"],d["city"],d["salary"],d["skill"],
                                d["desc"],d["jtype"],d["remote"],u[0] if u else None)
            except Exception as e:
                QMessageBox.critical(self,"Error",f"Could not post job:\n{e}"); return
            self._load()

    def _edit(self):
        j=self._selected_job()
        if not j: QMessageBox.information(self,"Select","Select a job first."); return
        dlg=JobDlg(job=j,parent=self)
        if dlg.exec()==QDialog.Accepted:
            d=dlg.get()
            try:
                self.db.update_job(j[0],d["title"],d["company"],d["city"],d["salary"],
                                   d["skill"],d["desc"],d["jtype"],d["remote"])
            except Exception as e:
                QMessageBox.critical(self,"Error",f"Could not update job:\n{e}"); return
            self._load()

    def _delete(self):
        j=self._selected_job()
        if not j: QMessageBox.information(self,"Select","Select a job first."); return
        if QMessageBox.question(self,"Confirm",f"Delete '{j[1]}'?",
            QMessageBox.Yes|QMessageBox.No)==QMessageBox.Yes:
            try:
                self.db.delete_job(j[0])
            except Exception as e:
                QMessageBox.critical(self,"Error",f"Could not delete job:\n{e}"); return
            self._load()

    def _export(self):
        path,_=QFileDialog.getSaveFileName(self,"Export","jobs.csv","CSV (*.csv)")
        if path:
            try:
                self.db.export_csv(path)
            except Exception as e:
                QMessageBox.critical(self,"Error",f"Could not export:\n{e}"); return
            QMessageBox.information(self,"Done",f"Saved: {path}")

    def _import_csv(self):
        path,_=QFileDialog.getOpenFileName(self,"Import","","CSV (*.csv)")
        if path:
            try:
                n=self.db.import_csv(path)
            except Exception as e:
                QMessageBox.critical(self,"Error",f"Could not import:\n{e}"); return
            QMessageBox.information(self,"Done",f"{n} records imported."); self._load()


# ════════════════════════════════════════════════════════════════
# MAIN WINDOW
# ════════════════════════════════════════════════════════════════
class MainWindow(QMainWindow):
    def __init__(self, db):
        super().__init__()
        self.db = db
        self.current_user = None
        self.setWindowTitle("Job Market AI")
        self.setMinimumSize(1180, 720)
        self.resize(1280, 780)
        self.setStyleSheet(GLOBAL_QSS)
        self._build()

    def _build(self):
        root = QWidget(); self.setCentralWidget(root)
        root.setStyleSheet(f"background:{C_BG};")
        ml = QHBoxLayout(root); ml.setContentsMargins(0,0,0,0); ml.setSpacing(0)

        # ── auth stack (login/register/start) ──
        self._auth_stack = QStackedWidget()
        self._auth_stack.setObjectName("page")

        self.frames = {}
        self.frames["start"]    = StartPage(self)
        self.frames["login"]    = LoginPage(self)
        self.frames["register"] = RegisterPage(self)
        for f in ["start","login","register"]:
            self._auth_stack.addWidget(self.frames[f])

        # ── app shell (sidebar + pages) ──
        self._app_shell = QWidget(); self._app_shell.setStyleSheet(f"background:{C_BG};")
        shell_lay = QHBoxLayout(self._app_shell); shell_lay.setContentsMargins(0,0,0,0); shell_lay.setSpacing(0)

        self._sidebar = Sidebar()
        self._sidebar.page_changed.connect(self._nav)
        shell_lay.addWidget(self._sidebar)

        self._page_stack = QStackedWidget()
        self._page_stack.setObjectName("page")
        shell_lay.addWidget(self._page_stack, 1)

        # pages
        self._pages = {
            "Dashboard":     DashPage(self),
            "Jobs":          JobsPage(self),
            "Applications":  AppsPage(self),
            "Analytics":     AnalyticsPage(self),
            "AI Match":      AIMatchPage(self),
            "Profile":       ProfilePage(self),
            "Settings":      SettingsPage(self),
            "EmployerJobs":  EmployerJobsPage(self),
        }
        for p in self._pages.values():
            self._page_stack.addWidget(p)

        # ── outer switcher ──
        self._outer = QStackedWidget()
        self._outer.addWidget(self._auth_stack)   # idx 0
        self._outer.addWidget(self._app_shell)    # idx 1
        ml.addWidget(self._outer)

        self.show_page("start")

    # ── navigation ────────────────────────────────────────────────
    def show_page(self, name):
        if name in self.frames:
            self._auth_stack.setCurrentWidget(self.frames[name])
            self._outer.setCurrentIndex(0)
        elif name in self._pages:
            self._page_stack.setCurrentWidget(self._pages[name])
            self._pages[name].on_show()
            self._outer.setCurrentIndex(1)

    def nav(self, name):
        self._sidebar.set_active(name)
        self.show_page(name)

    def _nav(self, name):
        if name == "Logout":
            self.logout(); return
        # Employers browse all jobs on "Jobs" tab but use EmployerJobs for management
        if name == "Jobs" and self.current_user and self.current_user[3] == "Employer":
            target = "EmployerJobs"
        else:
            target = name
        self.show_page(target)

    # ── auth ──────────────────────────────────────────────────────
    def login_success(self, user):
        self.current_user = user
        is_emp = (user[3] == "Employer")
        seeker_pages = {"Dashboard","Jobs","Applications","Analytics","AI Match","Profile","Settings"}
        emp_pages    = {"Dashboard","Jobs","Applications","Analytics","Profile","Settings"}
        self._sidebar.show_items(emp_pages if is_emp else seeker_pages)
        self.nav("Dashboard")

    def logout(self):
        self.current_user = None
        self.show_page("start")

    def refresh_user(self):
        if self.current_user:
            row=self.db.get_user(self.current_user[0])
            if row: self.current_user=(row[0],row[1],row[2],row[3])


# ════════════════════════════════════════════════════════════════
# ENTRY POINT
# ════════════════════════════════════════════════════════════════
def main():
    # Create the single QApplication instance FIRST, before anything that
    # could fail and short-circuit main(). Creating a second QApplication
    # later (e.g. in an error branch) is what caused:
    #   "Please destroy the QApplication singleton before creating a new
    #    QApplication instance."
    app = QApplication.instance() or QApplication(sys.argv)
    app.setStyle("Fusion")
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    try:
        db = DB()
    except Exception as e:
        QMessageBox.critical(None, "Database Error",
            f"Cannot connect to MySQL:\n{e}\n\n"
            "Check DB_HOST / DB_USER / DB_PASSWORD / DB_NAME at the top of this file.")
        sys.exit(1)
        return

    win = MainWindow(db)
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
