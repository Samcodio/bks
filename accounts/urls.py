from django.urls import path
from .views import (
    login_page, logout_button, signUp,
    ForgotPasswordView, ForgotPasswordDoneView,
    ResetPasswordConfirmView, ResetPasswordCompleteView,
)

app_name = 'accounts'

urlpatterns = [
    path('login/', login_page, name='login'),
    path('logout/', logout_button, name='logout'),
    path('signUp/', signUp, name='signUp'),

    # Password reset flow (built-in views)
    path('password-reset/',
         ForgotPasswordView.as_view(), name='password_reset'),
    path('password-reset/done/',
         ForgotPasswordDoneView.as_view(), name='password_reset_done'),
    path('password-reset/<uidb64>/<token>/',
         ResetPasswordConfirmView.as_view(), name='password_reset_confirm'),
    path('password-reset/complete/',
         ResetPasswordCompleteView.as_view(), name='password_reset_complete'),
]