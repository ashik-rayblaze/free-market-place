from django.contrib import admin
from .models import PaymentMethod, Wallet, Transaction, Escrow


@admin.register(PaymentMethod)
class PaymentMethodAdmin(admin.ModelAdmin):
    """Payment method admin interface."""
    
    list_display = ('user', 'payment_type', 'card_brand', 'card_last_four', 'is_default', 'is_active', 'created_at')
    list_filter = ('payment_type', 'is_default', 'is_active', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'external_id')
    ordering = ('-created_at',)


@admin.register(Wallet)
class WalletAdmin(admin.ModelAdmin):
    """Wallet admin interface."""
    
    list_display = ('user', 'balance', 'is_active', 'created_at', 'updated_at')
    list_filter = ('is_active', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name')
    readonly_fields = ('created_at', 'updated_at')
    ordering = ('-created_at',)


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Transaction admin interface."""
    
    list_display = ('id', 'user', 'transaction_type', 'amount', 'status', 'project', 'created_at')
    list_filter = ('transaction_type', 'status', 'created_at')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'external_transaction_id', 'description')
    readonly_fields = ('id', 'created_at', 'completed_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('id', 'user', 'transaction_type', 'amount', 'status')
        }),
        ('Related Objects', {
            'fields': ('project', 'bid', 'payment_method'),
            'classes': ('collapse',)
        }),
        ('Payment Details', {
            'fields': ('description', 'external_transaction_id', 'processing_fee'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'completed_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Escrow)
class EscrowAdmin(admin.ModelAdmin):
    """Escrow admin interface."""
    
    list_display = ('project', 'employer', 'freelancer', 'amount', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('project__title', 'employer__email', 'freelancer__email')
    readonly_fields = ('created_at', 'released_at')
    ordering = ('-created_at',)

