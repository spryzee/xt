// XTLive Animations and Loading Effects

document.addEventListener('DOMContentLoaded', function() {
    // Initialize loading screen
    initLoadingScreen();
    
    // Button click effects
    initButtonEffects();
    
    // Add loading animations to form submissions
    initFormSubmissions();
});

// Function to create and show loading screen
function initLoadingScreen() {
    // Check if user has already seen the loading screen in this session
    if (sessionStorage.getItem('loadingShown')) {
        // Skip loading screen for subsequent page views
        return;
    }
    
    // Create loading screen element on page load
    const loadingScreen = document.createElement('div');
    loadingScreen.className = 'xtlive-loading-screen';
    loadingScreen.innerHTML = `
        <div class="xtlive-logo">
            <div class="xtlive-logo-text">XTLive</div>
        </div>
        <div class="xtlive-loading-bar">
            <div class="xtlive-loading-progress"></div>
        </div>
        <div class="xtlive-loading-text">Loading resources...</div>
    `;
    
    document.body.appendChild(loadingScreen);
    
    // Hide loading screen after page is fully loaded
    window.addEventListener('load', function() {
        setTimeout(function() {
            loadingScreen.style.opacity = '0';
            loadingScreen.style.transition = 'opacity 0.5s ease';
            
            setTimeout(function() {
                loadingScreen.remove();
                
                // Set flag in sessionStorage to indicate loading screen has been shown
                sessionStorage.setItem('loadingShown', 'true');
            }, 500);
        }, 1500);
    });
}

// Function to initialize button click effects
function initButtonEffects() {
    const buttons = document.querySelectorAll('.btn');
    
    buttons.forEach(button => {
        button.classList.add('btn-click-effect');
        
        button.addEventListener('click', function(e) {
            // Only show transition on a real page reload (like logout), not for internal navigation
            // We'll check if it's a form submission button since those typically need processing time
            if (this.getAttribute('type') === 'submit' && !this.closest('form').classList.contains('no-loading')) {
                // Only show loading for form submissions that will create server processing
                // We don't show it for navigation buttons that use href
            }
            
            // Add ripple effect
            this.classList.remove('animate');
            void this.offsetWidth; // Trigger reflow to restart animation
            this.classList.add('animate');
        });
    });
    
    // Special handling for subscribe buttons
    const subscribeButtons = document.querySelectorAll('.subscribe-button');
    subscribeButtons.forEach(button => {
        button.addEventListener('mouseenter', function() {
            this.innerHTML = `<i class="fab fa-discord me-2"></i> Join Discord`;
        });
        
        button.addEventListener('mouseleave', function() {
            const originalIcon = this.getAttribute('data-original-icon') || 'fas fa-crown';
            const originalText = this.getAttribute('data-original-text') || 'Subscribe Now';
            this.innerHTML = `<i class="${originalIcon} me-2"></i> ${originalText}`;
        });
    });
}

// Function to add loading animations to form submissions
function initFormSubmissions() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', function(e) {
            // Don't show loading animation for forms with the 'no-loading' class
            if (this.classList.contains('no-loading')) return;
            
            // Only show loading spinner on the button itself without full page transition
            const submitBtn = this.querySelector('button[type="submit"]');
            if (submitBtn) {
                const originalText = submitBtn.innerHTML;
                submitBtn.setAttribute('data-original-text', originalText);
                submitBtn.innerHTML = `
                    <span class="spinner-border spinner-border-sm me-2" role="status" aria-hidden="true"></span>
                    Processing...
                `;
                submitBtn.disabled = true;
            }
            
            // We don't call showPageTransition() anymore for regular form submissions
            // This avoids the full page transition, keeping only the button spinner
        });
    });
}

// Function to show page transition animation
function showPageTransition() {
    // Check if this is a form submission - if so, don't show transition
    // This is a more selective approach that only shows loading when needed
    
    // Check if user has seen the loading screen already (we store in sessionStorage)
    if (sessionStorage.getItem('loadingShown')) {
        // User has already seen the loading screen, don't show it again
        return;
    }
    
    // Only create the transition if it doesn't already exist
    if (!document.querySelector('.page-transition')) {
        const transition = document.createElement('div');
        transition.className = 'page-transition';
        transition.innerHTML = `
            <div class="xt-spinner">
                <div class="xt-spinner-logo">XT</div>
            </div>
        `;
        
        document.body.appendChild(transition);
        
        // Remove the transition after animation is complete
        setTimeout(function() {
            transition.classList.add('fade-out');
            setTimeout(function() {
                transition.remove();
            }, 500);
        }, 1500);
    }
}

// Function to create a notification
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `toast notification-pop align-items-center text-white bg-${type} border-0`;
    notification.setAttribute('role', 'alert');
    notification.setAttribute('aria-live', 'assertive');
    notification.setAttribute('aria-atomic', 'true');
    
    notification.innerHTML = `
        <div class="d-flex">
            <div class="toast-body">
                ${message}
            </div>
            <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
    `;
    
    const container = document.querySelector('.toast-container');
    if (!container) {
        const newContainer = document.createElement('div');
        newContainer.className = 'toast-container position-fixed bottom-0 end-0 p-3';
        document.body.appendChild(newContainer);
        newContainer.appendChild(notification);
    } else {
        container.appendChild(notification);
    }
    
    const toast = new bootstrap.Toast(notification);
    toast.show();
    
    notification.addEventListener('hidden.bs.toast', function() {
        notification.remove();
    });
}

// Function to show loading animation on specific element
function showElementLoading(element, message = 'Loading...') {
    if (!element) return;
    
    const originalContent = element.innerHTML;
    element.setAttribute('data-original-content', originalContent);
    
    element.innerHTML = `
        <div class="text-center p-3">
            <div class="discord-loading mb-2">
                <div></div>
                <div></div>
            </div>
            <p class="text-muted">${message}</p>
        </div>
    `;
    
    return function() {
        element.innerHTML = element.getAttribute('data-original-content');
    };
}

// Make functions available globally
window.showPageTransition = showPageTransition;
window.showNotification = showNotification;
window.showElementLoading = showElementLoading;