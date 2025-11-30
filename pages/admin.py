from django.contrib import admin
from .models import StaticPage


@admin.register(StaticPage)
class StaticPageAdmin(admin.ModelAdmin):
    """Admin interface for static pages."""
    
    list_display = ('title', 'slug', 'page_type', 'status', 'is_featured', 'show_in_footer', 'show_in_nav', 'order', 'created_at', 'updated_at')
    list_filter = ('status', 'page_type', 'is_featured', 'show_in_footer', 'show_in_nav', 'created_at')
    search_fields = ('title', 'slug', 'content', 'meta_description')
    prepopulated_fields = {'slug': ('title',)}
    ordering = ('order', 'title')
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'page_type', 'content')
        }),
        ('SEO', {
            'fields': ('meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
        ('Display Options', {
            'fields': ('status', 'is_featured', 'show_in_footer', 'show_in_nav', 'order')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
        ('Authors', {
            'fields': ('created_by', 'updated_by'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'published_at')
    
    def save_model(self, request, obj, form, change):
        """Set created_by and updated_by automatically."""
        if not change:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)

