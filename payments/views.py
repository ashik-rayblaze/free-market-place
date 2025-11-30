from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Sum
from django.http import JsonResponse
from django.utils import timezone
from django.core.exceptions import PermissionDenied
from .models import PaymentMethod, Wallet, Transaction, Escrow
from projects.models import Project
from bids.models import Bid
from accounts.decorators import owner_required


@login_required
def payment_dashboard(request):
    """Payment dashboard for users."""
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    # Get recent transactions
    recent_transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')[:5]
    
    # Get payment methods
    payment_methods = PaymentMethod.objects.filter(user=request.user, is_active=True)
    
    # Get active escrows
    if request.user.role == 'employer':
        active_escrows = Escrow.objects.filter(employer=request.user, status='active')
    elif request.user.role == 'freelancer':
        active_escrows = Escrow.objects.filter(freelancer=request.user, status='active')
    else:
        active_escrows = Escrow.objects.none()
    
    context = {
        'wallet': wallet,
        'recent_transactions': recent_transactions,
        'payment_methods': payment_methods,
        'active_escrows': active_escrows,
    }
    return render(request, 'payments/dashboard.html', context)


@login_required
def wallet_view(request):
    """View wallet details and transaction history."""
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    # Get all transactions
    transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
    
    # Pagination
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)
    
    # Calculate statistics
    total_deposits = Transaction.objects.filter(
        user=request.user,
        transaction_type='deposit',
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_withdrawals = Transaction.objects.filter(
        user=request.user,
        transaction_type='withdrawal',
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    total_earnings = Transaction.objects.filter(
        user=request.user,
        transaction_type='payment',
        status='completed'
    ).aggregate(total=Sum('amount'))['total'] or 0
    
    context = {
        'wallet': wallet,
        'transactions': transactions,
        'total_deposits': total_deposits,
        'total_withdrawals': total_withdrawals,
        'total_earnings': total_earnings,
    }
    return render(request, 'payments/wallet.html', context)


@login_required
def add_funds(request):
    """Add funds to wallet (dummy payment)."""
    if request.method == 'POST':
        amount = request.POST.get('amount')
        payment_method_id = request.POST.get('payment_method')
        
        try:
            amount = float(amount)
            if amount <= 0:
                messages.error(request, 'Amount must be greater than 0.')
                return redirect('payments:add_funds')
            
            # Get payment method
            payment_method = get_object_or_404(PaymentMethod, pk=payment_method_id, user=request.user)
            
            # Create transaction (dummy payment - always succeeds)
            transaction = Transaction.objects.create(
                user=request.user,
                transaction_type='deposit',
                amount=amount,
                status='completed',
                payment_method=payment_method,
                description=f'Deposit via {payment_method.get_payment_type_display()}',
                completed_at=timezone.now()
            )
            
            # Add funds to wallet
            wallet, created = Wallet.objects.get_or_create(user=request.user)
            wallet.add_funds(amount)
            
            messages.success(request, f'Successfully added ${amount} to your wallet!')
            return redirect('payments:wallet')
        except (ValueError, PaymentMethod.DoesNotExist) as e:
            messages.error(request, f'Error adding funds: {str(e)}')
    
    payment_methods = PaymentMethod.objects.filter(user=request.user, is_active=True)
    context = {
        'payment_methods': payment_methods,
    }
    return render(request, 'payments/add_funds.html', context)


@login_required
def withdraw_funds(request):
    """Withdraw funds from wallet (dummy payment)."""
    wallet, created = Wallet.objects.get_or_create(user=request.user)
    
    if request.method == 'POST':
        amount = request.POST.get('amount')
        payment_method_id = request.POST.get('payment_method')
        
        try:
            amount = float(amount)
            if amount <= 0:
                messages.error(request, 'Amount must be greater than 0.')
                return redirect('payments:withdraw_funds')
            
            if amount > wallet.balance:
                messages.error(request, 'Insufficient funds.')
                return redirect('payments:withdraw_funds')
            
            # Get payment method
            payment_method = get_object_or_404(PaymentMethod, pk=payment_method_id, user=request.user)
            
            # Create transaction (dummy payment - always succeeds)
            transaction = Transaction.objects.create(
                user=request.user,
                transaction_type='withdrawal',
                amount=amount,
                status='completed',
                payment_method=payment_method,
                description=f'Withdrawal via {payment_method.get_payment_type_display()}',
                completed_at=timezone.now()
            )
            
            # Deduct funds from wallet
            wallet.deduct_funds(amount)
            
            messages.success(request, f'Successfully withdrew ${amount} from your wallet!')
            return redirect('payments:wallet')
        except (ValueError, PaymentMethod.DoesNotExist) as e:
            messages.error(request, f'Error withdrawing funds: {str(e)}')
    
    payment_methods = PaymentMethod.objects.filter(user=request.user, is_active=True)
    context = {
        'wallet': wallet,
        'payment_methods': payment_methods,
    }
    return render(request, 'payments/withdraw_funds.html', context)


@login_required
def payment_methods(request):
    """Manage payment methods."""
    payment_methods = PaymentMethod.objects.filter(user=request.user).order_by('-created_at')
    
    context = {
        'payment_methods': payment_methods,
    }
    return render(request, 'payments/payment_methods.html', context)


@login_required
def set_default_payment_method(request, pk):
    """Set a payment method as default."""
    payment_method = get_object_or_404(PaymentMethod, pk=pk, user=request.user)
    
    # Unset all other payment methods as default
    PaymentMethod.objects.filter(user=request.user).update(is_default=False)
    
    # Set this payment method as default
    payment_method.is_default = True
    payment_method.save()
    
    messages.success(request, f'{payment_method.get_payment_type_display()} has been set as your default payment method.')
    return redirect('payments:methods')


@login_required
def add_payment_method(request):
    """Add a new payment method."""
    if request.method == 'POST':
        payment_type = request.POST.get('payment_type')
        is_default = request.POST.get('is_default') == 'on'
        
        # Validate required fields
        if not payment_type:
            messages.error(request, 'Please select a payment type.')
            return redirect('payments:add_method')
        
        # For dummy payment, we'll just store basic info
        if payment_type in ['credit_card', 'debit_card']:
            card_brand = request.POST.get('card_brand', 'Visa')
            card_last_four = request.POST.get('card_last_four', '').strip()
            expiry_month = request.POST.get('expiry_month', '').strip()
            expiry_year = request.POST.get('expiry_year', '').strip()
            
            # Debug: Print received values
            print(f"DEBUG: payment_type={payment_type}, card_brand={card_brand}, card_last_four={card_last_four}, expiry_month={expiry_month}, expiry_year={expiry_year}, is_default={is_default}")
            print(f"DEBUG: card_last_four type={type(card_last_four)}, length={len(card_last_four) if card_last_four else 0}")
            print(f"DEBUG: expiry_month type={type(expiry_month)}, length={len(expiry_month) if expiry_month else 0}")
            print(f"DEBUG: expiry_year type={type(expiry_year)}, length={len(expiry_year) if expiry_year else 0}")
            print(f"DEBUG: All POST data: {dict(request.POST)}")
            
            # Validate all card details are provided
            if not card_last_four or not expiry_month or not expiry_year:
                print(f"ERROR: Validation failed - card_last_four='{card_last_four}', expiry_month='{expiry_month}', expiry_year='{expiry_year}'")
                messages.error(request, 'Please fill in all card detailss.')
                return redirect('payments:add_method')
            
            # Validate card last four digits
            if len(card_last_four) != 4 or not card_last_four.isdigit():
                messages.error(request, 'Please enter a valid 4-digit card number.')
                return redirect('payments:add_method')
            
            # Convert expiry month and year to integers if provided
            expiry_month_int = None
            expiry_year_int = None
            if expiry_month:
                try:
                    expiry_month_int = int(expiry_month)
                except ValueError:
                    pass
            if expiry_year:
                try:
                    expiry_year_int = int(expiry_year)
                except ValueError:
                    pass
            
            try:
                payment_method = PaymentMethod.objects.create(
                    user=request.user,
                    payment_type=payment_type,
                    card_brand=card_brand,
                    card_last_four=card_last_four,
                    expiry_month=expiry_month_int,
                    expiry_year=expiry_year_int,
                    is_default=is_default
                )
                print(f"DEBUG: Payment method created successfully: {payment_method.id}")
            except Exception as e:
                print(f"DEBUG: Error creating payment method: {str(e)}")
                import traceback
                print(traceback.format_exc())
                messages.error(request, f'Error saving payment method: {str(e)}')
                return redirect('payments:add_method')
        elif payment_type == 'bank_transfer':
            bank_name = request.POST.get('bank_name', '')
            account_number = request.POST.get('account_number', '')
            routing_number = request.POST.get('routing_number', '')
            
            # Validate required bank fields
            if not bank_name or not account_number or not routing_number:
                messages.error(request, 'Please fill in all bank details.')
                return redirect('payments:add_method')
            
            payment_method = PaymentMethod.objects.create(
                user=request.user,
                payment_type=payment_type,
                bank_name=bank_name,
                account_number=account_number,
                routing_number=routing_number,
                is_default=is_default
            )
        else:
            payment_method = PaymentMethod.objects.create(
                user=request.user,
                payment_type=payment_type,
                is_default=is_default
            )
        
        # If this is set as default, unset others
        if is_default:
            PaymentMethod.objects.filter(user=request.user).exclude(pk=payment_method.pk).update(is_default=False)
        
        messages.success(request, 'Payment method added successfully!')
        return redirect('payments:methods')
    
    context = {
        'payment_types': PaymentMethod.PAYMENT_TYPE_CHOICES,
    }
    return render(request, 'payments/add_payment_method.html', context)


@login_required
def delete_payment_method(request, pk):
    """Delete a payment method."""
    payment_method = get_object_or_404(PaymentMethod, pk=pk, user=request.user)
    
    if request.method == 'POST':
        payment_method.delete()
        messages.success(request, 'Payment method deleted successfully!')
        return redirect('payments:methods')
    
    context = {
        'payment_method': payment_method,
    }
    return render(request, 'payments/delete_payment_method.html', context)


@login_required
def transaction_list(request):
    """List all transactions."""
    transactions = Transaction.objects.filter(user=request.user).order_by('-created_at')
    
    # Filtering
    transaction_type = request.GET.get('type')
    status = request.GET.get('status')
    
    if transaction_type:
        transactions = transactions.filter(transaction_type=transaction_type)
    
    if status:
        transactions = transactions.filter(status=status)
    
    # Pagination
    paginator = Paginator(transactions, 20)
    page_number = request.GET.get('page')
    transactions = paginator.get_page(page_number)
    
    context = {
        'transactions': transactions,
        'transaction_types': Transaction.TRANSACTION_TYPE_CHOICES,
        'status_choices': Transaction.STATUS_CHOICES,
        'selected_type': transaction_type,
        'selected_status': status,
    }
    return render(request, 'payments/transaction_list.html', context)


@login_required
def escrow_detail(request, project_id):
    """View escrow details for a project."""
    project = get_object_or_404(Project, pk=project_id)
    
    # Check if user is involved in this project
    if request.user not in [project.employer, project.bids.filter(status='accepted').first().freelancer]:
        messages.error(request, 'You do not have permission to view this escrow.')
        return redirect('projects:home')
    
    escrow = get_object_or_404(Escrow, project=project)
    
    context = {
        'project': project,
        'escrow': escrow,
    }
    return render(request, 'payments/escrow_detail.html', context)


@login_required
def release_escrow(request, project_id):
    """Release escrow funds to freelancer."""
    project = get_object_or_404(Project, pk=project_id)
    
    if project.employer != request.user:
        messages.error(request, 'Only the employer can release escrow funds.')
        return redirect('payments:escrow_detail', project_id=project_id)
    
    escrow = get_object_or_404(Escrow, project=project, status='active')
    
    if request.method == 'POST':
        try:
            escrow.release_funds()
            messages.success(request, 'Escrow funds released successfully!')
            return redirect('payments:escrow_detail', project_id=project_id)
        except Exception as e:
            messages.error(request, f'Error releasing escrow: {str(e)}')
    
    context = {
        'project': project,
        'escrow': escrow,
    }
    return render(request, 'payments/release_escrow.html', context)


@login_required
def refund_escrow(request, project_id):
    """Refund escrow funds to employer."""
    project = get_object_or_404(Project, pk=project_id)
    
    if project.employer != request.user:
        messages.error(request, 'Only the employer can refund escrow funds.')
        return redirect('payments:escrow_detail', project_id=project_id)
    
    escrow = get_object_or_404(Escrow, project=project, status='active')
    
    if request.method == 'POST':
        try:
            escrow.refund_funds()
            messages.success(request, 'Escrow funds refunded successfully!')
            return redirect('payments:escrow_detail', project_id=project_id)
        except Exception as e:
            messages.error(request, f'Error refunding escrow: {str(e)}')
    
    context = {
        'project': project,
        'escrow': escrow,
    }
    return render(request, 'payments/refund_escrow.html', context)

