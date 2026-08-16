// main.js — students will add JavaScript here as features are built

// Modal functionality for "See how it works"
(function() {
    'use strict';

    const modal = document.getElementById('demo-modal');
    const triggers = document.querySelectorAll('[data-modal="demo-modal"]');
    const closeBtn = modal?.querySelector('.modal-close');
    const iframe = modal?.querySelector('.modal-video');

    function openModal() {
        if (!modal) return;
        modal.hidden = false;
        // Force reflow for animation
        modal.offsetHeight;
        document.body.style.overflow = 'hidden';
    }

    function closeModal() {
        if (!modal) return;
        modal.hidden = true;
        document.body.style.overflow = '';

        // Stop the video by resetting the iframe src
        if (iframe) {
            const src = iframe.src;
            iframe.src = '';
            iframe.src = src;
        }
    }

    // Open modal on trigger click
    triggers.forEach(trigger => {
        trigger.addEventListener('click', (e) => {
            e.preventDefault();
            openModal();
        });
    });

    // Close on close button click
    if (closeBtn) {
        closeBtn.addEventListener('click', closeModal);
    }

    // Close on overlay click (outside modal)
    if (modal) {
        modal.addEventListener('click', (e) => {
            if (e.target === modal) {
                closeModal();
            }
        });
    }

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
        if (e.key === 'Escape' && modal && !modal.hidden) {
            closeModal();
        }
    });
})();