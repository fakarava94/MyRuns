celery multi start w1 w2 --app MyRuns --concurrency=4 --loglevel=info --logfile=./celery.log
./monitorWorkers.sh &
tail -F ./celery.log &
gunicorn app:app
