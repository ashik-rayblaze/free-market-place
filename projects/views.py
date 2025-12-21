from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from .models import Project, Category, ProjectAttachment, ProjectMilestone
from accounts.models import Profile
from accounts.decorators import employer_required, owner_required


def project_list(request):
    """List all open projects with filtering and search."""
    projects = Project.objects.filter(status='open').order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        projects = projects.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query) |
            Q(skills_required__icontains=search_query)
        )
    
    # Category filtering
    category_id = request.GET.get('category')
    if category_id:
        projects = projects.filter(category_id=category_id)
    
    # Budget filtering
    budget_min = request.GET.get('budget_min')
    budget_max = request.GET.get('budget_max')
    if budget_min:
        projects = projects.filter(budget_min__gte=budget_min)
    if budget_max:
        projects = projects.filter(budget_max__lte=budget_max)
    
    # Experience level filtering
    experience_level = request.GET.get('experience_level')
    if experience_level:
        projects = projects.filter(experience_level=experience_level)
    
    # Pagination
    paginator = Paginator(projects, 12)
    page_number = request.GET.get('page')
    projects = paginator.get_page(page_number)
    
    # Get categories for filter
    categories = Category.objects.all()
    
    context = {
        'projects': projects,
        'categories': categories,
        'search_query': search_query,
        'selected_category': category_id,
        'selected_experience': experience_level,
    }
    return render(request, 'projects/project_list.html', context)


def project_detail(request, pk):
    """View project details."""
    project = get_object_or_404(Project, pk=pk)
    
    # Increment view count
    project.increment_views()
    
    # Get project bids
    bids = project.bids.all().order_by('-created_at')
    
    # Check if user has already bid on this project
    user_bid = None
    if request.user.is_authenticated and request.user.role == 'freelancer':
        user_bid = bids.filter(freelancer=request.user).first()
    
    # Get project milestones
    milestones = project.milestones.all().order_by('due_date')
    
    context = {
        'project': project,
        'bids': bids,
        'user_bid': user_bid,
        'milestones': milestones,
    }
    return render(request, 'projects/project_detail.html', context)


@login_required
@employer_required
def project_create(request):
    """Create a new project (employers only)."""
    
    if request.method == 'POST':
        title = request.POST.get('title')
        description = request.POST.get('description')
        category_id = request.POST.get('category')
        budget_type = request.POST.get('budget_type')
        budget_min = request.POST.get('budget_min')
        budget_max = request.POST.get('budget_max')
        deadline = request.POST.get('deadline')
        skills_required = request.POST.get('skills_required')
        experience_level = request.POST.get('experience_level')
        
        # Validation
        if not all([title, description, category_id, budget_min, budget_max, deadline, skills_required]):
            messages.error(request, 'Please fill in all required fields.')
            categories = Category.objects.all()
            return render(request, 'projects/project_create.html', {
                'categories': categories,
                'form_data': request.POST
            })
        
        # Validate budget values
        try:
            budget_min = float(budget_min)
            budget_max = float(budget_max)
            if budget_min <= 0 or budget_max <= 0:
                messages.error(request, 'Budget values must be greater than 0.')
                categories = Category.objects.all()
                return render(request, 'projects/project_create.html', {
                    'categories': categories,
                    'form_data': request.POST
                })
            if budget_min > budget_max:
                messages.error(request, 'Minimum budget cannot be greater than maximum budget.')
                categories = Category.objects.all()
                return render(request, 'projects/project_create.html', {
                    'categories': categories,
                    'form_data': request.POST
                })
        except (ValueError, TypeError):
            messages.error(request, 'Invalid budget values. Please enter valid numbers.')
            categories = Category.objects.all()
            return render(request, 'projects/project_create.html', {
                'categories': categories,
                'form_data': request.POST
            })
        
        try:
            category = Category.objects.get(id=category_id)
            
            # Convert budget values to Decimal
            from decimal import Decimal
            budget_min_decimal = Decimal(str(budget_min))
            budget_max_decimal = Decimal(str(budget_max))
            
            # Parse deadline
            from django.utils.dateparse import parse_datetime
            from django.utils import timezone
            deadline_datetime = parse_datetime(deadline)
            if not deadline_datetime:
                messages.error(request, 'Invalid deadline format. Please use the date picker.')
                categories = Category.objects.all()
                return render(request, 'projects/project_create.html', {
                    'categories': categories,
                    'form_data': request.POST
                })
            
            # Make datetime timezone-aware if it's naive
            if timezone.is_naive(deadline_datetime):
                deadline_datetime = timezone.make_aware(deadline_datetime)
            
            # Check if deadline is in the past
            if deadline_datetime < timezone.now():
                messages.error(request, 'Deadline cannot be in the past.')
                categories = Category.objects.all()
                return render(request, 'projects/project_create.html', {
                    'categories': categories,
                    'form_data': request.POST
                })
            
            project = Project.objects.create(
                title=title.strip(),
                description=description.strip(),
                category=category,
                employer=request.user,
                budget_type=budget_type,
                budget_min=budget_min_decimal,
                budget_max=budget_max_decimal,
                deadline=deadline_datetime,
                skills_required=skills_required.strip(),
                experience_level=experience_level,
            )
            
            messages.success(request, 'Project created successfully!')
            return redirect('projects:detail', pk=project.pk)
        except Category.DoesNotExist:
            messages.error(request, 'Selected category does not exist.')
            categories = Category.objects.all()
            return render(request, 'projects/project_create.html', {
                'categories': categories,
                'form_data': request.POST
            })
        except ValueError as e:
            messages.error(request, f'Invalid input: {str(e)}')
            categories = Category.objects.all()
            return render(request, 'projects/project_create.html', {
                'categories': categories,
                'form_data': request.POST
            })
        except Exception as e:
            messages.error(request, f'Error creating project: {str(e)}')
            import traceback
            print(traceback.format_exc())
            categories = Category.objects.all()
            return render(request, 'projects/project_create.html', {
                'categories': categories,
                'form_data': request.POST
            })
    
    categories = Category.objects.all()
    context = {
        'categories': categories,
    }
    return render(request, 'projects/project_create.html', context)


