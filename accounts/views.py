from django.shortcuts import render, redirect
from app.models import User
from django.contrib.auth import login, logout, authenticate
from django.contrib import messages
from .forms import RegistrationForm
import json


# Create your views here.


def login_page(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')

        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
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
            form.save()
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
