from django.contrib import admin
from .models import Report, ReportAttachment, ActivityLog, Notification


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    """Report admin interface."""
    
    list_display = ('title', 'reporter', 'reported_user', 'report_type', 'status', 'assigned_to', 'created_at')
    list_filter = ('report_type', 'status', 'created_at')
    search_fields = ('title', 'description', 'reporter__email', 'reported_user__email')
    readonly_fields = ('created_at', 'updated_at', 'resolved_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Report Info', {
            'fields': ('reporter', 'reported_user', 'project', 'bid', 'report_type', 'title', 'description')
        }),
        ('Status & Assignment', {
            'fields': ('status', 'assigned_to', 'admin_notes', 'resolution')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'resolved_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ReportAttachment)
class ReportAttachmentAdmin(admin.ModelAdmin):
    """Report attachment admin interface."""
    
    list_display = ('report', 'filename', 'file_size', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('report__title', 'filename')
    ordering = ('-uploaded_at',)


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    """Activity log admin interface."""
    
    list_display = ('user', 'action', 'ip_address', 'created_at')
    list_filter = ('action', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'description')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Notification admin interface."""
    
    list_display = ('user', 'notification_type', 'title', 'is_read', 'created_at')
    list_filter = ('notification_type', 'is_read', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'title', 'message')
    readonly_fields = ('created_at', 'read_at')
    ordering = ('-created_at',)

