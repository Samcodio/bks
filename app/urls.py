from .views import *
from django.urls import path

app_name = 'app'

urlpatterns = [
    path('dashboard/', dashboard, name='dashboard'),
    path('settings/', setting, name='settings'),
    path('transactions/', makeTransfer, name='transfer'),
    path('history/', history, name='history'),
    path('cards/', cards, name='cards'),
    path('products/', products, name='products'),
    path('loans/', loans, name='loans'),
    path('verifiedOrNot/', verifiedOrNot, name='verifiedOrNot'),
    path('notifications/', notificationList, name='notifications'),
    path('deposit/', deposit, name='deposit'),
    path('success/', success, name='success'),
    path('failed/', failed, name='failed'),
    path('custom_pin/', addPin, name='addPin'),
    path('users/', userList, name='users'),
    path('clients/<int:user_id>/ban/',    ban_user,    name='ban_user'),
    path('clients/<int:user_id>/unban/',  unban_user,  name='unban_user'),
    path('clients/<int:user_id>/delete/', delete_user, name='delete_user'),
    path('clients/<int:id>/balance/', changeBalance, name='change_balance'),

]