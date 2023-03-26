celery --app MyRuns  worker --loglevel=DEBUG --concurrency=4 &
gunicorn app:app