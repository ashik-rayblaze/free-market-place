// Main JavaScript for FreelancerHub

$(document).ready(function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    var popoverList = popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);

    // Smooth scrolling for anchor links
    $('a[href*="#"]').on('click', function(e) {
        e.preventDefault();
        var target = $(this.hash);
        if (target.length) {
            $('html, body').animate({
                scrollTop: target.offset().top - 100
            }, 1000);
        }
    });

    // Form validation
    // EXCLUDE payment-method-form - it has its own validation handler
    $('form').not('#payment-method-form').on('submit', function(e) {
        var form = $(this);
        var requiredFields = form.find('[required]');
        var isValid = true;

        requiredFields.each(function() {
            var field = $(this);
            if (!field.val().trim()) {
                field.addClass('is-invalid');
                isValid = false;
            } else {
                field.removeClass('is-invalid');
            }
        });

        if (!isValid) {
            e.preventDefault();
            showAlert('Please fill in all required fields.', 'danger');
        }
    });

    // Real-time search
    $('#search').on('input', function() {
        var query = $(this).val();
        if (query.length > 2) {
            // Implement real-time search here
            console.log('Searching for:', query);
        }
    });

    // Message sending
    $('#send-message-form').on('submit', function(e) {
        e.preventDefault();
        var form = $(this);
        var content = form.find('#message-content').val().trim();
        
        if (content) {
            sendMessage(form.attr('action'), content);
            form[0].reset();
        }
    });

    // Notification handling
    $('.mark-notification-read').on('click', function(e) {
        e.preventDefault();
        var notificationId = $(this).data('notification-id');
        markNotificationRead(notificationId);
    });

    // Payment method validation
    // DISABLED - Validation is now handled in template's vanilla JS handler
    // The jQuery handler was interfering with form submission
    // $('#payment-method-form').off('submit').on('submit', function(e) {
    //     // This handler is disabled - validation is in template
    // });

    // Project filtering
    $('#project-filters').on('change', 'select, input', function() {
        $('#project-filters').submit();
    });

    // Bid amount validation
    $('#bid-amount').on('input', function() {
        var amount = parseFloat($(this).val());
        var projectMin = parseFloat($(this).data('project-min'));
        var projectMax = parseFloat($(this).data('project-max'));

        if (amount < projectMin) {
            $(this).addClass('is-invalid');
            $('#amount-feedback').text('Amount must be at least $' + projectMin);
        } else if (amount > projectMax) {
            $(this).addClass('is-invalid');
            $('#amount-feedback').text('Amount must not exceed $' + projectMax);
        } else {
            $(this).removeClass('is-invalid');
            $('#amount-feedback').text('');
        }
    });

    // File upload preview
    $('input[type="file"]').on('change', function() {
        var file = this.files[0];
        var preview = $(this).siblings('.file-preview');
        
        if (file) {
            var reader = new FileReader();
            reader.onload = function(e) {
                preview.html('<img src="' + e.target.result + '" class="img-thumbnail" style="max-width: 100px; max-height: 100px;">');
            };
            reader.readAsDataURL(file);
        }
    });

    // Character counter for textareas
    $('textarea[maxlength]').on('input', function() {
        var maxLength = $(this).attr('maxlength');
        var currentLength = $(this).val().length;
        var counter = $(this).siblings('.char-counter');
        
        if (counter.length === 0) {
            counter = $('<small class="char-counter text-muted"></small>');
            $(this).after(counter);
        }
        
        counter.text(currentLength + '/' + maxLength);
        
        if (currentLength > maxLength * 0.9) {
            counter.addClass('text-warning');
        } else {
            counter.removeClass('text-warning');
        }
    });

    // Auto-save draft functionality
    var draftKey = 'freelancerhub_draft_' + window.location.pathname;
    var draftTimer;

    $('textarea, input[type="text"]').on('input', function() {
        clearTimeout(draftTimer);
        draftTimer = setTimeout(function() {
            saveDraft();
        }, 2000);
    });

    // Load draft on page load
    loadDraft();

    // Confirm before leaving page - always show "Changes you made may not be saved" dialog
    var allowNavigation = false; // Flag to allow navigation when needed
    
    // Store the beforeunload handler reference
    var beforeunloadHandler = function(e) {
        // Always show browser's "Changes you made may not be saved" dialog unless navigation is explicitly allowed
        if (!allowNavigation) {
            // Modern browsers require preventDefault() and setting returnValue
            e.preventDefault();
            // Setting returnValue to empty string triggers the browser's default dialog
            // The browser will show: "Changes you made may not be saved."
            e.returnValue = '';
            // Return the empty string for older browser compatibility
            return '';
        }
    };
    
    window.addEventListener('beforeunload', beforeunloadHandler);
    
    // Allow navigation when form is submitted
    $('form').on('submit', function() {
        allowNavigation = true;
        // Clear draft from localStorage
        localStorage.removeItem('freelancerhub_draft_' + window.location.pathname);
        // Remove beforeunload listener to allow form submission
        window.removeEventListener('beforeunload', beforeunloadHandler);
    });
    
    // Allow navigation when clicking submit buttons
    $('form button[type="submit"], form input[type="submit"]').on('click', function() {
        allowNavigation = true;
    });
    
    // Allow navigation for specific links (logout, delete confirmations, etc.)
    $('a[href*="logout"], a[href*="delete"], a[href*="confirm"], a[href*="submit"]').on('click', function() {
        allowNavigation = true;
    });
    
    // Reset allowNavigation flag after a short delay to ensure it works for the next navigation
    // This ensures the flag doesn't stay true permanently
    setTimeout(function() {
        allowNavigation = false;
    }, 100);
});

