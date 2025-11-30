from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


def admin_required(view_func):
    """Decorator to ensure user is admin or staff."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('accounts:login')
        
        if not (request.user.is_staff or request.user.is_superuser):
            messages.error(request, 'You do not have permission to access this page.')
            raise PermissionDenied("Admin access required")
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def employer_required(view_func):
    """Decorator to ensure user is an employer."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('accounts:login')
        
        if request.user.role != 'employer':
            messages.error(request, 'Only employers can access this page.')
            raise PermissionDenied("Employer access required")
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def freelancer_required(view_func):
    """Decorator to ensure user is a freelancer."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('accounts:login')
        
        if request.user.role != 'freelancer':
            messages.error(request, 'Only freelancers can access this page.')
            raise PermissionDenied("Freelancer access required")
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def owner_required(model_class, owner_field='user'):
    """
    Decorator to ensure user owns the object.
    Usage: @owner_required(Project, 'employer')
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            if not request.user.is_authenticated:
                messages.error(request, 'Please log in to access this page.')
                return redirect('accounts:login')
            
            # Get pk from kwargs
            pk = kwargs.get('pk') or kwargs.get('id')
            if not pk:
                raise PermissionDenied("Object ID required")
            
            # Get the object
            obj = model_class.objects.get(pk=pk)
            
            # Check ownership
            owner = getattr(obj, owner_field, None)
            if owner != request.user and not (request.user.is_staff or request.user.is_superuser):
                messages.error(request, 'You do not have permission to access this resource.')
                raise PermissionDenied("You don't own this resource")
            
            return view_func(request, *args, **kwargs)
        return _wrapped_view
    return decorator


def verified_user_required(view_func):
    """Decorator to ensure user is verified."""
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.error(request, 'Please log in to access this page.')
            return redirect('accounts:login')
        
        if not request.user.is_verified and not (request.user.is_staff or request.user.is_superuser):
            messages.warning(request, 'Please verify your account to access this feature.')
            return redirect('accounts:profile')
        
        return view_func(request, *args, **kwargs)
    return _wrapped_view

