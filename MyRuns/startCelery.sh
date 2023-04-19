celery --app MyRuns  worker --loglevel=DEBUG --concurrency=2 --without-heartbeat --without-mingle  &
gunicorn app:app
