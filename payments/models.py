from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator
from django.utils import timezone
from decimal import Decimal
import uuid

User = get_user_model()


class PaymentMethod(models.Model):
    """Payment methods for users."""
    
    PAYMENT_TYPE_CHOICES = [
        ('credit_card', 'Credit Card'),
        ('debit_card', 'Debit Card'),
        ('bank_transfer', 'Bank Transfer'),
        ('paypal', 'PayPal'),
        ('stripe', 'Stripe'),
    ]
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='payment_methods')
    payment_type = models.CharField(max_length=20, choices=PAYMENT_TYPE_CHOICES)
    is_default = models.BooleanField(default=False)
    
    # For card payments
    card_last_four = models.CharField(max_length=4, blank=True)
    card_brand = models.CharField(max_length=20, blank=True)
    expiry_month = models.PositiveIntegerField(null=True, blank=True)
    expiry_year = models.PositiveIntegerField(null=True, blank=True)
    
    # For bank transfers
    bank_name = models.CharField(max_length=100, blank=True)
    account_number = models.CharField(max_length=50, blank=True)
    routing_number = models.CharField(max_length=20, blank=True)
    
    # External payment provider data
    external_id = models.CharField(max_length=255, blank=True)
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        if self.card_last_four:
            return f"{self.card_brand} ****{self.card_last_four}"
        return f"{self.get_payment_type_display()} - {self.user.full_name}"


class Wallet(models.Model):
    """User wallet for managing funds."""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='wallet')
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, validators=[MinValueValidator(0)])
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.full_name}'s Wallet (${self.balance})"
    
    def add_funds(self, amount):
        """Add funds to wallet."""
        # Convert amount to Decimal to ensure type compatibility
        amount = Decimal(str(amount))
        self.balance += amount
        self.save()
    
    def deduct_funds(self, amount):
        """Deduct funds from wallet."""
        # Convert amount to Decimal to ensure type compatibility
        amount = Decimal(str(amount))
        if self.balance >= amount:
            self.balance -= amount
            self.save()
            return True
        return False


class Transaction(models.Model):
    """Transaction records for all payments."""
    
    TRANSACTION_TYPE_CHOICES = [
        ('deposit', 'Deposit'),
        ('withdrawal', 'Withdrawal'),
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('commission', 'Commission'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='transactions')
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    
    # Related objects
    project = models.ForeignKey('projects.Project', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    phase = models.ForeignKey('projects.ProjectPhase', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    bid = models.ForeignKey('bids.Bid', on_delete=models.SET_NULL, null=True, blank=True, related_name='transactions')
    payment_method = models.ForeignKey(PaymentMethod, on_delete=models.SET_NULL, null=True, blank=True)
    
    # Payment details
    description = models.TextField(blank=True)
    external_transaction_id = models.CharField(max_length=255, blank=True)
    processing_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - ${self.amount} - {self.user.full_name}"
    
    def mark_completed(self):
        """Mark transaction as completed."""
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.save()
    
    def mark_failed(self):
        """Mark transaction as failed."""
        self.status = 'failed'
        self.save()


class Escrow(models.Model):
    """Escrow system for holding funds during project completion."""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('released', 'Released'),
        ('disputed', 'Disputed'),
        ('refunded', 'Refunded'),
    ]
    
    project = models.OneToOneField('projects.Project', on_delete=models.CASCADE, related_name='escrow')
    employer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='escrow_as_employer')
    freelancer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='escrow_as_freelancer')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Escrow for {self.project.title} - ${self.amount}"
    
    def release_funds(self):
        """Release funds to freelancer."""
        if self.status == 'active':
            self.status = 'released'
            self.released_at = timezone.now()
            self.save()
            
            # Add funds to freelancer's wallet
            freelancer_wallet, created = Wallet.objects.get_or_create(user=self.freelancer)
            freelancer_wallet.add_funds(self.amount)
            
            # Create transaction record
            Transaction.objects.create(
                user=self.freelancer,
                transaction_type='payment',
                amount=self.amount,
                status='completed',
                project=self.project,
                description=f"Payment for project: {self.project.title}",
                completed_at=timezone.now()
            )
    
    def refund_funds(self):
        """Refund funds to employer."""
        if self.status == 'active':
            self.status = 'refunded'
            self.save()
            
            # Add funds back to employer's wallet
            employer_wallet, created = Wallet.objects.get_or_create(user=self.employer)
            employer_wallet.add_funds(self.amount)
            
            # Create transaction record
            Transaction.objects.create(
                user=self.employer,
                transaction_type='refund',
                amount=self.amount,
                status='completed',
                project=self.project,
                description=f"Refund for project: {self.project.title}",
                completed_at=timezone.now()
            )


class PhaseEscrow(models.Model):
    """Escrow system for individual project phases."""
    
    STATUS_CHOICES = [
        ('active', 'Active'),
        ('released', 'Released'),
        ('disputed', 'Disputed'),
        ('refunded', 'Refunded'),
    ]
    
    phase = models.OneToOneField('projects.ProjectPhase', on_delete=models.CASCADE, related_name='escrow')
    project = models.ForeignKey('projects.Project', on_delete=models.CASCADE, related_name='phase_escrows')
    employer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phase_escrows_as_employer')
    freelancer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phase_escrows_as_freelancer')
    amount = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    released_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = "Phase Escrow"
        verbose_name_plural = "Phase Escrows"
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Escrow for {self.phase.name} - ${self.amount}"
    
    def release_funds(self):
        """Release phase funds to freelancer."""
        if self.status == 'active' and self.phase.can_be_paid():
            self.status = 'released'
            self.released_at = timezone.now()
            self.save()
            
            # Update phase status to paid
            self.phase.status = 'paid'
            self.phase.paid_at = timezone.now()
            self.phase.save()
            
            # Add funds to freelancer's wallet
            freelancer_wallet, created = Wallet.objects.get_or_create(user=self.freelancer)
            freelancer_wallet.add_funds(self.amount)
            
            # Create transaction record
            Transaction.objects.create(
                user=self.freelancer,
                transaction_type='payment',
                amount=self.amount,
                status='completed',
                project=self.project,
                phase=self.phase,
                description=f"Payment for phase: {self.phase.name} - {self.project.title}",
                completed_at=timezone.now()
            )
            return True
        return False
    
    def refund_funds(self):
        """Refund phase funds to employer."""
        if self.status == 'active':
            self.status = 'refunded'
            self.save()
            
            # Add funds back to employer's wallet
            employer_wallet, created = Wallet.objects.get_or_create(user=self.employer)
            employer_wallet.add_funds(self.amount)
            
            # Create transaction record
            Transaction.objects.create(
                user=self.employer,
                transaction_type='refund',
                amount=self.amount,
                status='completed',
                project=self.project,
                phase=self.phase,
                description=f"Refund for phase: {self.phase.name} - {self.project.title}",
                completed_at=timezone.now()
            )
            return True
        return False

