from django.urls import path
from . import views

app_name = 'weather'

urlpatterns = [
    path('', views.get_weather, name='get_weather'),
    path('history/', views.get_history, name='get_history'),
    path('health/', views.health_check, name='health_check'),
] 