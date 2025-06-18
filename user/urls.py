from django.urls import path
from . import views

from django.urls import path
from django.contrib.auth import views as auth_views



urlpatterns = [
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),  # ← 이게 있어야 함
]