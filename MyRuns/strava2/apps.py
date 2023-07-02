from django.apps import AppConfig
import re, logging, redis, os

log = logging.getLogger(__name__)

class Strava2Config(AppConfig):
    name = 'strava2'
    run_already = False

    def ready(self):

        if not self.run_already:
            print (' Application is READY !!!')
            self.run_already = True
            REDIS_URL = os.environ.get('CELERY_BROKER_URL', '')
            r = redis.from_url (REDIS_URL)
            initDone = r.get ('INIT')
            if initDone is not None:
                r.set ('INIT', '0')
            else:
                r.set ('INIT', '0')

