PGPASSWORD=iqNFrdrffHXrcceCkDunnK1yfkyIaOOL psql -h dpg-ch1fcrceoogo6oihajeg-a.oregon-postgres.render.com -U fli myruns_en73 << FF
select label, workout_id, distance, start_date from strava2_activity where uid=38251837 order by start_date;
FF