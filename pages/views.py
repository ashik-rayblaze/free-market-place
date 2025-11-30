from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from .models import StaticPage
from accounts.decorators import admin_required


def is_admin(user):
    """Check if user is admin or staff."""
    return user.is_authenticated and (user.is_staff or user.is_superuser)


def page_view(request, slug):
    """View a static page."""
    page = get_object_or_404(StaticPage, slug=slug, status='published')
    
    context = {
        'page': page,
    }
    return render(request, 'pages/view.html', context)


@login_required
@user_passes_test(is_admin)
def admin_page_list(request):
    """List all static pages for admin."""
    pages = StaticPage.objects.all().order_by('order', 'title')
    
    # Search
    search_query = request.GET.get('search', '')
    if search_query:
        pages = pages.filter(
            Q(title__icontains=search_query) |
            Q(slug__icontains=search_query) |
            Q(content__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        pages = pages.filter(status=status_filter)
    
    # Filter by page type
    type_filter = request.GET.get('type', '')
    if type_filter:
        pages = pages.filter(page_type=type_filter)
    
    # Pagination
    paginator = Paginator(pages, 20)
    page_number = request.GET.get('page')
    pages = paginator.get_page(page_number)
    
    context = {
        'pages': pages,
        'search_query': search_query,
        'status_filter': status_filter,
        'type_filter': type_filter,
    }
    return render(request, 'admin/pages/list.html', context)


@login_required
@user_passes_test(is_admin)
def admin_page_create(request):
    """Create a new static page."""
    if request.method == 'POST':
        title = request.POST.get('title')
        slug = request.POST.get('slug')
        page_type = request.POST.get('page_type', 'custom')
        content = request.POST.get('content')
        meta_description = request.POST.get('meta_description', '')
        meta_keywords = request.POST.get('meta_keywords', '')
        status = request.POST.get('status', 'draft')
        is_featured = request.POST.get('is_featured') == 'on'
        show_in_footer = request.POST.get('show_in_footer') == 'on'
        show_in_nav = request.POST.get('show_in_nav') == 'on'
        order = request.POST.get('order', 0)
        
        # Validation
        if not all([title, slug, content]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'admin/pages/create.html', {
                'form_data': request.POST
            })
        
        try:
            page = StaticPage.objects.create(
                title=title,
                slug=slug,
                page_type=page_type,
                content=content,
                meta_description=meta_description,
                meta_keywords=meta_keywords,
                status=status,
                is_featured=is_featured,
                show_in_footer=show_in_footer,
                show_in_nav=show_in_nav,
                order=int(order) if order else 0,
                created_by=request.user,
                updated_by=request.user,
            )
            
            messages.success(request, 'Static page created successfully!')
            return redirect('accounts:admin_pages')
        except Exception as e:
            messages.error(request, f'Error creating page: {str(e)}')
    
    context = {
        'page_types': StaticPage.PAGE_TYPES,
        'status_choices': StaticPage.STATUS_CHOICES,
    }
    return render(request, 'admin/pages/create.html', context)


@login_required
@admin_required
def admin_page_edit(request, pk):
    """Edit a static page."""
    page = get_object_or_404(StaticPage, pk=pk)
    
    # Only allow editing if user is admin or created the page
    if page.created_by != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You can only edit pages you created.')
        raise PermissionDenied("You don't have permission to edit this page")
    
    if request.method == 'POST':
        page.title = request.POST.get('title')
        page.slug = request.POST.get('slug')
        page.page_type = request.POST.get('page_type', 'custom')
        page.content = request.POST.get('content')
        page.meta_description = request.POST.get('meta_description', '')
        page.meta_keywords = request.POST.get('meta_keywords', '')
        page.status = request.POST.get('status', 'draft')
        page.is_featured = request.POST.get('is_featured') == 'on'
        page.show_in_footer = request.POST.get('show_in_footer') == 'on'
        page.show_in_nav = request.POST.get('show_in_nav') == 'on'
        page.order = int(request.POST.get('order', 0)) if request.POST.get('order') else 0
        page.updated_by = request.user
        
        try:
            page.save()
            messages.success(request, 'Static page updated successfully!')
            return redirect('accounts:admin_pages')
        except Exception as e:
            messages.error(request, f'Error updating page: {str(e)}')
    
    context = {
        'page': page,
        'page_types': StaticPage.PAGE_TYPES,
        'status_choices': StaticPage.STATUS_CHOICES,
    }
    return render(request, 'admin/pages/edit.html', context)


@login_required
@admin_required
def admin_page_delete(request, pk):
    """Delete a static page."""
    page = get_object_or_404(StaticPage, pk=pk)
    
    # Only allow deleting if user is admin or created the page
    if page.created_by != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You can only delete pages you created.')
        raise PermissionDenied("You don't have permission to delete this page")
    
    if request.method == 'POST':
        page.delete()
        messages.success(request, 'Static page deleted successfully!')
        return redirect('accounts:admin_pages')
    
    context = {
        'page': page,
    }
    return render(request, 'admin/pages/delete.html', context)

