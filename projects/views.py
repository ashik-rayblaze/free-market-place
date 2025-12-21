from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.core.exceptions import PermissionDenied
from .models import Project, Category, ProjectAttachment, ProjectMilestone, ProjectPhase
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
    
    # Check if project has accepted bid
    accepted_bid = bids.filter(status='accepted').first()
    
    # Get project milestones
    milestones = project.milestones.all().order_by('due_date')
    
    context = {
        'project': project,
        'bids': bids,
        'user_bid': user_bid,
        'accepted_bid': accepted_bid,
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


# ==================== Phase Management Views ====================

@login_required
def phase_list(request, project_id):
    """List all phases for a project."""
    project = get_object_or_404(Project, pk=project_id)
    
    # Check permissions: employer can manage, freelancer can view if bid accepted
    accepted_bid = project.bids.filter(status='accepted').first()
    is_employer = project.employer == request.user
    is_freelancer = accepted_bid and accepted_bid.freelancer == request.user
    
    if not (is_employer or is_freelancer or request.user.is_staff):
        messages.error(request, 'You do not have permission to view phases for this project.')
        return redirect('projects:detail', pk=project_id)
    
    phases = project.phases.all()
    
    # Calculate phase statistics
    total_allocated = project.get_total_phases_amount()
    paid_amount = project.get_paid_phases_amount()
    completed_count = project.get_completed_phases_count()
    remaining_budget = project.budget_max - total_allocated
    budget_exceeded_by = abs(remaining_budget) if remaining_budget < 0 else 0
    
    context = {
        'project': project,
        'phases': phases,
        'is_employer': is_employer,
        'is_freelancer': is_freelancer,
        'accepted_bid': accepted_bid,
        'total_allocated': total_allocated,
        'paid_amount': paid_amount,
        'completed_count': completed_count,
        'remaining_budget': remaining_budget,
        'budget_exceeded_by': budget_exceeded_by,
    }
    return render(request, 'projects/phase_list.html', context)


@login_required
def phase_create(request, project_id):
    """Create a new phase for a project."""
    project = get_object_or_404(Project, pk=project_id)
    
    # Only employer can create phases
    if project.employer != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Only the project employer can create phases.')
        return redirect('projects:detail', pk=project_id)
    
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description')
        amount = request.POST.get('amount')
        order = request.POST.get('order', 0)
        
        # Validation
        if not all([name, description, amount]):
            messages.error(request, 'Please fill in all required fields.')
            total_allocated = project.get_total_phases_amount()
            remaining_budget = project.budget_max - total_allocated
            return render(request, 'projects/phase_create.html', {
                'project': project,
                'next_order': project.phases.count() + 1,
                'total_allocated': total_allocated,
                'remaining_budget': remaining_budget,
            })
        
        try:
            from decimal import Decimal
            amount = Decimal(str(amount))
            order = int(order) if order else 0
            
            if amount <= 0:
                messages.error(request, 'Amount must be greater than 0.')
                total_allocated = project.get_total_phases_amount()
                remaining_budget = project.budget_max - total_allocated
                return render(request, 'projects/phase_create.html', {
                    'project': project,
                    'next_order': project.phases.count() + 1,
                    'total_allocated': total_allocated,
                    'remaining_budget': remaining_budget,
                })
            
            # Check if adding this phase would exceed project budget
            if not project.can_add_phase_amount(amount):
                current_total = project.get_total_phases_amount()
                remaining = project.budget_max - current_total
                new_total = current_total + amount
                messages.error(
                    request, 
                    f'Cannot add phase. Total phase amount (${new_total:.2f}) would exceed project budget (${project.budget_max:.2f}). '
                    f'Remaining budget: ${remaining:.2f}'
                )
                return render(request, 'projects/phase_create.html', {
                    'project': project,
                    'next_order': project.phases.count() + 1,
                    'total_allocated': current_total,
                    'remaining_budget': remaining,
                })
            
            phase = ProjectPhase.objects.create(
                project=project,
                name=name.strip(),
                description=description.strip(),
                amount=amount,
                order=order
            )
            
            messages.success(request, f'Phase "{phase.name}" created successfully!')
            return redirect('projects:phase_list', project_id=project_id)
        except ValueError:
            messages.error(request, 'Invalid amount or order value.')
        except Exception as e:
            messages.error(request, f'Error creating phase: {str(e)}')
    
    # Get next order number
    next_order = project.phases.count() + 1
    
    # Calculate budget info
    total_allocated = project.get_total_phases_amount()
    remaining_budget = project.budget_max - total_allocated
    
    context = {
        'project': project,
        'next_order': next_order,
        'total_allocated': total_allocated,
        'remaining_budget': remaining_budget,
    }
    return render(request, 'projects/phase_create.html', context)


@login_required
def phase_edit(request, project_id, phase_id):
    """Edit a phase."""
    project = get_object_or_404(Project, pk=project_id)
    phase = get_object_or_404(ProjectPhase, pk=phase_id, project=project)
    
    # Only employer can edit phases
    if project.employer != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Only the project employer can edit phases.')
        return redirect('projects:phase_list', project_id=project_id)
    
    if request.method == 'POST':
        phase.name = request.POST.get('name')
        phase.description = request.POST.get('description')
        new_amount = request.POST.get('amount')
        phase.order = request.POST.get('order', phase.order)
        
        try:
            from decimal import Decimal
            new_amount = Decimal(str(new_amount))
            phase.order = int(phase.order) if phase.order else phase.order
            
            if new_amount <= 0:
                messages.error(request, 'Amount must be greater than 0.')
                total_allocated = project.get_total_phases_amount()
                other_phases_total = total_allocated - phase.amount
                return render(request, 'projects/phase_edit.html', {
                    'project': project,
                    'phase': phase,
                    'total_allocated': total_allocated,
                    'other_phases_total': other_phases_total,
                })
            
            # Check if updating this phase would exceed project budget (only if not paid)
            if phase.status != 'paid' and not project.can_add_phase_amount(new_amount, exclude_phase=phase):
                current_total = project.get_total_phases_amount()
                remaining = project.budget_max - (current_total - phase.amount)
                new_total = current_total - phase.amount + new_amount
                messages.error(
                    request, 
                    f'Cannot update phase. Total phase amount (${new_total:.2f}) would exceed project budget (${project.budget_max:.2f}). '
                    f'Remaining budget: ${remaining:.2f}'
                )
                total_allocated = project.get_total_phases_amount()
                other_phases_total = total_allocated - phase.amount
                return render(request, 'projects/phase_edit.html', {
                    'project': project,
                    'phase': phase,
                    'total_allocated': total_allocated,
                    'other_phases_total': other_phases_total,
                })
            
            # Only update amount if phase is not paid
            if phase.status != 'paid':
                phase.amount = new_amount
            phase.save()
            messages.success(request, f'Phase "{phase.name}" updated successfully!')
            return redirect('projects:phase_list', project_id=project_id)
        except ValueError:
            messages.error(request, 'Invalid amount or order value.')
        except Exception as e:
            messages.error(request, f'Error updating phase: {str(e)}')
    
    # Calculate budget info
    total_allocated = project.get_total_phases_amount()
    other_phases_total = total_allocated - phase.amount
    
    context = {
        'project': project,
        'phase': phase,
        'total_allocated': total_allocated,
        'other_phases_total': other_phases_total,
    }
    return render(request, 'projects/phase_edit.html', context)


@login_required
def phase_delete(request, project_id, phase_id):
    """Delete a phase."""
    project = get_object_or_404(Project, pk=project_id)
    phase = get_object_or_404(ProjectPhase, pk=phase_id, project=project)
    
    # Only employer can delete phases
    if project.employer != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'Only the project employer can delete phases.')
        return redirect('projects:phase_list', project_id=project_id)
    
    # Don't allow deleting if phase is paid or in progress
    if phase.status in ['paid', 'in_progress']:
        messages.error(request, f'Cannot delete a phase that is {phase.get_status_display().lower()}.')
        return redirect('projects:phase_list', project_id=project_id)
    
    if request.method == 'POST':
        phase_name = phase.name
        phase.delete()
        messages.success(request, f'Phase "{phase_name}" deleted successfully!')
        return redirect('projects:phase_list', project_id=project_id)
    
    context = {
        'project': project,
        'phase': phase,
    }
    return render(request, 'projects/phase_delete.html', context)


