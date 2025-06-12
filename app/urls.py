from django.urls import path
from . import views

urlpatterns = [
    path('room/create/', views.create_room, name='create_room'),
    path('room/select/', views.select_room, name='select_room'),
    path('room/<int:room_id>/', views.room_detail, name='room_detail'),
]