PGPASSWORD=92PpHb5Hfm6xKsuQ4daSZYQMfIkOjULJ psql -h dpg-ckgniuuafg7c73dvuv40-a.oregon-postgres.render.com -U fli mystravauksj << FF
select label, workout_id, distance, start_date from strava2_activity where uid=38251837 order by start_date;
FF
