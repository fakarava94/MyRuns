#celery multi start w1 -A MyRuns -c 4 -f $PWD/celery.log -p $PWD/%n.pid
#celery multi start w2 -A MyRuns -c 4 -f $PWD/celery.log -p $PWD/%n.pid
celery --app MyRuns  worker --loglevel=DEBUG --concurrency=2 -E --detach
./monitorWorkers.sh &
# -F ./celery.log &
gunicorn app:app