@login_required
@owner_required(Project, 'employer')
def project_edit(request, pk):
    """Edit project (employers only)."""
    project = get_object_or_404(Project, pk=pk)
    
    if project.employer != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You can only edit your own projects.')
        raise PermissionDenied("You don't own this project")
    
    if request.method == 'POST':
        project.title = request.POST.get('title')
        project.description = request.POST.get('description')
        project.budget_type = request.POST.get('budget_type')
        project.budget_min = request.POST.get('budget_min')
        project.budget_max = request.POST.get('budget_max')
        
        # Parse and handle deadline datetime
        from django.utils.dateparse import parse_datetime
        from django.utils import timezone
        deadline_str = request.POST.get('deadline')
        if deadline_str:
            deadline_datetime = parse_datetime(deadline_str)
            if deadline_datetime:
                # Make datetime timezone-aware if it's naive
                if timezone.is_naive(deadline_datetime):
                    deadline_datetime = timezone.make_aware(deadline_datetime)
                project.deadline = deadline_datetime
            else:
                messages.error(request, 'Invalid deadline format. Please use the date picker.')
                categories = Category.objects.all()
                context = {
                    'project': project,
                    'categories': categories,
                }
                return render(request, 'projects/project_edit.html', context)
        
        project.skills_required = request.POST.get('skills_required')
        project.experience_level = request.POST.get('experience_level')
        
        try:
            project.save()
            messages.success(request, 'Project updated successfully!')
            return redirect('projects:detail', pk=project.pk)
        except Exception as e:
            messages.error(request, f'Error updating project: {str(e)}')
    
    categories = Category.objects.all()
    context = {
        'project': project,
        'categories': categories,
    }
    return render(request, 'projects/project_edit.html', context)


@login_required
@owner_required(Project, 'employer')
def project_delete(request, pk):
    """Delete project (employers only)."""
    project = get_object_or_404(Project, pk=pk)
    
    if project.employer != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You can only delete your own projects.')
        raise PermissionDenied("You don't own this project")
    
    if request.method == 'POST':
        project.delete()
        messages.success(request, 'Project deleted successfully!')
        return redirect('accounts:dashboard')
    
    context = {
        'project': project,
    }
    return render(request, 'projects/project_delete.html', context)


def project_search(request):
    """Advanced project search."""
    projects = Project.objects.filter(status='open')
    
    # Search parameters
    search_query = request.GET.get('q', '')
    category_id = request.GET.get('category')
    budget_min = request.GET.get('budget_min')
    budget_max = request.GET.get('budget_max')
    experience_level = request.GET.get('experience_level')
    skills = request.GET.get('skills', '')
    
    # Apply filters
    if search_query:
        projects = projects.filter(
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if category_id:
        projects = projects.filter(category_id=category_id)
    
    if budget_min:
        projects = projects.filter(budget_min__gte=budget_min)
    
    if budget_max:
        projects = projects.filter(budget_max__lte=budget_max)
    
    if experience_level:
        projects = projects.filter(experience_level=experience_level)
    
    if skills:
        skills_list = [skill.strip() for skill in skills.split(',')]
        for skill in skills_list:
            projects = projects.filter(skills_required__icontains=skill)
    
    # Pagination
    paginator = Paginator(projects, 12)
    page_number = request.GET.get('page')
    projects = paginator.get_page(page_number)
    
    categories = Category.objects.all()
    
    context = {
        'projects': projects,
        'categories': categories,
        'search_params': {
            'q': search_query,
            'category': category_id,
            'budget_min': budget_min,
            'budget_max': budget_max,
            'experience_level': experience_level,
            'skills': skills,
        }
    }
    return render(request, 'projects/project_search.html', context)


def project_list_by_category(request, category_id):
    """List projects by category."""
    category = get_object_or_404(Category, id=category_id)
    projects = Project.objects.filter(category=category, status='open').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(projects, 12)
    page_number = request.GET.get('page')
    projects = paginator.get_page(page_number)
    
    context = {
        'projects': projects,
        'category': category,
    }
    return render(request, 'projects/project_list_by_category.html', context)

