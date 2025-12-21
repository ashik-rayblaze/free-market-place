from django.db import models
from django.db.models import Sum
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
    
    def get_total_phases_amount(self):
        """Get total amount allocated to all phases."""
        from django.db.models import Sum
        return self.phases.aggregate(total=Sum('amount'))['total'] or 0
    
    def get_paid_phases_amount(self):
        """Get total amount paid for completed phases."""
        from django.db.models import Sum
        return self.phases.filter(status='paid').aggregate(total=Sum('amount'))['total'] or 0
    
    def get_completed_phases_count(self):
        """Get count of completed phases."""
        return self.phases.filter(status__in=['completed', 'paid']).count()
    
    def can_add_phase_amount(self, amount, exclude_phase=None):
        """Check if adding a phase amount would exceed budget."""
        current_total = self.get_total_phases_amount()
        if exclude_phase:
            current_total -= exclude_phase.amount
        return (current_total + amount) <= self.budget_max


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


class ProjectPhase(models.Model):
    """Project phases/stages with payment integration."""
    
    PHASE_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('paid', 'Paid'),
        ('cancelled', 'Cancelled'),
    ]
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='phases')
    name = models.CharField(max_length=200, help_text="Phase name (e.g., 'Design Phase', 'Development Phase')")
    description = models.TextField(help_text="Detailed description of what this phase entails")
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)], help_text="Amount to be paid for this phase")
    status = models.CharField(max_length=20, choices=PHASE_STATUS_CHOICES, default='pending')
    order = models.PositiveIntegerField(default=0, help_text="Order of phase execution (1, 2, 3...)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    paid_at = models.DateTimeField(null=True, blank=True)
    
    # Payment request tracking
    payment_requested = models.BooleanField(default=False)
    payment_requested_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['order', 'created_at']
        verbose_name = "Project Phase"
        verbose_name_plural = "Project Phases"
    
    def __str__(self):
        return f"{self.project.title} - {self.name} (${self.amount})"
    
    def can_start(self):
        """Check if this phase can be started."""
        if self.status != 'pending':
            return False
        # Check if previous phases are completed
        previous_phases = ProjectPhase.objects.filter(
            project=self.project,
            order__lt=self.order
        ).exclude(status__in=['completed', 'paid'])
        return not previous_phases.exists()
    
    def start(self):
        """Start the phase."""
        if self.can_start():
            self.status = 'in_progress'
            self.started_at = timezone.now()
            self.save()
            return True
        return False
    
    def mark_completed(self):
        """Mark phase as completed."""
        if self.status == 'in_progress':
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.save()
            return True
        return False
    
    def request_payment(self):
        """Request payment for this phase (freelancer action)."""
        if self.status == 'completed' and not self.payment_requested:
            self.payment_requested = True
            self.payment_requested_at = timezone.now()
            self.save()
            return True
        return False
    
    def can_be_paid(self):
        """Check if phase can be paid."""
        return self.status == 'completed' and self.payment_requested
    
    def get_total_phases_amount(self):
        """Get total amount for all phases in this project."""
        return ProjectPhase.objects.filter(project=self.project).aggregate(
            total=Sum('amount')
        )['total'] or 0

