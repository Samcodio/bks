from django.shortcuts import render, redirect, get_object_or_404
from app.models import User, Notification
from app.views import create_notification, _send_login_alert
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import RegistrationForm
import json, requests, resend
from django.template.loader import render_to_string
from django.conf import settings
import logging
logger = logging.getLogger(__name__)
from django.contrib.auth.views import (
    PasswordResetView,
    PasswordResetConfirmView,
    PasswordResetDoneView,
    PasswordResetCompleteView,
)
from django.urls import reverse_lazy
from .forms import CustomPasswordResetForm, CustomSetPasswordForm
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode
from django.core.mail import EmailMultiAlternatives  # not strictly needed

# Create your views here.
resend.api_key = settings.RESEND_API_KEY


def login_page(request):
    print(User.objects.filter(id=1).exists())
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        useracc = get_object_or_404(User, username=username)
        email = useracc.email
        print(email)
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Get IP → country → create notification
            ip      = get_client_ip(request)
            country = get_country_from_ip(ip)
            # create_notification(
            #     user=user,
            #     notification_type=Notification.NotificationType.SECURITY,
            #     title="New Sign-in Detected",
            #     message=f"A new sign-in to your account was detected from {country}. "
            #             "If this wasn't you, please secure your account immediately.",
            # )
            print(f'{user}')
            _send_login_alert(

                user=user,
                ip=ip,
                country=country,
                user_agent=request.META.get('HTTP_USER_AGENT', 'Unknown device'),
                email=email
            )
            messages.success(request, 'Login Successful')
            return redirect('app:dashboard')
        else:
            messages.warning(request, 'Invalid login details')
    context = {}
    return render(request, 'Auth/login.html', context)


def logout_button(request):
    logout(request)
    return redirect('accounts:login')


def signUp(request):
    form = RegistrationForm()
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            # Send email
            subject = 'Account Created'
            try:

                html_content = render_to_string('Admin/email.html', {
                    'user': user.username,
                    'user_account_num': user.account.account_genID,
                    'name': user.full_name,
                    'date': user.date_joined
                })
                resend.Emails.send({
                    "from": settings.DEFAULT_FROM_EMAIL,
                    "to": user.email,
                    "subject": subject,
                    "html": html_content,
                })
            except Exception as e:
                logger.exception("EMAIL ERROR: %s", e)
            messages.success(request, 'Account successfully created')
            return redirect('accounts:login')
        else:
            # Loop through errors and push them into messages
            for field, errors in form.errors.items():
                for error in errors:
                    if field == '__all__':
                        # Non-field error
                        messages.warning(request, error)
                    else:
                        messages.warning(
                            request,
                            f"{field.capitalize()}: {error}",
                        )

    context = {
        'form': form,
    }
    return render(request, 'Auth/signUp.html', context)


def get_client_ip(request) -> str:
    """Extract the real client IP from a Django request."""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")

    if x_forwarded_for:
        # Can be a comma-separated list — first one is the real client IP
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR")

    return ip

def get_country_from_ip(ip: str) -> str:
    """Returns the country name from an IP address, or 'Unknown Location' as fallback."""
    print(f"ip {ip}")
    try:
        # Skip private/local IPs
        res = requests.get(f"https://ipapi.co/{ip}/json/", timeout=5)
        data = res.json()

        if data.get("error"):
            return "Unknown Location"

        return data.get("country_name", "Unknown Location")
    except requests.RequestException:
        return "Unknown Location"



class ForgotPasswordView(PasswordResetView):
    """Step 1: request reset link by email — sends via Resend SDK."""
    template_name = 'Auth/forgot_password.html'
    form_class = CustomPasswordResetForm
    email_template_name = 'Auth/password_reset_email.txt'
    html_email_template_name = 'Auth/password_reset_email.html'
    subject_template_name = 'Auth/password_reset_subject.txt'
    success_url = reverse_lazy('accounts:password_reset_done')
    from_email = settings.DEFAULT_FROM_EMAIL

    def form_valid(self, form):
        email = form.cleaned_data["email"]
        for user in form.get_users(email):
            context = {
                'email': user.email,
                'domain': self.request.get_host(),
                'site_name': 'First National',
                'uid': urlsafe_base64_encode(force_bytes(user.pk)),
                'user': user,
                'token': self.token_generator.make_token(user),
                'protocol': 'https' if self.request.is_secure() else 'http',
            }

            subject = render_to_string(
                self.subject_template_name, context
            ).strip().replace('\n', ' ')
            text_body = render_to_string(self.email_template_name, context)
            html_body = render_to_string(self.html_email_template_name, context)

            try:
                resend.Emails.send({
                    "from": self.from_email,
                    "to": user.email,
                    "subject": subject,
                    "text": text_body,
                    "html": html_body,
                })
            except Exception as e:
                logger.exception("PASSWORD RESET EMAIL ERROR: %s", e)

        return super().form_valid(form)


class ForgotPasswordDoneView(PasswordResetDoneView):
    """Step 2: 'check your email' confirmation page."""
    template_name = 'Auth/password_reset_done.html'


class ResetPasswordConfirmView(PasswordResetConfirmView):
    """Step 3: set new password (validates uidb64 + token)."""
    template_name = 'Auth/reset_password.html'
    form_class = CustomSetPasswordForm
    success_url = reverse_lazy('accounts:password_reset_complete')
    post_reset_login = False    # require user to sign in manually


class ResetPasswordCompleteView(PasswordResetCompleteView):
    """Step 4: success page."""
    template_name = 'Auth/password_reset_complete.html'
