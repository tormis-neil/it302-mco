/**
 * Navbar scroll behavior module
 * Handles header condensing and auto-hide on scroll
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

        /**
         * Updates header state based on scroll position and direction
         * - Adds 'is-condensed' class when scrolled past threshold
         * - Adds 'is-hidden' class when scrolling down
         * - Removes 'is-hidden' when scrolling up or at top
         */
        const updateHeaderState = () => {
            const currentScroll = window.scrollY;
            const scrollingDown = currentScroll > lastScrollY;
            const scrollingUp = currentScroll < lastScrollY;

            if (currentScroll > CONDENSE_THRESHOLD) {
                header.classList.add('is-condensed');
            } else {
                header.classList.remove('is-condensed');
            }

            if (scrollingDown && currentScroll > threshold) {
                header.classList.add('is-hidden');
            } else if (scrollingUp || currentScroll <= threshold) {
                header.classList.remove('is-hidden');
            }

            lastScrollY = currentScroll;
        };

        window.addEventListener('scroll', updateHeaderState, { passive: true });
        updateHeaderState();
    } catch (error) {
        console.error('Error initializing navbar scroll behavior:', error);
    }
})();