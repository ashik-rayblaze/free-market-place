from django.db import models
from django.utils import timezone
from django.urls import reverse


class StaticPage(models.Model):
    """Model for static pages like About, FAQ, Terms, etc."""
    
    PAGE_TYPES = [
        ('about', 'About Us'),
        ('faq', 'FAQ'),
        ('terms', 'Terms of Service'),
        ('privacy', 'Privacy Policy'),
        ('contact', 'Contact'),
        ('info', 'Information'),
        ('help', 'Help'),
        ('custom', 'Custom Page'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, help_text="URL-friendly version of the title (e.g., 'about-us')")
    page_type = models.CharField(max_length=20, choices=PAGE_TYPES, default='custom')
    content = models.TextField(help_text="HTML content is allowed")
    meta_description = models.CharField(max_length=255, blank=True, help_text="SEO meta description")
    meta_keywords = models.CharField(max_length=255, blank=True, help_text="SEO meta keywords (comma-separated)")
    
    # Status and visibility
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    is_featured = models.BooleanField(default=False, help_text="Show on homepage or navigation")
    show_in_footer = models.BooleanField(default=False, help_text="Show link in footer")
    show_in_nav = models.BooleanField(default=False, help_text="Show link in main navigation")
    
    # Ordering
    order = models.IntegerField(default=0, help_text="Order for display (lower numbers appear first)")
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)
    
    # Author
    created_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='created_pages')
    updated_by = models.ForeignKey('accounts.User', on_delete=models.SET_NULL, null=True, related_name='updated_pages')
    
    class Meta:
        ordering = ['order', 'title']
        verbose_name = 'Static Page'
        verbose_name_plural = 'Static Pages'
    
    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        """Get the URL for this page."""
        return reverse('pages:view', kwargs={'slug': self.slug})
    
    def save(self, *args, **kwargs):
        """Auto-set published_at when status changes to published."""
        if self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()
        elif self.status != 'published':
            self.published_at = None
        super().save(*args, **kwargs)
    
    def is_published(self):
        """Check if page is published."""
        return self.status == 'published'

