const MENU_SELECTOR = '[data-menu]';
const BUTTON_SELECTOR = '[data-category-trigger]';
const PANEL_SELECTOR = '[data-category-panel]';

function activateCategory(panels, buttons, slug) {
  buttons.forEach((button) => {
    const isActive = button.dataset.target === slug;
    button.dataset.active = String(isActive);
    button.setAttribute('aria-selected', String(isActive));
    button.setAttribute('tabindex', isActive ? '0' : '-1');
  });

  panels.forEach((panel) => {
    const isActive = panel.id === slug;
    panel.toggleAttribute('hidden', !isActive);
    panel.dataset.active = String(isActive);
  });
}

function setupMenuTabs() {
  const menuRoot = document.querySelector(MENU_SELECTOR);
  if (!menuRoot) return;

  const panels = menuRoot.querySelectorAll(PANEL_SELECTOR);
  const buttons = document.querySelectorAll(BUTTON_SELECTOR);
  if (!buttons.length || !panels.length) return;

  const defaultSlug = menuRoot.dataset.defaultCategory || buttons[0].dataset.target;

  buttons.forEach((button) => {
    button.addEventListener('click', () => {
      activateCategory(panels, buttons, button.dataset.target);
      button.focus();
    });

    button.addEventListener('keydown', (event) => {
      if (event.key !== 'Enter' && event.key !== ' ') {
        return;
      }
      event.preventDefault();
      activateCategory(panels, buttons, button.dataset.target);
    });
  });

  if (defaultSlug) {
    activateCategory(panels, buttons, defaultSlug);
  }
}

document.addEventListener('DOMContentLoaded', setupMenuTabs);