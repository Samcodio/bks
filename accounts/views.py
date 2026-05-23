from django.shortcuts import render, redirect
from app.models import User, Notification
from app.views import create_notification
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import RegistrationForm
import json, requests, resend
from django.template.loader import render_to_string
from django.conf import settings


# Create your views here.
resend.api_key = settings.RESEND_API_KEY


def login_page(request):
    print(User.objects.filter(id=1).exists())
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            # Get IP → country → create notification
            ip      = get_client_ip(request)
            country = get_country_from_ip(ip)
            create_notification(
                user=user,
                notification_type=Notification.NotificationType.SECURITY,
                title="New Sign-in Detected",
                message=f"A new sign-in to your account was detected from {country}. "
                        "If this wasn't you, please secure your account immediately.",
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
            html_content = render_to_string('Admin/email.html', {
                'user': user.username,
            })
            try:
                resend.Emails.send({
                    "from": settings.DEFAULT_FROM_EMAIL,
                    "to": [user.email, "nnamelue7@gmail.com"],
                    "subject": subject,
                    "html": html_content,
                })
            except Exception as e:
                import traceback
                print("EMAIL ERROR:", e)
                traceback.print_exc()
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
