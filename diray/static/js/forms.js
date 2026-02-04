// static/js/forms.js
// Form Validation and Handling System

class FormValidator {
    constructor(formId, options = {}) {
        this.form = document.getElementById(formId);
        if (!this.form) return;

        this.options = {
            realtime: true,
            showErrors: true,
            scrollToError: true,
            ...options
        };

        this.init();
    }

    init() {
        // Add validation attributes
        this.addValidationAttributes();

        // Add realtime validation
        if (this.options.realtime) {
            this.addRealtimeValidation();
        }

        // Handle form submission
        this.form.addEventListener('submit', this.handleSubmit.bind(this));
    }

    addValidationAttributes() {
        // Add required fields validation
        this.form.querySelectorAll('[required]').forEach(field => {
            if (!field.hasAttribute('aria-required')) {
                field.setAttribute('aria-required', 'true');
            }
        });

        // Add email validation pattern
        this.form.querySelectorAll('input[type="email"]').forEach(field => {
            if (!field.hasAttribute('pattern')) {
                field.setAttribute('pattern', '[a-z0-9._%+-]+@[a-z0-9.-]+\\.[a-z]{2,}$');
            }
        });

        // Add phone validation pattern
        this.form.querySelectorAll('input[type="tel"]').forEach(field => {
            if (!field.hasAttribute('pattern')) {
                field.setAttribute('pattern', '[+]?[0-9\\s-]{10,}');
            }
        });
    }

    addRealtimeValidation() {
        const fields = this.form.querySelectorAll('input, textarea, select');

        fields.forEach(field => {
            // Validate on blur
            field.addEventListener('blur', () => {
                this.validateField(field);
            });

            // Clear errors on focus
            field.addEventListener('focus', () => {
                this.clearFieldError(field);
            });

            // Real-time validation for specific fields
            if (field.type === 'email' || field.type === 'tel') {
                field.addEventListener('input', () => {
                    if (field.value.length > 3) {
                        this.validateField(field);
                    }
                });
            }
        });
    }

    validateField(field) {
        const value = field.value.trim();
        let isValid = true;
        let errorMessage = '';

        // Check required fields
        if (field.required && !value) {
            isValid = false;
            errorMessage = 'Ce champ est requis';
        }

        // Check email format
        if (field.type === 'email' && value) {
            const emailRegex = /^[a-z0-9._%+-]+@[a-z0-9.-]+\.[a-z]{2,}$/i;
            if (!emailRegex.test(value)) {
                isValid = false;
                errorMessage = 'Format email invalide';
            }
        }

        // Check phone format
        if (field.type === 'tel' && value) {
            const phoneRegex = /^[+]?[0-9\s-]{10,}$/;
            if (!phoneRegex.test(value.replace(/\s/g, ''))) {
                isValid = false;
                errorMessage = 'Format téléphone invalide';
            }
        }

        // Check pattern
        if (field.pattern && value) {
            const regex = new RegExp(field.pattern);
            if (!regex.test(value)) {
                isValid = false;
                errorMessage = field.dataset.errorMessage || 'Format invalide';
            }
        }

        // Check min/max length
        if (field.minLength && value.length < field.minLength) {
            isValid = false;
            errorMessage = `Minimum ${field.minLength} caractères`;
        }

        if (field.maxLength && value.length > field.maxLength) {
            isValid = false;
            errorMessage = `Maximum ${field.maxLength} caractères`;
        }

        // Update field state
        this.updateFieldState(field, isValid, errorMessage);

        return isValid;
    }

    updateFieldState(field, isValid, errorMessage = '') {
        // Remove existing error classes
        field.classList.remove('form-control-error');
        field.setAttribute('aria-invalid', 'false');

        // Remove existing error message
        const existingError = field.parentElement.querySelector('.form-error');
        if (existingError) {
            existingError.remove();
        }

        // Update field based on validation result
        if (!isValid && errorMessage && this.options.showErrors) {
            field.classList.add('form-control-error');
            field.setAttribute('aria-invalid', 'true');
            field.setAttribute('aria-describedby', `${field.id}-error`);

            // Create error message element
            const errorElement = document.createElement('div');
            errorElement.className = 'form-error';
            errorElement.id = `${field.id}-error`;
            errorElement.textContent = errorMessage;
            errorElement.setAttribute('role', 'alert');

            // Insert after field
            field.parentElement.appendChild(errorElement);

            // Focus the field if this is a submission error
            if (field.dataset.submitError === 'true') {
                field.focus();
                if (this.options.scrollToError) {
                    field.scrollIntoView({ behavior: 'smooth', block: 'center' });
                }
            }
        } else if (isValid && value) {
            // Add success visual feedback
            field.classList.add('form-control-success');
        }
    }

