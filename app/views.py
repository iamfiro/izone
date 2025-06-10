from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login
from django.contrib.auth.models import User

# Create your views here.
def index(request):
    return render(request, 'index.html')

def login(request):
    return render(request, 'login.html')

def signup(request):
    return render(request, 'signup.html')

def login_process(request):
    email = request.POST.get('email')
    password = request.POST.get('password')

    user = authenticate(request, email=email, password=password)

    if user is not None:
        login(request, user)
        return redirect('index')
    else:
        return redirect('login')
    
def signup_process(request):
    email = request.POST.get('email')
    username = request.POST.get('username')
    password = request.POST.get('password')

    user = User.objects.create_user(email=email, username=username, password=password)
    user.save()

    return redirect('login')