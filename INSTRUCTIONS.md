# 📘 Job Market Analytics — User Guide

## Overview

A Streamlit-powered analytics dashboard for job market data. Built for both **Job Seekers** and **Employers** to manage listings, track applications, and visualize trends.

---

## Features

### 🔐 Role-Based Authentication
- Two roles: Job Seeker and Employer
- Register new accounts or log in with existing credentials

### 📋 Job Management (Employers)
- Add, edit, delete job listings (title, company, city, salary, skill)
- Search/filter by company, city, or skill
- Import/Export job data via CSV

### 📝 Application Pipeline (Job Seekers)
- Browse all available jobs
- Apply with your name, email, phone, experience, and education
- Track application status (Pending / Approved / Rejected)

### ✅ Application Management (Employers)
- View all applications in a master grid
- Filter by status (All / Pending / Approved / Rejected)
- Approve or reject applications

### 📊 Analytics & Charts
- Key metrics: Total jobs, average salary, max salary, top skill, top city
- Charts for skill distribution, city distribution, salary by skill, and top companies

### 🎨 UI / UX
- Dark space-themed design with purple accents
- Responsive layout with sidebar navigation

---

## Getting Started

### Prerequisites
- Python 3.9+
- MySQL 8+ running locally

### Installation
ash
# Clone the repo
git clone https://github.com/PooravGahlan/job-market-analytics.git
cd job-market-analytics

# Create virtual environment
python -m venv venv
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Configure database
cp .env.example .env
# Edit .env with your MySQL credentials

mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS job_market_db"

# Run the app
streamlit run app.py


> First run: Tables are created automatically and 25 sample job listings are seeded.

---

## For Job Seekers

1. Click **"Seeker Access"** on the start screen
2. Register (select "Seeker") or log in
3. Browse jobs and filter by company, city, or skill
4. Select a job and click **Apply** — fill in your details
5. Go to **My Applications** to track status
6. View your profile in the **Profile** section

---

## For Employers

1. Click **"Employer Access"** on the start screen
2. Register (select "Employer") or log in
3. **Add jobs** via the form on the left
4. **Edit/Delete** by selecting a row in the data table
5. Search jobs using Company, City, and Skill filters
6. Go to **Applications Tray** to review, approve, or reject applications
7. Export all jobs as CSV or import jobs in bulk via CSV upload

---

## Data Management

### CSV Export Format
ID,Title,Company,City,Salary,Skill

### CSV Import Format
Title,Company,City,Salary,Skill (header row required, min 5 columns)

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| MySQL connection error | Ensure MySQL is running and credentials in .env are correct |
| Streamlit not found | Run pip install -r requirements.txt |
| CSV import fails | Ensure CSV has a header row and 5+ data columns |
| Email already registered | Use a different email or log in |

---

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Frontend | Streamlit |
| Database | MySQL |
| Charts | Matplotlib, Pandas |
| Language | Python 3.9+ |
