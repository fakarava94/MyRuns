celery --app MyRuns worker --loglevel info --concurrency 4 --detach
gunicorn app:app