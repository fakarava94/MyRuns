import os
#from channels.asgi import get_channel_layer
#from channels.layers import get_channel_layer
from channels.routing import get_default_application
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MyRuns.settings")
#channel_layer = get_channel_layer()
#application = get_asgi_application()

django.setup()
application = get_default_application()