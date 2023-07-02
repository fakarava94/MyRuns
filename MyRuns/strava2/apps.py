from django.apps import AppConfig
import re, logging

log = logging.getLogger(__name__)

class Strava2Config(AppConfig):
    name = 'strava2'
    run_already = False

    def ready(self):
        from stravalib import Client
        from strava2.models import Login, StravaUser
        from strava2.common import getRefreshedToken
        if not self.run_already:
            print (' Application is READY !!!')
            self.run_already = True

            login=Login.objects.filter(id=1)
            for user in StravaUser.objects.all():
                print(user)
                token = {}
                token['access_token'] = user.token
                token['refresh_token'] = user.refresh_token
                token['expires_at'] = user.token_expires_at
                refresh_token = getRefreshedToken(login[0].clientID, login[0].clientSecret, token)

                client = Client(refresh_token['access_token'])
                login=Login.objects.filter(id=1)
                subscribeUrl = re.sub('callback', 'subscribeCB',  login[0].callbackURL)  
                log.info ('subscribeUrl=%s',subscribeUrl)
                client.create_subscription(login[0].clientID, login[0].clientSecret, subscribeUrl, verify_token=u'STRAVA')