    clearFieldError(field) {
        field.classList.remove('form-control-error');
        field.removeAttribute('aria-invalid');
        field.removeAttribute('aria-describedby');

        const errorElement = field.parentElement.querySelector('.form-error');
        if (errorElement) {
            errorElement.remove();
        }

        // Remove submit error flag
        delete field.dataset.submitError;
    }

    validateForm() {
        let isValid = true;
        const fields = this.form.querySelectorAll('input, textarea, select');
        const firstInvalidField = null;

        fields.forEach(field => {
            const fieldValid = this.validateField(field);
            if (!fieldValid) {
                isValid = false;
                field.dataset.submitError = 'true';
                if (!firstInvalidField) {
                    firstInvalidField = field;
                }
            }
        });

        // Scroll to first invalid field
        if (!isValid && firstInvalidField && this.options.scrollToError) {
            firstInvalidField.focus();
            firstInvalidField.scrollIntoView({ behavior: 'smooth', block: 'center' });
        }

        return isValid;
    }

    async handleSubmit(event) {
        event.preventDefault();

        // Validate form
        if (!this.validateForm()) {
            return;
        }

        // Get form data
        const formData = new FormData(this.form);
        const data = Object.fromEntries(formData.entries());

        // Get form attributes
        const action = this.form.getAttribute('action') || window.location.pathname;
        const method = this.form.getAttribute('method') || 'POST';

        // Show loading state
        this.setLoadingState(true);

        try {
            // Send request
            const response = await fetch(action, {
                method: method,
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': this.getCSRFToken()
                },
                body: JSON.stringify(data)
            });

            const result = await response.json();

            if (result.success) {
                // Handle success
                this.handleSuccess(result);
            } else {
                // Handle error
                this.handleError(result);
            }
        } catch (error) {
            // Handle network error
            this.handleNetworkError(error);
        } finally {
            // Reset loading state
            this.setLoadingState(false);
        }
    }

    getCSRFToken() {
        return document.querySelector('[name=csrfmiddlewaretoken]')?.value || '';
    }

    setLoadingState(isLoading) {
        const submitButton = this.form.querySelector('button[type="submit"]');
        const allButtons = this.form.querySelectorAll('button');

        if (submitButton) {
            if (isLoading) {
                submitButton.disabled = true;
                submitButton.innerHTML = `
                    <span class="loader loader-sm"></span>
                    <span class="ml-2">Traitement...</span>
                `;
            } else {
                submitButton.disabled = false;
                submitButton.textContent = submitButton.dataset.originalText || 'Envoyer';
            }
        }

        allButtons.forEach(button => {
            if (button !== submitButton) {
                button.disabled = isLoading;
            }
        });
    }

    handleSuccess(result) {
        // Show success message
        if (window.showToast) {
            window.showToast('success', result.message || 'Formulaire envoyé avec succès');
        }

        // Reset form if needed
        if (this.options.resetOnSuccess) {
            this.form.reset();
            this.clearAllErrors();
        }

        // Call success callback
        if (this.options.onSuccess) {
            this.options.onSuccess(result);
        }

        // Scroll to top
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    handleError(result) {
        // Show error message
        if (window.showToast) {
            window.showToast('error', result.message || 'Une erreur est survenue');
        }

        // Handle field-specific errors
        if (result.errors) {
            Object.entries(result.errors).forEach(([fieldName, errors]) => {
                const field = this.form.querySelector(`[name="${fieldName}"]`);
                if (field) {
                    this.updateFieldState(field, false, errors.join(', '));
                    field.dataset.submitError = 'true';
                }
            });
        }

        // Call error callback
        if (this.options.onError) {
            this.options.onError(result);
        }
    }

    handleNetworkError(error) {
        // Show network error
        if (window.showToast) {
            window.showToast('error', 'Erreur de connexion. Veuillez réessayer.');
        }

        console.error('Network error:', error);
    }

    clearAllErrors() {
        this.form.querySelectorAll('.form-error').forEach(error => error.remove());
        this.form.querySelectorAll('.form-control-error').forEach(field => {
            field.classList.remove('form-control-error');
            field.removeAttribute('aria-invalid');
            field.removeAttribute('aria-describedby');
        });
    }
}

