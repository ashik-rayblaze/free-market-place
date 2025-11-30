from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.core.exceptions import PermissionDenied
from .models import Bid, BidAttachment, BidMessage
from projects.models import Project
from accounts.decorators import freelancer_required, owner_required


@login_required
def bid_list(request):
    """List user's bids."""
    if request.user.role == 'freelancer':
        bids = Bid.objects.filter(freelancer=request.user).order_by('-created_at')
    else:
        bids = Bid.objects.filter(project__employer=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(bids, 10)
    page_number = request.GET.get('page')
    bids = paginator.get_page(page_number)
    
    context = {
        'bids': bids,
    }
    return render(request, 'bids/bid_list.html', context)


@login_required
@freelancer_required
def bid_create(request, project_id):
    """Create a new bid (freelancers only)."""
    
    project = get_object_or_404(Project, pk=project_id)
    
    # Check if project can accept bids
    if not project.can_accept_bids():
        messages.error(request, 'This project is no longer accepting bids.')
        return redirect('projects:detail', pk=project_id)
    
    # Check if user has already bid on this project
    existing_bid = Bid.objects.filter(project=project, freelancer=request.user).first()
    if existing_bid:
        messages.info(request, 'You have already placed a bid on this project.')
        return redirect('bids:detail', pk=existing_bid.pk)
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        delivery_time = request.POST.get('delivery_time')
        proposal = request.POST.get('proposal')
        
        # Validation
        if not all([amount, delivery_time, proposal]):
            messages.error(request, 'Please fill in all required fields.')
            return render(request, 'bids/bid_create.html', {'project': project})
        
        try:
            bid = Bid.objects.create(
                project=project,
                freelancer=request.user,
                amount=amount,
                delivery_time=delivery_time,
                proposal=proposal,
            )
            
            # Increment project bid count
            project.increment_bids()
            
            messages.success(request, 'Bid placed successfully!')
            return redirect('bids:detail', pk=bid.pk)
        except Exception as e:
            messages.error(request, f'Error placing bid: {str(e)}')
    
    context = {
        'project': project,
    }
    return render(request, 'bids/bid_create.html', context)


def bid_detail(request, pk):
    """View bid details."""
    bid = get_object_or_404(Bid, pk=pk)
    
    # Check if user has permission to view this bid
    if request.user != bid.freelancer and request.user != bid.project.employer:
        messages.error(request, 'You do not have permission to view this bid.')
        return redirect('bids:list')
    
    # Get bid messages
    bid_messages = bid.messages.all().order_by('created_at')
    
    context = {
        'bid': bid,
        'bid_messages': bid_messages,
    }
    return render(request, 'bids/bid_detail.html', context)


@login_required
def bid_edit(request, pk):
    """Edit bid (freelancers only)."""
    bid = get_object_or_404(Bid, pk=pk)
    
    if bid.freelancer != request.user:
        messages.error(request, 'You can only edit your own bids.')
        return redirect('bids:detail', pk=pk)
    
    if not bid.can_be_modified():
        messages.error(request, 'This bid can no longer be modified.')
        return redirect('bids:detail', pk=pk)
    
    if request.method == 'POST':
        bid.amount = request.POST.get('amount')
        bid.delivery_time = request.POST.get('delivery_time')
        bid.proposal = request.POST.get('proposal')
        
        try:
            bid.save()
            messages.success(request, 'Bid updated successfully!')
            return redirect('bids:detail', pk=bid.pk)
        except Exception as e:
            messages.error(request, f'Error updating bid: {str(e)}')
    
    context = {
        'bid': bid,
    }
    return render(request, 'bids/bid_edit.html', context)


@login_required
@owner_required(Bid, 'freelancer')
def bid_delete(request, pk):
    """Delete bid (freelancers only)."""
    bid = get_object_or_404(Bid, pk=pk)
    
    if bid.freelancer != request.user and not (request.user.is_staff or request.user.is_superuser):
        messages.error(request, 'You can only delete your own bids.')
        raise PermissionDenied("You don't own this bid")
    
    if not bid.can_be_modified():
        messages.error(request, 'This bid can no longer be deleted.')
        return redirect('bids:detail', pk=pk)
    
    if request.method == 'POST':
        # Decrement project bid count
        bid.project.decrement_bids()
        bid.delete()
        messages.success(request, 'Bid deleted successfully!')
        return redirect('bids:list')
    
    context = {
        'bid': bid,
    }
    return render(request, 'bids/bid_delete.html', context)


@login_required
def bid_accept(request, pk):
    """Accept bid (employers only)."""
    bid = get_object_or_404(Bid, pk=pk)
    
    if bid.project.employer != request.user:
        messages.error(request, 'You can only accept bids on your own projects.')
        return redirect('bids:detail', pk=pk)
    
    if bid.status != 'pending':
        messages.error(request, 'This bid cannot be accepted.')
        return redirect('bids:detail', pk=pk)
    
    if request.method == 'POST':
        try:
            # Accept the bid
            bid.accept()
            
            # Reject all other bids on this project
            Bid.objects.filter(project=bid.project, status='pending').exclude(pk=bid.pk).update(status='rejected')
            
            messages.success(request, 'Bid accepted successfully!')
            return redirect('bids:detail', pk=bid.pk)
        except Exception as e:
            messages.error(request, f'Error accepting bid: {str(e)}')
    
    context = {
        'bid': bid,
    }
    return render(request, 'bids/bid_accept.html', context)


@login_required
def bid_reject(request, pk):
    """Reject bid (employers only)."""
    bid = get_object_or_404(Bid, pk=pk)
    
    if bid.project.employer != request.user:
        messages.error(request, 'You can only reject bids on your own projects.')
        return redirect('bids:detail', pk=pk)
    
    if bid.status != 'pending':
        messages.error(request, 'This bid cannot be rejected.')
        return redirect('bids:detail', pk=pk)
    
    if request.method == 'POST':
        try:
            bid.reject()
            messages.success(request, 'Bid rejected successfully!')
            return redirect('bids:detail', pk=bid.pk)
        except Exception as e:
            messages.error(request, f'Error rejecting bid: {str(e)}')
    
    context = {
        'bid': bid,
    }
    return render(request, 'bids/bid_reject.html', context)


@login_required
def bid_withdraw(request, pk):
    """Withdraw bid (freelancers only)."""
    bid = get_object_or_404(Bid, pk=pk)
    
    if bid.freelancer != request.user:
        messages.error(request, 'You can only withdraw your own bids.')
        return redirect('bids:detail', pk=pk)
    
    if bid.status != 'pending':
        messages.error(request, 'This bid cannot be withdrawn.')
        return redirect('bids:detail', pk=pk)
    
    if request.method == 'POST':
        try:
            bid.withdraw()
            # Decrement project bid count
            bid.project.decrement_bids()
            messages.success(request, 'Bid withdrawn successfully!')
            return redirect('bids:list')
        except Exception as e:
            messages.error(request, f'Error withdrawing bid: {str(e)}')
    
    context = {
        'bid': bid,
    }
    return render(request, 'bids/bid_withdraw.html', context)

