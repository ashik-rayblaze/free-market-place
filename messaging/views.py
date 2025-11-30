from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from .models import Conversation, Message, MessageAttachment
from accounts.models import User


@login_required
def conversation_list(request):
    """List user's conversations."""
    conversations = Conversation.objects.filter(
        participants=request.user,
        is_active=True
    ).order_by('-updated_at')
    
    # Add unread message count for each conversation
    conversations_with_unread = []
    total_unread = 0
    
    for conversation in conversations:
        unread_count = conversation.messages.filter(
            is_read=False
        ).exclude(sender=request.user).count()
        
        conversation.unread_count = unread_count
        conversations_with_unread.append(conversation)
        total_unread += unread_count
    
    # Pagination
    paginator = Paginator(conversations_with_unread, 10)
    page_number = request.GET.get('page')
    conversations = paginator.get_page(page_number)
    
    context = {
        'conversations': conversations,
        'total_unread': total_unread,
    }
    return render(request, 'messaging/conversation_list.html', context)


@login_required
def conversation_detail(request, pk):
    """View conversation and send messages."""
    conversation = get_object_or_404(Conversation, pk=pk, participants=request.user)
    
    # Mark messages as read
    conversation.messages.filter(is_read=False).exclude(sender=request.user).update(is_read=True)
    
    # Get messages
    messages_list = conversation.messages.all().order_by('created_at')
    
    if request.method == 'POST':
        content = request.POST.get('content', '').strip()
        if content:
            try:
                message = Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    content=content
                )
                
                # Update conversation timestamp
                conversation.save()
                
                messages.success(request, 'Message sent successfully!')
                return redirect('messaging:conversation_detail', pk=pk)
            except Exception as e:
                messages.error(request, f'Error sending message: {str(e)}')
        else:
            messages.error(request, 'Message cannot be empty.')
    
    other_participant = conversation.get_other_participant(request.user)
    
    context = {
        'conversation': conversation,
        'messages': messages_list,
        'other_participant': other_participant,
    }
    return render(request, 'messaging/conversation_detail.html', context)


@login_required
def send_message(request, conversation_id):
    """Send a message via AJAX."""
    if request.method == 'POST':
        conversation = get_object_or_404(Conversation, pk=conversation_id, participants=request.user)
        content = request.POST.get('content', '').strip()
        
        if content:
            try:
                message = Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    content=content
                )
                
                # Update conversation timestamp
                conversation.save()
                
                return JsonResponse({
                    'success': True,
                    'message': 'Message sent successfully!'
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': f'Error sending message: {str(e)}'
                })
        else:
            return JsonResponse({
                'success': False,
                'message': 'Message cannot be empty.'
            })
    
    return JsonResponse({
        'success': False,
        'message': 'Invalid request method.'
    })


@login_required
def start_conversation(request, user_id):
    """Start a new conversation with a user."""
    other_user = get_object_or_404(User, pk=user_id)
    
    if other_user == request.user:
        messages.error(request, 'You cannot start a conversation with yourself.')
        return redirect('accounts:dashboard')
    
    # Check if conversation already exists
    existing_conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=other_user
    ).first()
    
    if existing_conversation:
        return redirect('messaging:conversation_detail', pk=existing_conversation.pk)
    
    if request.method == 'POST':
        subject = request.POST.get('subject', '')
        initial_message = request.POST.get('message', '')
        
        try:
            conversation = Conversation.objects.create(
                subject=subject
            )
            conversation.participants.add(request.user, other_user)
            
            if initial_message:
                Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    content=initial_message
                )
            
            messages.success(request, 'Conversation started successfully!')
            return redirect('messaging:conversation_detail', pk=conversation.pk)
        except Exception as e:
            messages.error(request, f'Error starting conversation: {str(e)}')
    
    context = {
        'other_user': other_user,
    }
    return render(request, 'messaging/start_conversation.html', context)


@login_required
def start_project_conversation(request, project_id):
    """Start a conversation related to a project."""
    from projects.models import Project
    
    project = get_object_or_404(Project, pk=project_id)
    
    # Determine the other participant
    if request.user == project.employer:
        other_user = None  # Will be determined by the freelancer who bids
        messages.info(request, 'You can start a conversation once a freelancer places a bid on your project.')
        return redirect('projects:detail', pk=project_id)
    else:
        other_user = project.employer
    
    # Check if conversation already exists
    existing_conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=other_user
    ).filter(
        project=project
    ).first()
    
    if existing_conversation:
        return redirect('messaging:conversation_detail', pk=existing_conversation.pk)
    
    if request.method == 'POST':
        subject = request.POST.get('subject', f'Discussion about {project.title}')
        initial_message = request.POST.get('message', '')
        
        try:
            conversation = Conversation.objects.create(
                subject=subject,
                project=project
            )
            conversation.participants.add(request.user, other_user)
            
            if initial_message:
                Message.objects.create(
                    conversation=conversation,
                    sender=request.user,
                    content=initial_message
                )
            
            messages.success(request, 'Conversation started successfully!')
            return redirect('messaging:conversation_detail', pk=conversation.pk)
        except Exception as e:
            messages.error(request, f'Error starting conversation: {str(e)}')
    
    context = {
        'project': project,
        'other_user': other_user,
    }
    return render(request, 'messaging/start_project_conversation.html', context)

