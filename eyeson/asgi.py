import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eyeson.settings')
import django
django.setup()

from django.core.asgi import get_asgi_application
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import eyeson.routing

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            eyeson.routing.websocket_urlpatterns
        )
    ),
})