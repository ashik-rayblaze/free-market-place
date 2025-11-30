from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from .models import User, Profile, Skill
from projects.models import Project, Category
from bids.models import Bid
from payments.models import Wallet, Transaction, PaymentMethod, Escrow
from messaging.models import Conversation, Message
from reports.models import Report, Notification, ActivityLog
from pages.models import StaticPage


def is_admin(user):
    """Check if user is admin or staff."""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    """Admin dashboard with statistics."""
    from django.utils import timezone
    from django.conf import settings
    
    total_users = User.objects.count()
    total_projects = Project.objects.count()
    total_bids = Bid.objects.count()
    pending_reports = Report.objects.filter(status='pending').count()
    total_transactions = Transaction.objects.count()
    total_wallets = Wallet.objects.count()
    total_pages = StaticPage.objects.count()
    published_pages = StaticPage.objects.filter(status='published').count()
    
    # Get recent activity
    recent_projects = Project.objects.order_by('-created_at')[:5]
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_reports = Report.objects.filter(status='pending').order_by('-created_at')[:5]
    recent_pages = StaticPage.objects.order_by('-created_at')[:5]
    
    # Statistics by role
    freelancers = User.objects.filter(role='freelancer').count()
    employers = User.objects.filter(role='employer').count()
    admins = User.objects.filter(is_staff=True).count()
    
    context = {
        'total_users': total_users,
        'total_projects': total_projects,
        'total_bids': total_bids,
        'pending_reports': pending_reports,
        'total_transactions': total_transactions,
        'total_wallets': total_wallets,
        'total_pages': total_pages,
        'published_pages': published_pages,
        'freelancers': freelancers,
        'employers': employers,
        'admins': admins,
        'recent_projects': recent_projects,
        'recent_users': recent_users,
        'recent_reports': recent_reports,
        'recent_pages': recent_pages,
        'debug': settings.DEBUG,
        'now': timezone.now(),
    }
    return render(request, 'accounts/admin_dashboard.html', context)


@login_required
@user_passes_test(is_admin)
def admin_user_list(request):
    """List all users."""
    users = User.objects.all().order_by('-date_joined')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        users = users.filter(
            Q(email__icontains=search_query) |
            Q(username__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    
    # Filter by role
    role_filter = request.GET.get('role', '')
    if role_filter:
        users = users.filter(role=role_filter)
    
    # Pagination
    paginator = Paginator(users, 20)
    page_number = request.GET.get('page')
    users = paginator.get_page(page_number)
    
    context = {
        'users': users,
        'search_query': search_query,
        'role_filter': role_filter,
    }
    return render(request, 'admin/users/list.html', context)


@login_required
@user_passes_test(is_admin)
def admin_user_detail(request, pk):
    """View user details."""
    user = get_object_or_404(User, pk=pk)
    profile, created = Profile.objects.get_or_create(user=user)
    projects = Project.objects.filter(employer=user)
    bids = Bid.objects.filter(freelancer=user)
    
    context = {
        'user': user,
        'profile': profile,
        'projects': projects,
        'bids': bids,
    }
    return render(request, 'admin/users/detail.html', context)


@login_required
@user_passes_test(is_admin)
def admin_project_list(request):
    """List all projects."""
    projects = Project.objects.all().order_by('-created_at')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        projects = projects.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        projects = projects.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(projects, 20)
    page_number = request.GET.get('page')
    projects = paginator.get_page(page_number)
    
    context = {
        'projects': projects,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'admin/projects/list.html', context)


@login_required
@user_passes_test(is_admin)
def admin_bid_list(request):
    """List all bids."""
    bids = Bid.objects.all().order_by('-created_at')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        bids = bids.filter(
            Q(proposal__icontains=search_query) |
            Q(project__title__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        bids = bids.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(bids, 20)
    page_number = request.GET.get('page')
    bids = paginator.get_page(page_number)
    
    context = {
        'bids': bids,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'admin/bids/list.html', context)


@login_required
@user_passes_test(is_admin)
def admin_transaction_list(request):
    """List all transactions."""
    transactions = Transaction.objects.all().order_by('-created_at')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        transactions = transactions.filter(
            Q(user__email__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(external_transaction_id__icontains=search_query)
        )
    
    # Filter by type
    type_filter = request.GET.get('type', '')
    if type_filter:
        transactions = transactions.filter(transaction_type=type_filter)
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        transactions = transactions.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)
    
    context = {
        'transactions': transactions,
        'search_query': search_query,
        'type_filter': type_filter,
        'status_filter': status_filter,
    }
    return render(request, 'admin/transactions/list.html', context)


@login_required
@user_passes_test(is_admin)
def admin_report_list(request):
    """List all reports."""
    reports = Report.objects.all().order_by('-created_at')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        reports = reports.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        reports = reports.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(reports, 20)
    page_number = request.GET.get('page')
    reports = paginator.get_page(page_number)
    
    context = {
        'reports': reports,
        'search_query': search_query,
        'status_filter': status_filter,
    }
    return render(request, 'admin/reports/list.html', context)


@login_required
@user_passes_test(is_admin)
def admin_wallet_list(request):
    """List all wallets."""
    wallets = Wallet.objects.all().order_by('-created_at')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        wallets = wallets.filter(
            Q(user__email__icontains=search_query) |
            Q(user__first_name__icontains=search_query) |
            Q(user__last_name__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(wallets, 20)
    page_number = request.GET.get('page')
    wallets = paginator.get_page(page_number)
    
    context = {
        'wallets': wallets,
        'search_query': search_query,
    }
    return render(request, 'admin/wallets/list.html', context)


@login_required
@user_passes_test(is_admin)
def admin_category_list(request):
    """List all categories."""
    categories = Category.objects.all().order_by('name')
    
    context = {
        'categories': categories,
    }
    return render(request, 'admin/categories/list.html', context)

