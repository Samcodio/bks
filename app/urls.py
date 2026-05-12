from .views import *
from django.urls import path

app_name = 'app'

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard')
]