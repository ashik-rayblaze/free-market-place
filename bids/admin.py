from django.contrib import admin
from .models import Bid, BidAttachment, BidMessage


@admin.register(Bid)
class BidAdmin(admin.ModelAdmin):
    """Bid admin interface."""
    
    list_display = ('freelancer', 'project', 'amount', 'delivery_time', 'status', 'is_featured', 'created_at')
    list_filter = ('status', 'is_featured', 'created_at')
    search_fields = ('freelancer__email', 'freelancer__first_name', 'freelancer__last_name', 'project__title', 'proposal')
    readonly_fields = ('created_at', 'updated_at', 'accepted_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('project', 'freelancer', 'amount', 'delivery_time', 'proposal')
        }),
        ('Status', {
            'fields': ('status', 'is_featured')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'accepted_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(BidAttachment)
class BidAttachmentAdmin(admin.ModelAdmin):
    """Bid attachment admin interface."""
    
    list_display = ('bid', 'filename', 'file_size', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('bid__project__title', 'filename')
    ordering = ('-uploaded_at',)


@admin.register(BidMessage)
class BidMessageAdmin(admin.ModelAdmin):
    """Bid message admin interface."""
    
    list_display = ('bid', 'sender', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('bid__project__title', 'sender__email', 'message')
    ordering = ('-created_at',)

