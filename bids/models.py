from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone

User = get_user_model()


class Bid(models.Model):
    """Bid model for freelancers to bid on projects."""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='bids')
    freelancer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bids')
    
    # Bid details
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    delivery_time = models.PositiveIntegerField(help_text="Delivery time in days")
    proposal = models.TextField()
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    is_featured = models.BooleanField(default=False)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    accepted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['project', 'freelancer']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.freelancer.full_name} - {self.project.title} (${self.amount})"
    
    def accept(self):
        """Accept the bid."""
        self.status = 'accepted'
        self.accepted_at = timezone.now()
        self.save()
        
        # Update project status
        self.project.status = 'in_progress'
        self.project.save()
    
    def reject(self):
        """Reject the bid."""
        self.status = 'rejected'
        self.save()
    
    def withdraw(self):
        """Withdraw the bid."""
        self.status = 'withdrawn'
        self.save()
    
    def can_be_modified(self):
        """Check if bid can still be modified."""
        return self.status == 'pending' and self.project.can_accept_bids()


class BidAttachment(models.Model):
    """File attachments for bids."""
    
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='bid_attachments/')
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.bid} - {self.filename}"


class BidMessage(models.Model):
    """Messages between employer and freelancer regarding a bid."""
    
    bid = models.ForeignKey(Bid, on_delete=models.CASCADE, related_name='messages')
    sender = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['created_at']
    
    def __str__(self):
        return f"{self.sender.full_name} - {self.bid.project.title}"

