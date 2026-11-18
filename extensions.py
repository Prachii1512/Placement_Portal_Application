from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_caching import Cache
from celery import Celery
from celery.schedules import crontab

db = SQLAlchemy()
jwt = JWTManager()
cache = Cache()
celery = Celery(__name__)


def make_celery(app):
    celery.conf.update(
        broker_url=app.config["CELERY_BROKER_URL"],
        result_backend=app.config["CELERY_RESULT_BACKEND"],
    )
    celery.conf.beat_schedule = {
        "daily-deadline-reminders": {
            "task": "tasks.send_daily_reminders",
            "schedule": crontab(hour=8, minute=0),  # every day at 8:00 AM server time
        },
        "monthly-activity-report": {
            "task": "tasks.generate_monthly_report",
            "schedule": crontab(hour=8, minute=0, day_of_month=1),  # 1st of every month, 8:00 AM
        },
    }

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery