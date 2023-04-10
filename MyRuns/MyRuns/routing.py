from django.urls import path
from channels.http import AsgiHandler
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator
from strava2.consumers import Consumers
from django.core.asgi import get_asgi_application

django_asgi_app = get_asgi_application()
 
application = ProtocolTypeRouter({

    # Channels will do this for you automatically. It's included here as an example.
    # "http": AsgiHandler,
    # Django's ASGI application to handle traditional HTTP requests
    "http": django_asgi_app,

    # Route all WebSocket requests to our custom chat handler.
    # We actually don't need the URLRouter here, but we've put it in for
    # illustration. Also note the inclusion of the AuthMiddlewareStack to
    # add users and sessions - see http://channels.readthedocs.io/en/latest/topics/authentication.html
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
                URLRouter([
                # URLRouter just takes standard Django path() or url() entries.
                path("strava2/stream/", Consumers),
                ])
        )
    ),

})