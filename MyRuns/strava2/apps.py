from django.apps import AppConfig

class Strava2Config(AppConfig):
    name = 'strava2'
    run_already = False

    def ready(self):
        if not self.run_already:
            print (' Application is READY !!!')
            self.run_already = True
