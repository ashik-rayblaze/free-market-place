from django.contrib import admin
from .models import Category, Project, ProjectAttachment, ProjectMilestone


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    """Category admin interface."""
    
    list_display = ('name', 'icon', 'created_at')
    search_fields = ('name', 'description')
    ordering = ('name',)


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Project admin interface."""
    
    list_display = ('title', 'employer', 'category', 'budget_type', 'budget_min', 'budget_max', 'status', 'is_featured', 'created_at')
    list_filter = ('status', 'budget_type', 'category', 'is_featured', 'created_at')
    search_fields = ('title', 'description', 'employer__email', 'employer__first_name', 'employer__last_name')
    readonly_fields = ('views_count', 'bids_count', 'created_at', 'updated_at')
    ordering = ('-created_at',)
    
    fieldsets = (
        ('Basic Info', {
            'fields': ('title', 'description', 'category', 'employer')
        }),
        ('Budget & Timeline', {
            'fields': ('budget_type', 'budget_min', 'budget_max', 'deadline')
        }),
        ('Requirements', {
            'fields': ('skills_required', 'experience_level')
        }),
        ('Status & Stats', {
            'fields': ('status', 'is_featured', 'views_count', 'bids_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ProjectAttachment)
class ProjectAttachmentAdmin(admin.ModelAdmin):
    """Project attachment admin interface."""
    
    list_display = ('project', 'filename', 'file_size', 'uploaded_at')
    list_filter = ('uploaded_at',)
    search_fields = ('project__title', 'filename')
    ordering = ('-uploaded_at',)


@admin.register(ProjectMilestone)
class ProjectMilestoneAdmin(admin.ModelAdmin):
    """Project milestone admin interface."""
    
    list_display = ('project', 'title', 'amount', 'due_date', 'is_completed', 'created_at')
    list_filter = ('is_completed', 'created_at', 'due_date')
    search_fields = ('project__title', 'title', 'description')
    ordering = ('-created_at',)

