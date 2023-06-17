PGPASSWORD=g3OCMXtsgTKRIrxAztAumHA8V2GCgDJV psql -h dpg-ci6rhpenqql0ldcmbnp0-a.oregon-postgres.render.com -U fli mystrava << FF
select label, workout_id, distance, start_date from strava2_activity where uid=5202057 order by start_date;
FF