(function () {
    const header = document.querySelector('.site-header');
    if (!header) {
        return;
    }

    let lastScrollY = window.scrollY;
    const threshold = header.offsetHeight;

    const updateHeaderState = () => {
        const currentScroll = window.scrollY;
        const scrollingDown = currentScroll > lastScrollY;
        const scrollingUp = currentScroll < lastScrollY;

        if (currentScroll > 16) {
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
})();