// Main script for Discord Selfbot Manager

document.addEventListener('DOMContentLoaded', function() {
    // Initialize tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    var tooltipList = tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Handle token visibility toggle
    const tokenToggleBtns = document.querySelectorAll('.toggle-token-visibility');
    tokenToggleBtns.forEach(btn => {
        btn.addEventListener('click', function() {
            const tokenElement = this.closest('tr').querySelector('.token-value');
            const isHidden = tokenElement.textContent.includes('*');
            
            if (isHidden) {
                tokenElement.textContent = tokenElement.dataset.token;
                this.innerHTML = '<i class="fas fa-eye-slash"></i>';
                this.setAttribute('title', 'Hide Token');
                // Auto-hide after 10 seconds
                setTimeout(() => {
                    tokenElement.textContent = tokenElement.dataset.token.substring(0, 10) + '*****';
                    this.innerHTML = '<i class="fas fa-eye"></i>';
                    this.setAttribute('title', 'Show Token');
                }, 10000);
            } else {
                tokenElement.textContent = tokenElement.dataset.token.substring(0, 10) + '*****';
                this.innerHTML = '<i class="fas fa-eye"></i>';
                this.setAttribute('title', 'Show Token');
            }
        });
    });

    // Confirmation for token deletion
    const deleteTokenForms = document.querySelectorAll('.delete-token-form');
    deleteTokenForms.forEach(form => {
        form.addEventListener('submit', function(e) {
            if (!confirm('Are you sure you want to delete this token?')) {
                e.preventDefault();
            }
        });
    });

    // Copy script path to clipboard
    const copyScriptPathBtn = document.getElementById('copy-script-path');
    if (copyScriptPathBtn) {
        copyScriptPathBtn.addEventListener('click', function() {
            const scriptPath = this.dataset.path;
            navigator.clipboard.writeText(scriptPath).then(() => {
                // Show success message
                const originalText = this.textContent;
                this.textContent = 'Copied!';
                setTimeout(() => {
                    this.textContent = originalText;
                }, 2000);
            });
        });
    }

    // Animate heading on homepage
    const mainHeading = document.querySelector('.display-4');
    if (mainHeading && window.location.pathname === '/') {
        mainHeading.classList.add('animate__animated', 'animate__fadeInDown');
    }
});
