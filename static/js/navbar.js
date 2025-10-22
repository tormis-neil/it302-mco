/**
 * Navbar scroll behavior module
 * Handles header condensing and auto-hide on scroll
 * Includes focus management for accessibility
 */
(function () {
    try {
        const header = document.querySelector('.site-header');
        if (!header) {
            console.warn('Navbar: .site-header element not found');
            return;
        }

        /** Minimum scroll distance to trigger condensed state */
        const CONDENSE_THRESHOLD = 16;

        let lastScrollY = window.scrollY;
        const threshold = header.offsetHeight;
        let headerHasFocus = false;

        /**
         * Checks if the header or any of its children currently have focus
         * @returns {boolean} True if header contains focused element
         */
        const checkHeaderFocus = () => {
            return header.contains(document.activeElement);
        };

        /**
         * Updates header state based on scroll position and direction
         * - Adds 'is-condensed' class when scrolled past threshold
         * - Adds 'is-hidden' class when scrolling down (unless header has focus)
         * - Removes 'is-hidden' when scrolling up or at top
         */
        const updateHeaderState = () => {
            const currentScroll = window.scrollY;
            const scrollingDown = currentScroll > lastScrollY;
            const scrollingUp = currentScroll < lastScrollY;
            headerHasFocus = checkHeaderFocus();

            if (currentScroll > CONDENSE_THRESHOLD) {
                header.classList.add('is-condensed');
            } else {
                header.classList.remove('is-condensed');
            }

            // Don't hide header if it has focus (for keyboard navigation)
            if (scrollingDown && currentScroll > threshold && !headerHasFocus) {
                header.classList.add('is-hidden');
            } else if (scrollingUp || currentScroll <= threshold || headerHasFocus) {
                header.classList.remove('is-hidden');
            }

            lastScrollY = currentScroll;
        };

        // Show header when any element inside it receives focus
        header.addEventListener('focusin', () => {
            header.classList.remove('is-hidden');
        });

        window.addEventListener('scroll', updateHeaderState, { passive: true });
        updateHeaderState();
    } catch (error) {
        console.error('Error initializing navbar scroll behavior:', error);
    }
})();