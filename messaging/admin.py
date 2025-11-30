from django.contrib import admin
from .models import Conversation, Message, MessageAttachment


@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    """Conversation admin interface."""
    
    list_display = ('__str__', 'project', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('participants__email', 'participants__first_name', 'participants__last_name', 'project__title', 'subject')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-updated_at',)
    
    filter_horizontal = ('participants',)


@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    """Message admin interface."""
    
    list_display = ('conversation', 'sender', 'is_read', 'created_at')
    list_filter = ('is_read', 'created_at')
    search_fields = ('conversation__participants__email', 'sender__email', 'content')
    readonly_fields = ('created_at', 'read_at')
    ordering = ('-created_at',)


@admin.register(MessageAttachment)
class MessageAttachmentAdmin(admin.ModelAdmin):
    """Message attachment admin interface."""
    
    list_display = ('message', 'filename', 'file_size', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('message__conversation__participants__email', 'filename')
    ordering = ('-uploaded_at',)

