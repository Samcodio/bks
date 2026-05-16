from .views import *
from django.urls import path

app_name = 'accounts'

urlpatterns = [
    path('login/', login_page, name='login'),
    path('logout/', logout_button, name='logout'),
    path('signUp/', signUp, name='signUp')
]