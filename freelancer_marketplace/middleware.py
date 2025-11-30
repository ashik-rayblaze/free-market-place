from django.shortcuts import redirect
from django.contrib import messages
from django.core.exceptions import PermissionDenied


class AuthorizationMiddleware:
    """Middleware to add additional authorization checks."""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Add custom authorization logic here if needed
        response = self.get_response(request)
        return response
    
    def process_exception(self, request, exception):
        """Handle PermissionDenied exceptions."""
        if isinstance(exception, PermissionDenied):
            messages.error(request, 'You do not have permission to access this resource.')
            if request.user.is_authenticated:
                return redirect('accounts:dashboard')
            else:
                return redirect('accounts:login')
        return None

