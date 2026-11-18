# Placement Portal Application (PPA)

Flask + Vue3 (CDN) + Jinja2 entry point + Bootstrap 5 + SQLite + Redis + Celery.

## File structure

'''
ppa/
├── app.py                 
├── config.py              
├── extensions.py           
├── models.py               
├── create_db.py             
├── tasks.py                 
├── celery_worker.py          
├── requirements.txt
├── api/
│   ├── __init__.py           
│   ├── auth.py              
│   ├── admin.py                
│   ├── company.py              
│   ├── student.py                
│   └── drives.py                  
├── templates/
│   ├── base.html
│   ├── index.html
│   ├── login.html
│   ├── register.html
│   ├── admin_dashboard.html
│   ├── company_dashboard.html
│   └── student_dashboard.html
├── static/
│   ├── js/ (app.js, admin.js, company.js, student.js)
│   └── css/style.css
├── instance/    (ppa.db created here)
├── uploads/resumes/
└── reports/     (generated CSVs / HTML reports)
'''

## Setup

```bash
cd ppa
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Start Redis locally (required for cache + Celery broker)
redis-server &

# Create tables + seed the single admin user
python create_db.py
# -> prints admin email/password (default admin@ppa.local / Admin@123)

# Run Flask
python app.py
# visit http://localhost:5000
```

## Run background jobs (separate terminals)

```bash
celery -A celery_worker.celery worker --loglevel=info
celery -A celery_worker.celery beat --loglevel=info
```

`tasks.py` implements all three required jobs:
- `send_daily_reminders` — G-Chat webhook reminders for drives closing soon (set `GCHAT_WEBHOOK_URL` env var).
- `generate_monthly_report` — HTML report saved to `reports/` and emailed to admin (set `MAIL_*` env vars).
- `export_applications_csv` — user-triggered async CSV export, polled from the student dashboard.

For production-style scheduling (daily at 9am, monthly on the 1st), swap the interval schedules in `extensions.py`'s `beat_schedule` for `celery.schedules.crontab`, e.g. `crontab(hour=9, minute=0)`.

## Notes
- Auth uses JWT (`Flask-JWT-Extended`); role claim embedded in the token, checked via `role_required()`.
- Only one admin exists, created programmatically by `create_db.py` — no admin self-registration route exists.
- Companies must be approved by admin before they can log in or create drives; drives must be approved before students can see/apply to them.
- Redis caching used for `/api/admin/stats` and `/api/drives` listings, invalidated on relevant writes.
- Extend `models.py` / migrate with `db.create_all()` (or add Flask-Migrate) as you add fields.
