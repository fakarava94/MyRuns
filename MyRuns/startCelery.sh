celery multi start w1 w2 -A MyRuns  --concurrency=4 --loglevel=info --detach --logfile=celery.log
tail -f celery.log &
./monitorWorkers.sh &
gunicorn app:app
