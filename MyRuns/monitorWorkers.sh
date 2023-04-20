while sleep 15; do
   status=`celery status -A MyRuns`
   echo $status
   if echo $status | egrep "w1@.*: OK" > /dev/null 2>&1
   then
      echo "w1 Online"
   else
      echo "w1 Offline"
      celery multi restart w1 -A MyRuns  --concurrency=2 --loglevel=info --logfile=celery.log
   fi
   if echo $status | egrep "w2@.*: OK" > /dev/null 2>&1
   then
      echo "w2 Online"
   else
      echo "w2 Offline"
      celery multi restart w2 -A MyRuns  --concurrency=2 --loglevel=info --logfile=celery.log
   fi
done