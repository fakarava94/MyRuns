from django.apps import AppConfig
import re, logging

log = logging.getLogger(__name__)

class Strava2Config(AppConfig):
    name = 'strava2'
    run_already = False

    def ready(self):

        if not self.run_already:
            print (' Application is READY !!!')
            self.run_already = True

