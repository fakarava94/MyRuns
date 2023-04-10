import os
#from channels.asgi import get_channel_layer
from channels.layers import get_channel_layer
from django.core.asgi import get_asgi_application
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "MyRuns.settings")
channel_layer = get_channel_layer()
application = get_asgi_application()