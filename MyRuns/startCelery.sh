celery --app MyRuns  worker --loglevel=DEBUG --concurrency=2 --without-mingle --detach
gunicorn app:app
