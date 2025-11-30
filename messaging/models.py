from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Conversation(models.Model):
    """Conversation between two users."""
    
    participants = models.ManyToManyField(User, related_name='conversations')
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='conversations', null=True, blank=True)
    subject = models.CharField(max_length=200, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-updated_at']
    
    def __str__(self):
        if self.project:
            return f"Conversation about {self.project.title}"
        return f"Conversation between {', '.join([p.full_name for p in self.participants.all()])}"
    
    def get_other_participant(self, user):
        """Get the other participant in the conversation."""
        return self.participants.exclude(id=user.id).first()
    
    def get_latest_message(self):
        """Get the latest message in the conversation."""
        return self.messages.order_by('-created_at').first()
    
    @property
    def last_message(self):
        """Get the latest message in the conversation (property for templates)."""
        return self.get_latest_message()


class Message(models.Model):
    """Individual message in a conversation."""
    
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_messages')
    content = models.TextField()
    is_read = models.BooleanField(default=False)
    read_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.full_name} - {self.conversation}"
    
    def mark_as_read(self):
        """Mark message as read."""
        if not self.is_read:
            self.is_read = True
            self.read_at = timezone.now()
            self.save()


class MessageAttachment(models.Model):
    """File attachments for messages."""
    
    message = models.ForeignKey(Message, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='message_attachments/')
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.message} - {self.filename}"

