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
    $('form').on('submit', function(e) {
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
    $('#payment-method-form').on('submit', function(e) {
        var paymentType = $('#payment_type').val();
        var isValid = true;

        if (paymentType === 'credit_card' || paymentType === 'debit_card') {
            var cardNumber = $('#card_number').val();
            var expiryMonth = $('#expiry_month').val();
            var expiryYear = $('#expiry_year').val();
            var cvv = $('#cvv').val();

            if (!cardNumber || !expiryMonth || !expiryYear || !cvv) {
                isValid = false;
                showAlert('Please fill in all card detailsss.', 'danger');
            }
        }

        if (!isValid) {
            e.preventDefault();
        }
    });

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

    // Confirm before leaving page with unsaved changes
    window.addEventListener('beforeunload', function(e) {
        if (hasUnsavedChanges()) {
            e.preventDefault();
            e.returnValue = '';
        }
    });
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
