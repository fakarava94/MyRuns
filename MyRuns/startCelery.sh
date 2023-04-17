celery --app MyRuns  worker --loglevel=DEBUG --concurrency=2 --without-mingle &
gunicorn app:app