// Phone Input with Country Code
class PhoneInput {
    constructor(inputId, options = {}) {
        this.input = document.getElementById(inputId);
        if (!this.input) return;

        this.options = {
            defaultCountry: 'MA',
            preferredCountries: ['MA', 'FR', 'DZ', 'TN'],
            ...options
        };

        this.countryCode = '+212';
        this.init();
    }

    init() {
        // Create wrapper
        const wrapper = document.createElement('div');
        wrapper.className = 'phone-input-wrapper flex';

        // Create country selector
        this.createCountrySelector(wrapper);

        // Wrap the input
        this.input.parentNode.insertBefore(wrapper, this.input);
        wrapper.appendChild(this.input);

        // Set initial value
        this.updateInput();

        // Listen for input changes
        this.input.addEventListener('input', this.handleInput.bind(this));
    }

    createCountrySelector(wrapper) {
        const selector = document.createElement('div');
        selector.className = 'country-selector relative';

        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'flex items-center gap-2 px-3 border-r border-neutral-300 bg-neutral-50 text-neutral-700';
        button.innerHTML = `
            <span class="text-sm">${this.getCountryFlag(this.options.defaultCountry)}</span>
            <span class="text-sm">${this.countryCode}</span>
            <span class="material-symbols-outlined text-xs">expand_more</span>
        `;

        const dropdown = document.createElement('div');
        dropdown.className = 'country-dropdown absolute top-full left-0 mt-1 bg-white border border-neutral-200 rounded-lg shadow-xl z-50 hidden min-w-[200px]';

        // Add countries
        const countries = this.getCountries();
        countries.forEach(country => {
            const item = document.createElement('button');
            item.type = 'button';
            item.className = 'flex items-center gap-3 px-3 py-2 w-full hover:bg-neutral-50 text-left';
            item.innerHTML = `
                <span class="text-lg">${country.flag}</span>
                <span class="flex-1 text-sm">${country.name}</span>
                <span class="text-sm text-neutral-500">${country.code}</span>
            `;
            item.addEventListener('click', () => {
                this.selectCountry(country);
                button.innerHTML = `
                    <span class="text-sm">${country.flag}</span>
                    <span class="text-sm">${country.code}</span>
                    <span class="material-symbols-outlined text-xs">expand_more</span>
                `;
                dropdown.classList.add('hidden');
            });
            dropdown.appendChild(item);
        });

        button.addEventListener('click', () => {
            dropdown.classList.toggle('hidden');
        });

        selector.appendChild(button);
        selector.appendChild(dropdown);
        wrapper.appendChild(selector);

        // Close dropdown when clicking outside
        document.addEventListener('click', (event) => {
            if (!selector.contains(event.target)) {
                dropdown.classList.add('hidden');
            }
        });
    }

    getCountries() {
        return [
            { code: '+212', flag: '🇲🇦', name: 'Maroc', iso: 'MA' },
            { code: '+33', flag: '🇫🇷', name: 'France', iso: 'FR' },
            { code: '+213', flag: '🇩🇿', name: 'Algérie', iso: 'DZ' },
            { code: '+216', flag: '🇹🇳', name: 'Tunisie', iso: 'TN' },
            { code: '+1', flag: '🇺🇸', name: 'États-Unis', iso: 'US' },
            { code: '+44', flag: '🇬🇧', name: 'Royaume-Uni', iso: 'GB' },
            { code: '+49', flag: '🇩🇪', name: 'Allemagne', iso: 'DE' },
            { code: '+34', flag: '🇪🇸', name: 'Espagne', iso: 'ES' },
        ];
    }

    getCountryFlag(isoCode) {
        const countries = this.getCountries();
        const country = countries.find(c => c.iso === isoCode);
        return country ? country.flag : '🇺🇳';
    }

    selectCountry(country) {
        this.countryCode = country.code;
        this.updateInput();
    }

    handleInput() {
        // Remove non-numeric characters
        let value = this.input.value.replace(/\D/g, '');

        // Remove country code if already present
        if (value.startsWith(this.countryCode.replace('+', ''))) {
            value = value.slice(this.countryCode.replace('+', '').length);
        }

        // Update input value
        this.input.value = value;
    }

    updateInput() {
        // Get current number without country code
        let currentValue = this.input.value.replace(/\D/g, '');
        const countryCodeDigits = this.countryCode.replace('+', '');

        if (currentValue.startsWith(countryCodeDigits)) {
            currentValue = currentValue.slice(countryCodeDigits.length);
        }

        // Update placeholder
        this.input.placeholder = `${this.countryCode} XX XX XX XX`;

        // Format the value
        if (currentValue) {
            this.input.value = currentValue;
        }
    }

