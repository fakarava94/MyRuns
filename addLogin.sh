PGPASSWORD=gbhZHcZAsYeU3iuw17HfFQ1haOtmbQWq psql -h dpg-cnhldbi1hbls73cufio0-a.oregon-postgres.render.com -U fli mystrava_rd1l << FF
insert into strava2_login (id, name, url, "clientID", "clientSecret", "callbackURL", "dateLogin", "userName", "lastUpdate", "forceUpdateDateTo") VALUES (1,'strava', 'https://www.strava.com/oauth/authorize', 25021, 'a62c3867e77f9c9deaa2b3d72136ae7936ecb8cf', 'https://django-srv.onrender.com/strava2/callback', '2019-05-12', 'Fli', '2024-01-01 20:00:00+00', '2024-01-01 20:00:00+00');
FF

