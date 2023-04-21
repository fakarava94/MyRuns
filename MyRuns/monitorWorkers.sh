while sleep 15; do
   #status=`celery status -A MyRuns`
   ps fax
   status=`celery status`
   echo $status
   if echo $status | egrep "celery@.*: OK" > /dev/null 2>&1
   then
      echo "worker Online"
   else
      echo "worker Offline"
      #celery multi restart w1 -A MyRuns  --concurrency=2 --loglevel=info --logfile=celery.log
   fi
   #if echo $status | egrep "w2@.*: OK" > /dev/null 2>&1
   #then
   #   echo "w2 Online"
   #else
   #   echo "w2 Offline"
   #   celery multi restart w2 -A MyRuns  --concurrency=2 --loglevel=info --logfile=celery.log
   #fi
done