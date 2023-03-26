from __future__ import absolute_import, unicode_literals
import os
from celery import Celery

# set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'MyRuns.settings')

app = Celery('MyRuns',
             broker=os.getenv("CELERY_BROKER_URL"),
             backend='redis://red-cgetk8pmbg568r47cnl0:6379')

print ('>>> Celery app=",app)


# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object('django.conf:settings', namespace='CELERY')
print ('>>> app.config_from_object done")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()
print ('>>> app.autodiscover_tasks done")


@app.task(bind=True)
def debug_task(self):
        print('Request: {0!r}'.format(self.request))

