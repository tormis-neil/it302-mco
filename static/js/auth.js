const REQUIREMENTS = [
  {
    key: 'length',
    test: (value) => value.length >= 8,
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

const STRENGTH_LEVELS = [
  { threshold: 0, label: 'Strength: Too weak', color: '#d14343' },
  { threshold: 2, label: 'Strength: Fair', color: '#f4a259' },
  { threshold: 3, label: 'Strength: Good', color: '#f7d154' },
  { threshold: 4, label: 'Strength: Strong', color: '#2ecc71' },
];

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

function updateRequirementIndicators(form, password) {
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

function validateUsername(value) {
  if (!value.trim()) return 'Username is required.';
  if (!/^[A-Za-z0-9._-]{3,30}$/.test(value.trim())) {
    return 'Use 3-30 characters with letters, numbers, or ._- only.';
  }
  return '';
}

function validateEmail(value) {
  if (!value.trim()) return 'Email is required.';
  const emailPattern = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
  if (!emailPattern.test(value.trim())) {
    return 'Enter a valid email address.';
  }
  return '';
}

function validatePassword(password) {
  const { score } = evaluateStrength(password);
  if (!password) return 'Password is required.';
  if (score < REQUIREMENTS.length) {
    return 'Password does not meet all requirements yet.';
  }
  return '';
}

function validateConfirm(password, confirm) {
  if (!confirm) return 'Confirm your password.';
  if (password !== confirm) return 'Passwords do not match.';
  return '';
}

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

function init() {
  setupSignupForm();
  setupLoginForm();
}

document.addEventListener('DOMContentLoaded', init);