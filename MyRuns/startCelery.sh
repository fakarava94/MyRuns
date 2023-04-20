celery multi start w1 w2 -A MyRuns -c 4 -f ./celery.log -p PWD/%n.pid
./monitorWorkers.sh &
tail -F ./celery.log &
gunicorn app:app
