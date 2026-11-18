import os
import csv
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta

import requests

from app import create_app
from extensions import make_celery, db
from models import Drive, Application, StudentProfile, CompanyProfile

flask_app = create_app()
celery = make_celery(flask_app)


def _send_gchat(message: str):
    webhook = flask_app.config.get("GCHAT_WEBHOOK_URL")
    if not webhook:
        print(f"[GCHAT] (no webhook configured) {message}")
        return
    try:
        requests.post(webhook, json={"text": message}, timeout=10)
    except Exception as exc:
        print(f"[GCHAT] send failed: {exc}")


def _send_email(to_addr: str, subject: str, html_body: str):
    cfg = flask_app.config
    if not cfg.get("MAIL_USERNAME") or not to_addr:
        print(f"[MAIL] (not configured) To: {to_addr} | Subject: {subject}")
        return
    msg = MIMEMultipart("alternative")
    msg["Subject"] = subject
    msg["From"] = cfg["MAIL_SENDER"] or cfg["MAIL_USERNAME"]
    msg["To"] = to_addr
    msg.attach(MIMEText(html_body, "html"))
    try:
        with smtplib.SMTP(cfg["MAIL_SERVER"], cfg["MAIL_PORT"]) as server:
            server.starttls()
            server.login(cfg["MAIL_USERNAME"], cfg["MAIL_PASSWORD"])
            server.sendmail(msg["From"], [to_addr], msg.as_string())
    except Exception as exc:
        print(f"[MAIL] send failed: {exc}")


@celery.task(name="tasks.send_daily_reminders")
def send_daily_reminders():
    with flask_app.app_context():
        soon = datetime.utcnow() + timedelta(days=2)
        upcoming = Drive.query.filter(
            Drive.status == "approved",
            Drive.application_deadline <= soon,
            Drive.application_deadline >= datetime.utcnow(),
        ).all()

        if not upcoming:
            _send_gchat("PPA Reminder: No drives closing in the next 2 days.")
            return "no upcoming drives"

        applied_drive_ids_by_student = {}
        for app_row in Application.query.all():
            applied_drive_ids_by_student.setdefault(app_row.student_id, set()).add(app_row.drive_id)

        notified = 0
        for student in StudentProfile.query.filter_by(is_blacklisted=False).all():
            already_applied = applied_drive_ids_by_student.get(student.id, set())
            relevant = [d for d in upcoming if d.id not in already_applied]
            if not relevant:
                continue
            titles = ", ".join(f"{d.job_title} ({d.company.company_name})" for d in relevant)
            message = f"Reminder for {student.name}: deadlines approaching for {titles}"
            _send_gchat(message)
            notified += 1

        return f"Reminders sent for {notified} students, {len(upcoming)} drives"


@celery.task(name="tasks.generate_monthly_report")
def generate_monthly_report(): 
    with flask_app.app_context():
        from models import User

        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)

        drives_this_month = Drive.query.filter(Drive.created_at >= month_start).count()
        apps_this_month = Application.query.filter(Application.application_date >= month_start).count()
        selected_this_month = Application.query.filter(
            Application.application_date >= month_start, Application.status == "selected"
        ).count()
        total_students = StudentProfile.query.count()
        total_companies = CompanyProfile.query.count()

        html = f"""
        <html><body style="font-family:Arial,sans-serif;">
        <h2>PPA Monthly Placement Activity Report — {now.strftime('%B %Y')}</h2>
        <table border="1" cellpadding="8" cellspacing="0" style="border-collapse:collapse;">
          <tr><td><b>Drives conducted this month</b></td><td>{drives_this_month}</td></tr>
          <tr><td><b>Applications submitted this month</b></td><td>{apps_this_month}</td></tr>
          <tr><td><b>Students selected this month</b></td><td>{selected_this_month}</td></tr>
          <tr><td><b>Total registered students</b></td><td>{total_students}</td></tr>
          <tr><td><b>Total registered companies</b></td><td>{total_companies}</td></tr>
        </table>
        </body></html>
        """

        report_path = os.path.join(
            flask_app.config["REPORTS_FOLDER"], f"monthly_report_{now.strftime('%Y_%m')}.html"
        )
        with open(report_path, "w") as f:
            f.write(html)

        admin = User.query.filter_by(role="admin").first()
        if admin:
            _send_email(admin.email, f"PPA Monthly Report — {now.strftime('%B %Y')}", html)

        return report_path


@celery.task(name="tasks.export_applications_csv")
def export_applications_csv(student_id: int):
    """(c) User-triggered async job — export a student's application history as CSV."""
    with flask_app.app_context():
        student = StudentProfile.query.get(student_id)
        if not student:
            raise ValueError("Student not found")

        applications = Application.query.filter_by(student_id=student_id).all()
        filename = f"applications_student_{student_id}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.csv"
        filepath = os.path.join(flask_app.config["REPORTS_FOLDER"], filename)

        with open(filepath, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Student ID", "Company Name", "Drive Title", "Application Status", "Application Date"])
            for a in applications:
                writer.writerow([
                    student_id,
                    a.drive.company.company_name if a.drive and a.drive.company else "",
                    a.drive.job_title if a.drive else "",
                    a.status,
                    a.application_date.isoformat() if a.application_date else "",
                ])

        _send_gchat(f"Your application export is ready: {filename}")
        return filename
