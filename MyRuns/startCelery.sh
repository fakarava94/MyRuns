celery --app MyRuns  worker --loglevel=DEBUG --concurrency=2 &
gunicorn app:app
