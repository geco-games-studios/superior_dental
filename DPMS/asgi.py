import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import DPMS.routing  # Replace with your app's routing module

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'DPMS.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(
            DPMS.routing.websocket_urlpatterns  # Replace with your app's websocket routes
        )
    ),
})