from django import template
from ..models import Conversation

register = template.Library()

@register.simple_tag
def get_unread_message_count(user):
    """Get the total number of unread messages for a user."""
    if not user.is_authenticated:
        return 0
    
    conversations = Conversation.objects.filter(
        participants=user,
        is_active=True
    )
    
    total_unread = 0
    for conversation in conversations:
        unread_count = conversation.messages.filter(
            is_read=False
        ).exclude(sender=user).count()
        total_unread += unread_count
    
    return total_unread
