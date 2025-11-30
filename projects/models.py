from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone

User = get_user_model()


class Category(models.Model):
    """Project categories."""
    
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Font Awesome icon class")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['name']


class Project(models.Model):
    """Project model for employers to post jobs."""
    
    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    BUDGET_TYPE_CHOICES = [
        ('fixed', 'Fixed Price'),
        ('hourly', 'Hourly Rate'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='projects')
    employer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_projects')
    
    # Budget and timeline
    budget_type = models.CharField(max_length=10, choices=BUDGET_TYPE_CHOICES, default='fixed')
    budget_min = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    budget_max = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    deadline = models.DateTimeField()
    
    # Project details
    skills_required = models.TextField(help_text="Comma-separated list of required skills")
    experience_level = models.CharField(max_length=20, choices=[
        ('entry', 'Entry Level'),
        ('intermediate', 'Intermediate'),
        ('expert', 'Expert'),
    ], default='intermediate')
    
    # Status and metadata
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    is_featured = models.BooleanField(default=False)
    views_count = models.PositiveIntegerField(default=0)
    bids_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
    
    def get_skills_required_list(self):
        """Return required skills as a list."""
        if self.skills_required:
            return [skill.strip() for skill in self.skills_required.split(',')]
        return []
    
    def is_deadline_passed(self):
        """Check if project deadline has passed."""
        return timezone.now() > self.deadline
    
    def can_accept_bids(self):
        """Check if project can still accept bids."""
        return self.status == 'open' and not self.is_deadline_passed()
    
    def increment_views(self):
        """Increment view count."""
        self.views_count += 1
        self.save(update_fields=['views_count'])
    
    def increment_bids(self):
        """Increment bid count."""
        self.bids_count += 1
        self.save(update_fields=['bids_count'])
    
    def decrement_bids(self):
        """Decrement bid count."""
        self.bids_count = max(0, self.bids_count - 1)
        self.save(update_fields=['bids_count'])


class ProjectAttachment(models.Model):
    """File attachments for projects."""
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='attachments')
    file = models.FileField(upload_to='project_attachments/')
    filename = models.CharField(max_length=255)
    file_size = models.PositiveIntegerField()
    uploaded_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.project.title} - {self.filename}"


class ProjectMilestone(models.Model):
    """Project milestones for tracking progress."""
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='milestones')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    due_date = models.DateTimeField()
    is_completed = models.BooleanField(default=False)
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.project.title} - {self.title}"
    
    def mark_completed(self):
        """Mark milestone as completed."""
        self.is_completed = True
        self.completed_at = timezone.now()
        self.save()