    getFullNumber() {
        const number = this.input.value.replace(/\D/g, '');
        return `${this.countryCode}${number}`;
    }
}

// City Autocomplete
class CityAutocomplete {
    constructor(inputId, options = {}) {
        this.input = document.getElementById(inputId);
        if (!this.input) return;

        this.options = {
            cities: [],
            minChars: 2,
            maxResults: 5,
            ...options
        };

        this.init();
    }

    async init() {
        // Load cities if not provided
        if (this.options.cities.length === 0) {
            await this.loadCities();
        }

        // Create dropdown
        this.createDropdown();

        // Add event listeners
        this.input.addEventListener('input', this.handleInput.bind(this));
        this.input.addEventListener('focus', this.handleFocus.bind(this));
        this.input.addEventListener('blur', this.handleBlur.bind(this));

        // Prevent form submission on enter when dropdown is open
        this.input.addEventListener('keydown', this.handleKeydown.bind(this));
    }

    async loadCities() {
        try {
            const response = await fetch('/api/cities/');
            const data = await response.json();
            this.options.cities = data.cities || [];
        } catch (error) {
            console.error('Error loading cities:', error);
            this.options.cities = [
                'Casablanca', 'Rabat', 'Tanger', 'Marrakech', 'Agadir',
                'Fès', 'Meknès', 'Oujda', 'Laâyoune', 'Dakhla'
            ];
        }
    }

    createDropdown() {
        this.dropdown = document.createElement('div');
        this.dropdown.className = 'city-autocomplete-dropdown absolute top-full left-0 right-0 bg-white border border-neutral-200 rounded-lg shadow-xl z-50 hidden max-h-60 overflow-y-auto';

        // Position relative to input
        const wrapper = document.createElement('div');
        wrapper.className = 'relative';
        this.input.parentNode.insertBefore(wrapper, this.input);
        wrapper.appendChild(this.input);
        wrapper.appendChild(this.dropdown);
    }

    handleInput() {
        const query = this.input.value.trim();

        if (query.length >= this.options.minChars) {
            this.showResults(query);
        } else {
            this.hideDropdown();
        }
    }

    handleFocus() {
        const query = this.input.value.trim();
        if (query.length >= this.options.minChars) {
            this.showResults(query);
        }
    }

    handleBlur() {
        // Hide dropdown after a delay to allow click
        setTimeout(() => {
            if (!this.dropdown.contains(document.activeElement)) {
                this.hideDropdown();
            }
        }, 200);
    }

    handleKeydown(event) {
        const items = this.dropdown.querySelectorAll('.city-item');
        let currentIndex = -1;

        items.forEach((item, index) => {
            if (item.classList.contains('active')) {
                currentIndex = index;
            }
        });

        switch (event.key) {
            case 'ArrowDown':
                event.preventDefault();
                this.navigateDropdown(currentIndex + 1, items);
                break;

            case 'ArrowUp':
                event.preventDefault();
                this.navigateDropdown(currentIndex - 1, items);
                break;

            case 'Enter':
                if (currentIndex >= 0) {
                    event.preventDefault();
                    items[currentIndex].click();
                }
                break;

            case 'Escape':
                this.hideDropdown();
                break;
        }
    }

    navigateDropdown(newIndex, items) {
        // Remove active class from all items
        items.forEach(item => item.classList.remove('active'));

        // Validate index bounds
        if (newIndex < 0) newIndex = items.length - 1;
        if (newIndex >= items.length) newIndex = 0;

        // Add active class to new item
        if (items[newIndex]) {
            items[newIndex].classList.add('active');
            items[newIndex].scrollIntoView({ block: 'nearest' });
        }
    }

    showResults(query) {
        const results = this.filterCities(query);

        if (results.length > 0) {
            this.dropdown.innerHTML = '';

            results.forEach(city => {
                const item = document.createElement('button');
                item.type = 'button';
                item.className = 'city-item flex items-center gap-3 px-4 py-3 w-full hover:bg-neutral-50 text-left';
                item.innerHTML = `
                    <span class="material-symbols-outlined text-neutral-400">location_on</span>
                    <span class="flex-1">${city}</span>
                `;

                item.addEventListener('click', () => {
                    this.selectCity(city);
                });

                this.dropdown.appendChild(item);
            });

            this.dropdown.classList.remove('hidden');
        } else {
            this.hideDropdown();
        }
    }

