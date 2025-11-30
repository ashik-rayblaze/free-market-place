from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Report(models.Model):
    """Reports for disputes and flagged content."""
    
    REPORT_TYPE_CHOICES = [
        ('inappropriate_content', 'Inappropriate Content'),
        ('spam', 'Spam'),
        ('fraud', 'Fraud'),
        ('harassment', 'Harassment'),
        ('payment_dispute', 'Payment Dispute'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('under_review', 'Under Review'),
        ('resolved', 'Resolved'),
        ('dismissed', 'Dismissed'),
    ]
    
    reporter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_made')
    reported_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reports_received', null=True, blank=True)
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    bid = models.ForeignKey('bids.Bid', on_delete=models.CASCADE, related_name='reports', null=True, blank=True)
    
    report_type = models.CharField(max_length=30, choices=REPORT_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Admin handling
    assigned_to = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_reports')
    admin_notes = models.TextField(blank=True)
    resolution = models.TextField(blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    resolved_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Report: {self.title} - {self.get_status_display()}"
    
    def assign_to_staff(self, staff_member):
        """Assign report to staff member."""
        self.assigned_to = staff_member
        self.status = 'under_review'
        self.save()
    
    def resolve(self, resolution_text, staff_member):
        """Resolve the report."""
        self.status = 'resolved'
        self.resolution = resolution_text
        self.assigned_to = staff_member
        self.resolved_at = timezone.now()
        self.save()
    
    def dismiss(self, staff_member):
        """Dismiss the report."""
        self.status = 'dismissed'
        self.assigned_to = staff_member
        self.resolved_at = timezone.now()
        self.save()


class ReportAttachment(models.Model):
    """File attachments for reports."""
    
    report = models.ForeignKey(Report, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='report_attachments/')
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.report.title} - {self.filename}"


class ActivityLog(models.Model):
    """Activity logs for monitoring user actions."""
    
    ACTION_CHOICES = [
        ('login', 'User Login'),
        ('logout', 'User Logout'),
        ('project_created', 'Project Created'),
        ('project_updated', 'Project Updated'),
        ('bid_placed', 'Bid Placed'),
        ('bid_accepted', 'Bid Accepted'),
        ('payment_made', 'Payment Made'),
        ('message_sent', 'Message Sent'),
        ('report_submitted', 'Report Submitted'),
        ('profile_updated', 'Profile Updated'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='activity_logs')
    action = models.CharField(max_length=30, choices=ACTION_CHOICES)
    description = models.TextField()
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.full_name} - {self.get_action_display()}"


class Notification(models.Model):
    """User notifications."""
    
    NOTIFICATION_TYPE_CHOICES = [
        ('bid_received', 'New Bid Received'),
        ('bid_accepted', 'Bid Accepted'),
        ('bid_rejected', 'Bid Rejected'),
        ('payment_received', 'Payment Received'),
        ('project_completed', 'Project Completed'),
        ('message_received', 'New Message'),
        ('report_status', 'Report Status Update'),
        ('system', 'System Notification'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    notification_type = models.CharField(max_length=30, choices=NOTIFICATION_TYPE_CHOICES)
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    
    # Related objects
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    bid = models.ForeignKey('bids.Bid', on_delete=models.CASCADE, null=True, blank=True, related_name='notifications')
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.full_name} - {self.title}"
    
    def mark_as_read(self):
        """Mark notification as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()

