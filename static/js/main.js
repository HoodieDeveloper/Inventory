document.addEventListener('DOMContentLoaded', () => {
    const navToggle = document.querySelector('.nav-toggle');
    const navMobile = document.querySelector('.nav-mobile');
    const passwordToggles = document.querySelectorAll('.toggle-password');
    const searchInput = document.querySelector('#productSearch');
    const productCards = document.querySelectorAll('.product-card');
    const emptyState = document.querySelector('#emptySearchState');
    const paymentInputs = document.querySelectorAll('input[name="payment_method"]');
    const paymentCards = document.querySelectorAll('[data-payment-card]');
    const qrPreview = document.querySelector('#qrPreview');
    const cashPreview = document.querySelector('#cashPreview');

    if (navToggle && navMobile) {
        navToggle.addEventListener('click', () => {
            navMobile.classList.toggle('hidden');
            const expanded = navToggle.getAttribute('aria-expanded') === 'true';
            navToggle.setAttribute('aria-expanded', String(!expanded));
        });
    }

    passwordToggles.forEach((toggleButton) => {
        toggleButton.addEventListener('click', () => {
            const input = document.getElementById(toggleButton.dataset.target);
            if (!input) return;
            const isPassword = input.getAttribute('type') === 'password';
            input.setAttribute('type', isPassword ? 'text' : 'password');
            toggleButton.textContent = isPassword ? 'Hide' : 'Show';
        });
    });

    if (searchInput && productCards.length) {
        searchInput.addEventListener('input', (event) => {
            const value = event.target.value.trim().toLowerCase();
            let visibleCount = 0;

            productCards.forEach((card) => {
                const name = card.dataset.name || '';
                const category = card.dataset.category || '';
                const matches = name.includes(value) || category.includes(value);
                card.classList.toggle('hidden', !matches);
                if (matches) visibleCount += 1;
            });

            if (emptyState) {
                emptyState.classList.toggle('hidden', visibleCount !== 0);
            }
        });
    }

    const syncPaymentState = () => {
        const selected = document.querySelector('input[name="payment_method"]:checked');
        const isQr = selected && selected.value === 'qr';

        paymentCards.forEach((card) => {
            const input = card.querySelector('input[name="payment_method"]');
            const active = input && input.checked;
            card.classList.toggle('border-blue-300', active);
            card.classList.toggle('bg-blue-50', active);
            card.classList.toggle('ring-4', active);
            card.classList.toggle('ring-blue-100', active);
        });

        if (qrPreview) qrPreview.classList.toggle('hidden', !isQr);
        if (cashPreview) cashPreview.classList.toggle('hidden', !!isQr);
    };

    paymentInputs.forEach((input) => input.addEventListener('change', syncPaymentState));
    if (paymentInputs.length) syncPaymentState();
});
