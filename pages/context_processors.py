from .models import StaticPage


def static_pages(request):
    """Context processor to add static pages to all templates."""
    footer_pages = StaticPage.objects.filter(
        show_in_footer=True,
        status='published'
    ).order_by('order', 'title')
    
    nav_pages = StaticPage.objects.filter(
        show_in_nav=True,
        status='published'
    ).order_by('order', 'title')
    
    return {
        'footer_pages': footer_pages,
        'nav_pages': nav_pages,
    }

