from django.urls import path
from . import views

app_name='payments'


urlpatterns = [
    path('initiate/',  views.initiate_deposit,    name='initiate_deposit'),
    path('verify/',    views.verify_deposit,       name='verify_deposit'),
    path('webhook/',   views.flutterwave_webhook,  name='flutterwave_webhook'),
# payments/urls.py
    path('deposit/redirect/', views.deposit_redirect, name='deposit_redirect'),
]