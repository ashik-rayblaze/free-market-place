from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.http import JsonResponse
from django.utils import timezone
from .models import Report, ReportAttachment, ActivityLog, Notification
from projects.models import Project
from bids.models import Bid


@login_required
def report_list(request):
    """List user's reports."""
    if request.user.role in ['admin', 'staff']:
        reports = Report.objects.all().order_by('-created_at')
    else:
        reports = Report.objects.filter(reporter=request.user).order_by('-created_at')
    
    # Filtering
    status = request.GET.get('status')
    report_type = request.GET.get('type')
    
    if status:
        reports = reports.filter(status=status)
    
    if report_type:
        reports = reports.filter(report_type=report_type)
    
    # Pagination
    paginator = Paginator(reports, 10)
    page_number = request.GET.get('page')
    reports = paginator.get_page(page_number)
    
    context = {
        'reports': reports,
        'status_choices': Report.STATUS_CHOICES,
        'report_types': Report.REPORT_TYPE_CHOICES,
        'selected_status': status,
        'selected_type': report_type,
    }
    return render(request, 'reports/report_list.html', context)


@login_required
def report_create(request):
    """Create a new report."""
    if request.method == 'POST':
        report_type = request.POST.get('report_type')
        title = request.POST.get('title')
        description = request.POST.get('description')
        reported_user_id = request.POST.get('reported_user')
        project_id = request.POST.get('project')
        bid_id = request.POST.get('bid')
        
        # Validation
        if not all([report_type, title, description]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'reports/report_create.html')
        
        try:
            report = Report.objects.create(
                reporter=request.user,
                report_type=report_type,
                title=title,
                description=description,
            )
            
            # Add related objects if provided
            if reported_user_id:
                from accounts.models import User
                report.reported_user = get_object_or_404(User, pk=reported_user_id)
            
            if project_id:
                report.project = get_object_or_404(Project, pk=project_id)
            
            if bid_id:
                report.bid = get_object_or_404(Bid, pk=bid_id)
            
            report.save()
            
            messages.success(request, 'Report submitted successfully!')
            return redirect('reports:detail', pk=report.pk)
        except Exception as e:
            messages.error(request, f'Error creating report: {str(e)}')
    
    context = {
        'report_types': Report.REPORT_TYPE_CHOICES,
    }
    return render(request, 'reports/report_create.html', context)


def report_detail(request, pk):
    """View report details."""
    report = get_object_or_404(Report, pk=pk)
    
    # Check permissions
    if request.user != report.reporter and request.user.role not in ['admin', 'staff']:
        messages.error(request, 'You do not have permission to view this report.')
        return redirect('reports:list')
    
    context = {
        'report': report,
    }
    return render(request, 'reports/report_detail.html', context)


@login_required
def notification_list(request):
    """List user's notifications."""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Filtering
    notification_type = request.GET.get('type')
    is_read = request.GET.get('is_read')
    
    if notification_type:
        notifications = notifications.filter(notification_type=notification_type)
    
    if is_read is not None:
        notifications = notifications.filter(is_read=is_read == 'true')
    
    # Pagination
    paginator = Paginator(notifications, 20)
    page_number = request.GET.get('page')
    notifications = paginator.get_page(page_number)
    
    context = {
        'notifications': notifications,
        'notification_types': Notification.NOTIFICATION_TYPE_CHOICES,
        'selected_type': notification_type,
        'selected_read': is_read,
    }
    return render(request, 'reports/notification_list.html', context)


@login_required
def mark_notification_read(request, pk):
    """Mark a notification as read."""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    
    if request.method == 'POST':
        notification.mark_as_read()
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})


@login_required
def mark_all_notifications_read(request):
    """Mark all notifications as read."""
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})

