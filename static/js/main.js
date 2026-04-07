document.addEventListener('DOMContentLoaded', () => {
    const navToggle = document.querySelector('.nav-toggle');
    const navMenu = document.querySelector('.nav-menu');
    const passwordToggles = document.querySelectorAll('.toggle-password');
    const searchInput = document.querySelector('#productSearch');
    const productCards = document.querySelectorAll('.product-card');
    const emptyState = document.querySelector('#emptySearchState');
    const paymentInputs = document.querySelectorAll('input[name="payment_method"]');
    const qrPreview = document.querySelector('#qrPreview');
    const cashPreview = document.querySelector('#cashPreview');
    const revealItems = document.querySelectorAll('[data-reveal]');

    if (navToggle && navMenu) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('open');
        });
    }

    if (passwordToggles.length) {
        passwordToggles.forEach((toggleButton) => {
            toggleButton.addEventListener('click', () => {
                const input = document.getElementById(toggleButton.dataset.target);
                if (!input) return;
                const isPassword = input.getAttribute('type') === 'password';
                input.setAttribute('type', isPassword ? 'text' : 'password');
                toggleButton.textContent = isPassword ? 'Hide' : 'Show';
            });
        });
    }

    if (searchInput && productCards.length) {
        searchInput.addEventListener('input', (event) => {
            const value = event.target.value.trim().toLowerCase();
            let visibleCount = 0;

            productCards.forEach((card) => {
                const name = card.dataset.name || '';
                const category = card.dataset.category || '';
                const matches = name.includes(value) || category.includes(value);
                card.style.display = matches ? '' : 'none';
                if (matches) visibleCount += 1;
            });

            if (emptyState) {
                emptyState.classList.toggle('hidden', visibleCount !== 0);
            }
        });
    }

    const syncPaymentState = () => {
        if (!paymentInputs.length) return;
        const selected = document.querySelector('input[name="payment_method"]:checked');
        const isQr = selected && selected.value === 'qr';

        paymentInputs.forEach((input) => {
            const label = input.closest('label');
            if (!label) return;
            label.classList.toggle('radio-card-active', input.checked);
        });

        if (qrPreview) {
            qrPreview.classList.toggle('hidden', !isQr);
        }
        if (cashPreview) {
            cashPreview.classList.toggle('hidden', !!isQr);
        }
    };

    if (paymentInputs.length) {
        paymentInputs.forEach((input) => {
            input.addEventListener('change', syncPaymentState);
        });
        syncPaymentState();
    }

    if (revealItems.length) {
        const revealObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach((entry) => {
                if (!entry.isIntersecting) return;
                entry.target.classList.add('revealed');
                observer.unobserve(entry.target);
            });
        }, {
            threshold: 0.14,
            rootMargin: '0px 0px -40px 0px'
        });

        revealItems.forEach((item) => revealObserver.observe(item));
    }
});
