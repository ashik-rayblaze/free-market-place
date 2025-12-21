from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.core.paginator import Paginator
from django.db.models import Q, Count
from .models import User, Profile
from projects.models import Project
from bids.models import Bid
from payments.models import Wallet, Transaction
from reports.models import Notification


def admin_redirect(request):
    """Redirect admin URLs to appropriate pages."""
    if request.user.is_authenticated:
        if request.user.is_superuser or request.user.is_staff:
            return redirect('accounts:admin_dashboard')
        else:
            return redirect('accounts:dashboard')
    else:
        return redirect('accounts:login')


def home(request):
    """Home page with featured projects and statistics."""
    featured_projects = Project.objects.filter(is_featured=True, status='open')[:6]
    recent_projects = Project.objects.filter(status='open').order_by('-created_at')[:6]
    
    # Statistics
    total_projects = Project.objects.filter(status='open').count()
    total_freelancers = User.objects.filter(role='freelancer', is_active=True).count()
    total_employers = User.objects.filter(role='employer', is_active=True).count()
    
    context = {
        'featured_projects': featured_projects,
        'recent_projects': recent_projects,
        'total_projects': total_projects,
        'total_freelancers': total_freelancers,
        'total_employers': total_employers,
    }
    return render(request, 'accounts/home.html', context)


def login_view(request):
    """User login view."""
    if request.user.is_authenticated:
        # Redirect admin users to admin dashboard
        if request.user.is_staff or request.user.is_superuser:
            return redirect('accounts:admin_dashboard')
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        
        user = authenticate(request, username=email, password=password)
        if user is not None:
            login(request, user)
            messages.success(request, f'Welcome back, {user.first_name}!')
            # Redirect admin users to admin dashboard
            if user.is_staff or user.is_superuser:
                return redirect('accounts:admin_dashboard')
            return redirect('accounts:dashboard')
        else:
            messages.error(request, 'Invalid email or password.')
    
    return render(request, 'accounts/login.html')


def logout_view(request):
    """User logout view."""
    logout(request)
    messages.info(request, 'You have been logged out successfully.')
    return redirect('accounts:home')


def register(request):
    """User registration view."""
    if request.user.is_authenticated:
        return redirect('accounts:dashboard')
    
    if request.method == 'POST':
        first_name = request.POST.get('first_name')
        last_name = request.POST.get('last_name')
        email = request.POST.get('email')
        username = request.POST.get('username')
        password = request.POST.get('password')
        confirm_password = request.POST.get('confirm_password')
        role = request.POST.get('role', 'freelancer')
        
        # Validation
        if password != confirm_password:
            messages.error(request, 'Passwords do not match.')
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
            return render(request, 'accounts/register.html')
        
        if User.objects.filter(username=username).exists():
            messages.error(request, 'Username already exists.')
            return render(request, 'accounts/register.html')
        
        # Create user
        with transaction.atomic():
            user = User.objects.create_user(
                username=username,
                email=email,
                first_name=first_name,
                last_name=last_name,
                password=password,
                role=role
            )
            
            # Create profile
            Profile.objects.create(user=user)
            
            # Wallet is automatically created by signal in payments.signals
        
        messages.success(request, 'Account created successfully! Please log in.')
        return redirect('accounts:login')
    
    return render(request, 'accounts/register.html')


@login_required
def dashboard(request):
    """User dashboard based on role."""
    user = request.user
    
    if user.role == 'freelancer':
        # Freelancer dashboard
        my_bids = Bid.objects.filter(freelancer=user).order_by('-created_at')[:5]
        available_projects = Project.objects.filter(status='open').order_by('-created_at')[:5]
        recent_notifications = Notification.objects.filter(user=user).order_by('-created_at')[:5]
        
        context = {
            'my_bids': my_bids,
            'available_projects': available_projects,
            'recent_notifications': recent_notifications,
        }
        return render(request, 'accounts/freelancer_dashboard.html', context)
    
    elif user.role == 'employer':
        # Employer dashboard
        my_projects = Project.objects.filter(employer=user).order_by('-created_at')[:5]
        recent_bids = Bid.objects.filter(project__employer=user).order_by('-created_at')[:5]
        recent_notifications = Notification.objects.filter(user=user).order_by('-created_at')[:5]
        
        context = {
            'my_projects': my_projects,
            'recent_bids': recent_bids,
            'recent_notifications': recent_notifications,
        }
        return render(request, 'accounts/employer_dashboard.html', context)
    
    else:
        # Admin/Staff dashboard - redirect to admin dashboard
        return redirect('accounts:admin_dashboard')


@login_required
def profile_view(request):
    """View user profile."""
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    # Get user's projects and bids based on role
    if request.user.role == 'freelancer':
        projects = Project.objects.filter(bids__freelancer=request.user).distinct()
        bids = Bid.objects.filter(freelancer=request.user)
    else:
        projects = Project.objects.filter(employer=request.user)
        bids = Bid.objects.filter(project__employer=request.user)
    
    context = {
        'profile': profile,
        'projects': projects[:5],
        'bids': bids[:5],
    }
    return render(request, 'accounts/profile.html', context)


@login_required
def profile_edit(request):
    """Edit user profile."""
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        # Update profile fields
        profile.bio = request.POST.get('bio', '')
        profile.phone = request.POST.get('phone', '')
        profile.location = request.POST.get('location', '')
        profile.website = request.POST.get('website', '')
        
        if request.user.role == 'freelancer':
            profile.hourly_rate = request.POST.get('hourly_rate') or None
            profile.skills = request.POST.get('skills', '')
            profile.experience_years = request.POST.get('experience_years') or None
            profile.portfolio_url = request.POST.get('portfolio_url', '')
        else:
            profile.company_name = request.POST.get('company_name', '')
            profile.company_size = request.POST.get('company_size', '')
        
        # Handle avatar upload
        if 'avatar' in request.FILES:
            profile.avatar = request.FILES['avatar']
        
        profile.save()
        
        # Update user basic info
        request.user.first_name = request.POST.get('first_name', '')
        request.user.last_name = request.POST.get('last_name', '')
        request.user.save()
        
        messages.success(request, 'Profile updated successfully!')
        return redirect('accounts:profile')
    
    context = {
        'profile': profile,
    }
    return render(request, 'accounts/profile_edit.html', context)


@login_required
def user_profile_view(request, user_id):
    """View another user's profile."""
    user = get_object_or_404(User, id=user_id)
    profile = get_object_or_404(Profile, user=user)
    
    # Get user's projects and bids based on role
    if user.role == 'freelancer':
        projects = Project.objects.filter(bids__freelancer=user).distinct()
        bids = Bid.objects.filter(freelancer=user)
    else:
        projects = Project.objects.filter(employer=user)
        bids = Bid.objects.filter(project__employer=user)
    
    context = {
        'profile_user': user,
        'profile': profile,
        'projects': projects,
        'bids': bids,
    }
    return render(request, 'accounts/user_profile.html', context)

