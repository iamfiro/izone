from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login as auth_login
from django.contrib.auth.models import User
from .models import CustomUser

# Create your views here.
def index(request):
    return render(request, 'index.html')

def login(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        user = authenticate(request, email=email, password=password)
        if user is not None:
            auth_login(request, user)
            return redirect('index')
        else:
            return render(request, 'login.html', {'error': '이메일 또는 비밀번호가 올바르지 않습니다.'})
    return render(request, 'login.html')

def signup(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        password_confirm = request.POST.get('password_confirm')
        terms = request.POST.get('terms')
        
        if CustomUser.objects.filter(email=email).exists():
            return render(request, 'signup.html', {'error': '이미 존재하는 이메일입니다.'})
            
        user = CustomUser.objects.create_user(
            email=email,
            username=username,
            password=password
        )
        return redirect('login')
    return render(request, 'signup.html')

def login_process(request):
    email = request.POST.get('email')
    password = request.POST.get('password')

    user = authenticate(request, email=email, password=password)

    if user is not None:
        login(request, user)
        return redirect('index')
    else:
        return redirect('/login?error=1')
    
def signup_process(request):
    email = request.POST.get('email')
    username = request.POST.get('username')
    password = request.POST.get('password')

    user = User.objects.create_user(email=email, username=username, password=password)
    user.save()

    return redirect('login')