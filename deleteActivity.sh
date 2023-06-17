
if [ "$1" = "" ]; then
  echo "Usage: $0 <wid>"
  exit
fi
wid=$1
echo "wid=$1"
updateDate=$(date -d "1 days ago" +%Y-%m-%d)
echo updateDate=$updateDate
PGPASSWORD=g3OCMXtsgTKRIrxAztAumHA8V2GCgDJV psql -v workoutid=$wid -v updateDate=$updateDate -h dpg-ch1fcrceoogo6oihajeg-a.oregon-postgres.render.com -U fli mystrava  << FF
select label, workout_id, distance, start_date from strava2_activity where wid=:'workoutid' order by start_date;
delete from strava2_distance where workout_id=:'workoutid';
delete from strava2_lap where workout_id=:'workoutid';
delete from strava2_heartrate where workout_id=:'workoutid';
delete from strava2_elevation where workout_id=:'workoutid';
delete from strava2_gpscoord where workout_id=:'workoutid';
delete from strava2_speed where workout_id=:'workoutid';
delete from strava2_split where workout_id=:'workoutid';
delete from strava2_workout where id=:'workoutid';
delete from strava2_activity where workout_id=:'workoutid';
update strava2_login set "lastUpdate"=:'updateDate' where id=1;
FF