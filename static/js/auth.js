/**
 * Authentication form validation and password strength module
 * Handles client-side validation for login and signup forms
 */

/**
 * Password validation requirements configuration
 * @type {Array<{key: string, test: function(string): boolean}>}
 */
const REQUIREMENTS = [
  {
    key: 'length',
    test: (value) => value.length >= 12,
  },
  {
    key: 'uppercase',
    test: (value) => /[A-Z]/.test(value),
  },
  {
    key: 'number',
    test: (value) => /\d/.test(value),
  },
  {
    key: 'special',
    test: (value) => /[!@#$%^&*]/.test(value),
  },
];

/**
 * Password strength levels with thresholds and visual styling
 * @type {Array<{threshold: number, label: string, color: string}>}
 */
const STRENGTH_LEVELS = [
  { threshold: 0, label: 'Strength: Too weak', color: '#d14343' },
  { threshold: 2, label: 'Strength: Fair', color: '#f4a259' },
  { threshold: 3, label: 'Strength: Good', color: '#f7d154' },
  { threshold: 4, label: 'Strength: Strong', color: '#2ecc71' },
];

/**
 * Evaluates password strength based on requirements
 * @param {string} value - The password to evaluate
 * @returns {{score: number, level: {threshold: number, label: string, color: string}}}
 */
function evaluateStrength(value) {
  let score = 0;
  for (const requirement of REQUIREMENTS) {
    if (requirement.test(value)) {
      score += 1;
    }
  }

  let level = STRENGTH_LEVELS[0];
  for (const candidate of STRENGTH_LEVELS) {
    if (score >= candidate.threshold) {
      level = candidate;
    }
  }

  return { score, level };
}

/**
 * Updates password strength indicators and requirement checkmarks in the UI
 * @param {HTMLFormElement} form - The signup form element
 * @param {string} password - The password value to evaluate
 * @returns {{score: number, level: object}} The evaluation result
 */
function updateRequirementIndicators(form, password) {
  if (!form) {
    console.warn('updateRequirementIndicators: form element is null');
    return { score: 0, level: STRENGTH_LEVELS[0] };
  }

  const result = evaluateStrength(password);
  const { level, score } = result;

  const bar = form.querySelector('[data-strength-bar]');
  const label = form.querySelector('[data-strength-label]');

  if (bar) {
    bar.style.width = `${(score / REQUIREMENTS.length) * 100}%`;
    bar.style.backgroundColor = level.color;
  }

  if (label) {
    label.textContent = level.label;
    label.style.color = level.color;
  }

  for (const requirement of REQUIREMENTS) {
    const item = form.querySelector(`[data-requirement="${requirement.key}"]`);
    if (!item) continue;
    const isValid = requirement.test(password);
    item.dataset.valid = String(isValid);
  }

  return result;
}

/**
 * Displays or hides field error messages
 * @param {HTMLFormElement} form - The form containing the field
 * @param {string} field - The field identifier (matches data-field-error attribute)
 * @param {string} message - Error message to display (empty string to clear)
 */
function setFieldError(form, field, message) {
  const errorElement = form.querySelector(`[data-field-error="${field}"]`);
  if (!errorElement) return;
  if (message) {
    errorElement.textContent = message;
    errorElement.hidden = false;
  } else {
    errorElement.textContent = '';
    errorElement.hidden = true;
  }
}

/**
 * Validates username format
 * @param {string} value - Username to validate
 * @returns {string} Error message or empty string if valid
 */
function validateUsername(value) {
  if (!value.trim()) return 'Username is required.';
  if (!/^[A-Za-z0-9._-]{3,30}$/.test(value.trim())) {
    return 'Use 3-30 characters with letters, numbers, or ._- only.';
  }
  return '';
}

/**
 * Validates email format
 * @param {string} value - Email to validate
 * @returns {string} Error message or empty string if valid
 */
function validateEmail(value) {
  if (!value.trim()) return 'Email is required.';
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailPattern.test(value.trim())) {
    return 'Enter a valid email address.';
  }
  return '';
}

/**
 * Validates password meets all requirements
 * @param {string} password - Password to validate
 * @returns {string} Error message or empty string if valid
 */
function validatePassword(password) {
  const { score } = evaluateStrength(password);
  if (!password) return 'Password is required.';
  if (score < REQUIREMENTS.length) {
    return 'Password does not meet all requirements yet.';
  }
  return '';
}

/**
 * Validates password confirmation matches
 * @param {string} password - Original password
 * @param {string} confirm - Confirmation password
 * @returns {string} Error message or empty string if valid
 */
function validateConfirm(password, confirm) {
  if (!confirm) return 'Confirm your password.';
  if (password !== confirm) return 'Passwords do not match.';
  return '';
}

/**
 * Initializes signup form validation and password strength indicators
 */
function setupSignupForm() {
  const form = document.querySelector('[data-signup-form]');
  if (!form) return;

  const username = form.querySelector('#su-username');
  const email = form.querySelector('#su-email');
  const password = form.querySelector('#su-password');
  const confirm = form.querySelector('#su-confirm');

  password?.addEventListener('input', () => {
    updateRequirementIndicators(form, password.value);
    setFieldError(form, 'password', '');
    if (confirm?.value) {
      setFieldError(form, 'confirm', password.value === confirm.value ? '' : 'Passwords do not match.');
    }
  });

  confirm?.addEventListener('input', () => {
    if (!password) return;
    setFieldError(form, 'confirm', password.value === confirm.value ? '' : 'Passwords do not match.');
  });

  username?.addEventListener('blur', () => {
    setFieldError(form, 'username', validateUsername(username.value));
  });

  email?.addEventListener('blur', () => {
    setFieldError(form, 'email', validateEmail(email.value));
  });

  form.addEventListener('submit', (event) => {
    let hasError = false;

    if (username) {
      const message = validateUsername(username.value);
      setFieldError(form, 'username', message);
      hasError ||= Boolean(message);
    }

    if (email) {
      const message = validateEmail(email.value);
      setFieldError(form, 'email', message);
      hasError ||= Boolean(message);
    }

    if (password) {
      const message = validatePassword(password.value);
      setFieldError(form, 'password', message);
      hasError ||= Boolean(message);
    }

    if (password && confirm) {
      const message = validateConfirm(password.value, confirm.value);
      setFieldError(form, 'confirm', message);
      hasError ||= Boolean(message);
    }

    if (hasError) {
      event.preventDefault();
      form.querySelector('.auth-input')?.focus();
    }
  });

  // Seed the indicator on first render.
  updateRequirementIndicators(form, password?.value ?? '');
}

/**
 * Initializes login form validation
 */
function setupLoginForm() {
  const form = document.querySelector('[data-login-form]');
  if (!form) return;
  const alertBox = document.querySelector('[data-auth-alert]');

  form.addEventListener('submit', (event) => {
    const identifier = form.querySelector('#login-identifier');
    const password = form.querySelector('#login-password');
    const missingIdentifier = !identifier?.value.trim();
    const missingPassword = !password?.value.trim();

    if (missingIdentifier || missingPassword) {
      event.preventDefault();
      if (alertBox) {
        alertBox.textContent = 'Enter your username/email and password to continue.';
        alertBox.hidden = false;
      }
      identifier?.focus();
      return;
    }

    if (alertBox) {
      alertBox.hidden = true;
    }
  });
}

/**
 * Initializes all authentication form handlers
 */
function init() {
  try {
    setupSignupForm();
    setupLoginForm();
  } catch (error) {
    console.error('Error initializing authentication forms:', error);
  }
}

document.addEventListener('DOMContentLoaded', init);