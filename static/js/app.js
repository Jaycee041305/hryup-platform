document.addEventListener('DOMContentLoaded', function() {
    // Sidebar Toggle
    const sidebarToggle = document.getElementById('sidebarToggle');
    const sidebar = document.querySelector('.sidebar');
    const overlay = document.querySelector('.sidebar-overlay');
    
    if (sidebarToggle && sidebar) {
        sidebarToggle.addEventListener('click', function(e) {
            e.preventDefault();
            sidebar.classList.toggle('show');
            if (overlay) {
                overlay.classList.toggle('show');
            }
        });
    }

    if (overlay) {
        overlay.addEventListener('click', function() {
            sidebar.classList.remove('show');
            overlay.classList.remove('show');
        });
    }

    // Auto-dismiss alerts
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(function(alert) {
        setTimeout(function() {
            const bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        }, 5000);
    });

    // Auto-dismiss toasts
    const toasts = document.querySelectorAll('.toast');
    toasts.forEach(function(toastEl) {
        const toast = new bootstrap.Toast(toastEl, { delay: 5000 });
        toast.show();
    });

    // Confirm Modal Trigger
    const confirmTriggers = document.querySelectorAll('[data-bs-confirm]');
    const confirmModalEl = document.getElementById('confirmModal');
    
    if (confirmModalEl) {
        const confirmModal = new bootstrap.Modal(confirmModalEl);
        confirmTriggers.forEach(function(trigger) {
            trigger.addEventListener('click', function(e) {
                e.preventDefault();
                const title = this.getAttribute('data-confirm-title') || 'Confirm Action';
                const message = this.getAttribute('data-confirm-message') || 'Are you sure you want to proceed?';
                const href = this.getAttribute('href');
                const formId = this.getAttribute('data-confirm-form');
                
                document.getElementById('confirmModalTitle').textContent = title;
                document.getElementById('confirmModalBody').textContent = message;
                
                const confirmBtn = document.getElementById('confirmModalBtn');
                confirmBtn.onclick = function() {
                    if (formId) {
                        document.getElementById(formId).submit();
                    } else if (href) {
                        window.location.href = href;
                    }
                    confirmModal.hide();
                };
                
                confirmModal.show();
            });
        });
    }

    // Active sidebar link highlighting
    const currentPath = window.location.pathname;
    const navLinks = document.querySelectorAll('.sidebar-nav-item');
    navLinks.forEach(link => {
        const href = link.getAttribute('href');
        if (href && href !== '#' && currentPath.startsWith(href)) {
            link.classList.add('active');
        }
    });

    // File upload preview
    const fileInputs = document.querySelectorAll('.custom-file-input');
    fileInputs.forEach(input => {
        input.addEventListener('change', function(e) {
            const fileName = e.target.files[0] ? e.target.files[0].name : 'Choose file';
            const label = this.nextElementSibling;
            if (label && label.classList.contains('custom-file-label')) {
                label.textContent = fileName;
            }
        });
    });
});

// CSRF token helper
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
