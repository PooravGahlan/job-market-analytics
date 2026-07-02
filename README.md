# ⬡ Job Market Analytics System

A Streamlit-powered analytics dashboard for job market data — manage job listings, track applications, and visualize hiring trends.

## Features

- 🔐 **Role-based auth** — Job Seekers & Employers
- 📋 **Job CRUD** — Post, edit, delete listings with skill/city filters
- 📝 **Application pipeline** — Apply, approve, reject with status tracking
- 📊 **Analytics dashboard** — Salary distributions, top skills, city trends
- 📂 **CSV import/export** — Bulk upload/download job data
- 🎨 **Space-themed UI** — Dark mode, glowing accents

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | [Streamlit](https://streamlit.io) |
| Database | MySQL 8+ |
| Charts | Matplotlib |
| Backend | Python 3.9+ |

## Quick Start

### Prerequisites
- Python 3.9+
- MySQL 8+ running locally

### Setup

```bash
# 1. Clone the repo
git clone https://github.com/your-username/job-market-analytics.git
cd job-market-analytics

# 2. Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Install dependencies
pip install -r requirements.txt

# 4. Configure environment
cp .env.example .env
# Edit .env with your MySQL credentials

# 5. Create the database
mysql -u root -p -e "CREATE DATABASE IF NOT EXISTS job_market_db"

# 6. Run the app
streamlit run app.py
