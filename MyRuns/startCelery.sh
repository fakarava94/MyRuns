celery --app MyRuns  worker --loglevel=DEBUG &
gunicorn app:app
