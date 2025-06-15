from django.urls import re_path
from app import consumers

websocket_urlpatterns = [
    re_path(r'ws/room/(?P<room_id>\w+)/$', consumers.RoomConsumer.as_asgi()),
]