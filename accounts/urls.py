from .views import *
from django.urls import path

app_name = 'accounts'

urlpatterns = [
    path('login/', login_page, name='login'),
    path('signUp/', signUp, name='signUp')
]