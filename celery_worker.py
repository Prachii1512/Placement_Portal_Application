"""
Start the Celery worker:
    celery -A celery_worker.celery worker --loglevel=info --pool=solo

Start Celery beat (scheduler for the daily/monthly jobs) in a separate terminal:
    celery -A celery_worker.celery beat --loglevel=info
"""
from tasks import celery
