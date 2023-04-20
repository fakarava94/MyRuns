celery multi start w1 -A MyRuns -c 4 -f $PWD/celery.log -p $PWD/%n.pid
celery multi start w2 -A MyRuns -c 4 -f $PWD/celery.log -p $PWD/%n.pid
./monitorWorkers.sh &
tail -F ./celery.log &
gunicorn app:app
