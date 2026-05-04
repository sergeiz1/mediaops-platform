.\.venv\Scripts\celery.exe -A app.workers.celery_app:celery_app worker --loglevel=info --pool=solo