    filterCities(query) {
        const lowerQuery = query.toLowerCase();
        return this.options.cities
            .filter(city => city.toLowerCase().includes(lowerQuery))
            .slice(0, this.options.maxResults);
    }

    selectCity(city) {
        this.input.value = city;
        this.hideDropdown();

        // Trigger change event
        this.input.dispatchEvent(new Event('change', { bubbles: true }));
    }

    hideDropdown() {
        this.dropdown.classList.add('hidden');
        this.dropdown.innerHTML = '';
    }
}

// Form State Manager
class FormStateManager {
    constructor(formId) {
        this.form = document.getElementById(formId);
        if (!this.form) return;

        this.stateKey = `form_state_${formId}`;
        this.init();
    }

    init() {
        // Load saved state
        this.loadState();

        // Save state on input
        this.form.addEventListener('input', this.debounce(this.saveState.bind(this), 500));

        // Clear state on successful submission
        this.form.addEventListener('submit', () => {
            setTimeout(() => {
                if (!this.form.querySelector('.form-error')) {
                    this.clearState();
                }
            }, 1000);
        });

        // Clear state before unload if form is empty
        window.addEventListener('beforeunload', () => {
            if (this.isFormEmpty()) {
                this.clearState();
            }
        });
    }

    saveState() {
        const formData = new FormData(this.form);
        const state = {};

        formData.forEach((value, key) => {
            state[key] = value;
        });

        localStorage.setItem(this.stateKey, JSON.stringify(state));
    }

    loadState() {
        const savedState = localStorage.getItem(this.stateKey);
        if (!savedState) return;

        try {
            const state = JSON.parse(savedState);

            Object.entries(state).forEach(([key, value]) => {
                const field = this.form.querySelector(`[name="${key}"]`);
                if (field && !field.value) {
                    field.value = value;

                    // Trigger change event
                    field.dispatchEvent(new Event('change', { bubbles: true }));
                }
            });
        } catch (error) {
            console.error('Error loading form state:', error);
        }
    }

    clearState() {
        localStorage.removeItem(this.stateKey);
    }

    isFormEmpty() {
        const formData = new FormData(this.form);
        for (let value of formData.values()) {
            if (value) return false;
        }
        return true;
    }

    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Initialize all forms on page load
document.addEventListener('DOMContentLoaded', function () {
    // Initialize form validators
    document.querySelectorAll('form[data-validate]').forEach(form => {
        new FormValidator(form.id, {
            realtime: true,
            showErrors: true,
            scrollToError: true
        });
    });

    // Initialize phone inputs
    document.querySelectorAll('input[type="tel"][data-phone-input]').forEach(input => {
        new PhoneInput(input.id);
    });

    // Initialize city autocomplete
    document.querySelectorAll('input[data-city-autocomplete]').forEach(input => {
        new CityAutocomplete(input.id);
    });

    // Initialize form state managers
    document.querySelectorAll('form[id]').forEach(form => {
        new FormStateManager(form.id);
    });

    // Auto-fill forms for logged-in users
    autoFillForms();
});

function autoFillForms() {
    if (!window.currentUser || !window.currentUser.isAuthenticated || !window.currentUser.data) {
        return;
    }

    const userData = window.currentUser.data;

    // Fields to map (field name -> user data key)
    const fieldMap = {
        'full_name': 'full_name',
        'email': 'email',
        'phone': 'phone',
        'city': 'city',
        'name': 'full_name' // sometimes just 'name' is used
    };

    document.querySelectorAll('form').forEach(form => {
        Object.entries(fieldMap).forEach(([fieldName, dataKey]) => {
            const field = form.querySelector(`[name="${fieldName}"]`);
            // Only fill if field exists and is empty
            if (field && !field.value && userData[dataKey]) {
                field.value = userData[dataKey];
                // Trigger change event so generic form logic picks it up (e.g. valid styling)
                field.dispatchEvent(new Event('input', { bubbles: true }));
                field.dispatchEvent(new Event('change', { bubbles: true }));
            }
        });
    });
} document.querySelectorAll('form[data-save-state]').forEach(form => {
    new FormStateManager(form.id);
});
});

// Export for global use
window.FormValidator = FormValidator;
window.PhoneInput = PhoneInput;
window.CityAutocomplete = CityAutocomplete;
window.FormStateManager = FormStateManager;