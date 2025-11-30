from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Profile, Skill


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Custom User admin interface."""
    
    list_display = ('email', 'username', 'first_name', 'last_name', 'role', 'is_verified', 'is_active', 'date_joined')
    list_filter = ('role', 'is_verified', 'is_active', 'is_staff', 'is_superuser', 'date_joined')
    search_fields = ('email', 'username', 'first_name', 'last_name')
    ordering = ('-date_joined',)
    
    fieldsets = BaseUserAdmin.fieldsets + (
        ('Additional Info', {'fields': ('role', 'is_verified')}),
    )
    
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        ('Additional Info', {'fields': ('role', 'is_verified')}),
    )


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    """Profile admin interface."""
    
    list_display = ('user', 'location', 'hourly_rate', 'average_rating', 'is_active', 'created_at')
    list_filter = ('is_active', 'created_at', 'location')
    search_fields = ('user__email', 'user__first_name', 'user__last_name', 'bio', 'skills')
    readonly_fields = ('average_rating', 'total_ratings', 'created_at', 'updated_at')
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('user', 'bio', 'phone', 'location', 'website', 'avatar')
        }),
        ('Freelancer Info', {
            'fields': ('hourly_rate', 'skills', 'experience_years', 'portfolio_url'),
            'classes': ('collapse',)
        }),
        ('Employer Info', {
            'fields': ('company_name', 'company_size'),
            'classes': ('collapse',)
        }),
        ('Rating', {
            'fields': ('average_rating', 'total_ratings'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active', 'created_at', 'updated_at')
        }),
    )


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    """Skill admin interface."""
    
    list_display = ('name', 'category', 'created_at')
    list_filter = ('category', 'created_at')
    search_fields = ('name', 'category')
    ordering = ('name',)