@login_required
def phase_start(request, project_id, phase_id):
    """Start a phase (freelancer action)."""
    project = get_object_or_404(Project, pk=project_id)
    phase = get_object_or_404(ProjectPhase, pk=phase_id, project=project)
    
    # Check if user is the freelancer assigned to this project
    accepted_bid = project.bids.filter(status='accepted').first()
    if not accepted_bid or accepted_bid.freelancer != request.user:
        messages.error(request, 'You do not have permission to start this phase.')
        return redirect('projects:detail', pk=project_id)
    
    if phase.start():
        messages.success(request, f'Phase "{phase.name}" started successfully!')
    else:
        messages.error(request, 'Cannot start this phase. Previous phases must be completed first.')
    
    return redirect('projects:phase_list', project_id=project_id)


@login_required
def phase_complete(request, project_id, phase_id):
    """Mark a phase as completed (freelancer action)."""
    project = get_object_or_404(Project, pk=project_id)
    phase = get_object_or_404(ProjectPhase, pk=phase_id, project=project)
    
    # Check if user is the freelancer assigned to this project
    accepted_bid = project.bids.filter(status='accepted').first()
    if not accepted_bid or accepted_bid.freelancer != request.user:
        messages.error(request, 'You do not have permission to complete this phase.')
        return redirect('projects:detail', pk=project_id)
    
    if phase.mark_completed():
        messages.success(request, f'Phase "{phase.name}" marked as completed! You can now request payment.')
    else:
        messages.error(request, 'Cannot complete this phase. It must be in progress first.')
    
    return redirect('projects:phase_list', project_id=project_id)

