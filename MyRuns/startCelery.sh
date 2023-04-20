celery multi start w1 w2 -A MyRuns  --concurrency=4 --loglevel=info --detach --logfile=./celery.log --pidfile=./%n.pid
./monitorWorkers.sh &
tail -F ./celery.log &
gunicorn app:app
