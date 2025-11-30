"""
URL configuration for freelancer_marketplace project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView
from accounts import views as accounts_views

# Customize admin site
admin.site.site_header = "Freelancer Marketplace Administration"
admin.site.site_title = "Freelancer Marketplace Admin"
admin.site.index_title = "Welcome to Freelancer Marketplace Administration"

urlpatterns = [
    # Django admin disabled - redirect to custom admin dashboard
    path('admin/', accounts_views.admin_redirect, name='admin_redirect'),
    path('admin/login/', accounts_views.admin_redirect, name='admin_login_redirect'),
    path('', include('accounts.urls')),
    # Redirect singular 'project' to plural 'projects'
    path('project/create/', RedirectView.as_view(url='/projects/create/', permanent=True)),
    path('projects/', include('projects.urls')),
    path('bids/', include('bids.urls')),
    path('messaging/', include('messaging.urls')),
    path('payments/', include('payments.urls')),
    path('reports/', include('reports.urls')),
    path('pages/', include('pages.urls')),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)

