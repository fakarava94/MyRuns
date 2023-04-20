celery multi start w1 w2 --app MyRuns --concurrency=4 --loglevel=info --logfile=./celery.log --pidfile=$PWD/%n.pid
./monitorWorkers.sh &
tail -F ./celery.log &
gunicorn app:app