// Utility Functions
function showAlert(message, type) {
    var alertHtml = '<div class="alert alert-' + type + ' alert-dismissible fade show" role="alert">' +
                   message +
                   '<button type="button" class="btn-close" data-bs-dismiss="alert"></button>' +
                   '</div>';
    
    $('.container').first().prepend(alertHtml);
    
    setTimeout(function() {
        $('.alert').fadeOut('slow');
    }, 5000);
}

function sendMessage(url, content) {
    $.ajax({
        url: url,
        method: 'POST',
        data: {
            'content': content,
            'csrfmiddlewaretoken': $('[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            if (response.success) {
                // Reload the page to show the new message
                location.reload();
            } else {
                showAlert(response.message, 'danger');
            }
        },
        error: function() {
            showAlert('Error sending message. Please try again.', 'danger');
        }
    });
}

function markNotificationRead(notificationId) {
    $.ajax({
        url: '/reports/notifications/' + notificationId + '/mark-read/',
        method: 'POST',
        data: {
            'csrfmiddlewaretoken': $('[name=csrfmiddlewaretoken]').val()
        },
        success: function(response) {
            if (response.success) {
                $('[data-notification-id="' + notificationId + '"]').fadeOut();
            }
        }
    });
}

function saveDraft() {
    var formData = {};
    $('textarea, input[type="text"]').each(function() {
        if ($(this).val().trim()) {
            formData[$(this).attr('name')] = $(this).val();
        }
    });
    
    localStorage.setItem('freelancerhub_draft_' + window.location.pathname, JSON.stringify(formData));
}

function loadDraft() {
    var draft = localStorage.getItem('freelancerhub_draft_' + window.location.pathname);
    if (draft) {
        try {
            var formData = JSON.parse(draft);
            $.each(formData, function(name, value) {
                $('[name="' + name + '"]').val(value);
            });
        } catch (e) {
            console.log('Error loading draft:', e);
        }
    }
}

function hasUnsavedChanges() {
    var formData = {};
    $('textarea, input[type="text"]').each(function() {
        if ($(this).val().trim()) {
            formData[$(this).attr('name')] = $(this).val();
        }
    });
    
    var currentData = JSON.stringify(formData);
    var savedData = localStorage.getItem('freelancerhub_draft_' + window.location.pathname);
    
    return currentData !== savedData;
}

// Animation on scroll
function animateOnScroll() {
    $('.fade-in').each(function() {
        var elementTop = $(this).offset().top;
        var elementBottom = elementTop + $(this).outerHeight();
        var viewportTop = $(window).scrollTop();
        var viewportBottom = viewportTop + $(window).height();
        
        if (elementBottom > viewportTop && elementTop < viewportBottom) {
            $(this).addClass('animated');
        }
    });
}

$(window).on('scroll', animateOnScroll);
$(document).ready(animateOnScroll);