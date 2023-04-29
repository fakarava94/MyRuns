#celery multi start w1 -A MyRuns -c 4 -f $PWD/celery.log -p $PWD/%n.pid
#celery multi start w2 -A MyRuns -c 4 -f $PWD/celery.log -p $PWD/%n.pid

celery -A MyRuns beat --logfile=./sched.out --detach
celery --app MyRuns  worker --loglevel=DEBUG --concurrency=2 -E &
gunicorn app:app --timeout 300
