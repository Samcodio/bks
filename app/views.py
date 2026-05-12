from django.shortcuts import render, redirect, get_object_or_404
from .models import *
from django.contrib.auth.decorators import login_required

# Create your views here.


@login_required(login_url='accounts:login')
def dashboard(request):
    user = request.user
    context = {
        'user': user
    }
    return render(request, 'User/dashboard.html', context)
