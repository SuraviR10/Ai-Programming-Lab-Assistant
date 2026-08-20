/* ═══════════════════════════════════════════════════════════════
   AI Programming Lab — Toast Notifications (toast.js)
   Reusable notification system
   ═══════════════════════════════════════════════════════════════ */

const Toast = (() => {
  let container = null;
  const DURATION = 4000;
  const MAX_TOASTS = 5;

  // ── Initialize container ────────────────────────────────────
  function init() {
    if (container) return;
    container = document.createElement('div');
    container.className = 'toast-container';
    container.setAttribute('aria-live', 'polite');
    container.setAttribute('role', 'status');
    document.body.appendChild(container);
  }

  // ── Icons ───────────────────────────────────────────────────
  const icons = {
    success: '✓',
    error: '!',
    warning: '⚠',
    info: '✦',
    achievement: '★',
  };

  // ── Show toast ──────────────────────────────────────────────
  function show(message, type = 'info', duration = DURATION) {
    init();

    // Limit active toasts
    while (container.children.length >= MAX_TOASTS) {
      const oldest = container.firstChild;
      if (oldest) remove(oldest);
    }

    const toast = document.createElement('div');
    toast.className = `toast toast-${type}`;
    toast.innerHTML = `
      <span style="font-size: 16px; flex-shrink: 0;">${icons[type] || '✦'}</span>
      <span style="flex: 1;">${message}</span>
    `;

    container.appendChild(toast);

    // Trigger animation
    requestAnimationFrame(() => {
      toast.classList.add('toast-enter');
    });

    // Auto-dismiss
    const timer = setTimeout(() => remove(toast), duration);

    // Click to dismiss
    toast.addEventListener('click', () => {
      clearTimeout(timer);
      remove(toast);
    });

    return toast;
  }

  // ── Remove toast ────────────────────────────────────────────
  function remove(toast) {
    if (!toast || !toast.parentNode) return;
    toast.classList.remove('toast-enter');
    toast.classList.add('toast-exit');
    toast.addEventListener('animationend', () => {
      if (toast.parentNode) toast.parentNode.removeChild(toast);
    }, { once: true });
  }

  // ── Convenience Methods ─────────────────────────────────────
  function success(msg, duration) { return show(msg, 'success', duration); }
  function error(msg, duration)   { return show(msg, 'error', duration); }
  function warning(msg, duration) { return show(msg, 'warning', duration); }
  function info(msg, duration)    { return show(msg, 'info', duration); }
  function achievement(msg)       { return show(msg, 'achievement', 5000); }

  return { show, success, error, warning, info, achievement };
})();
