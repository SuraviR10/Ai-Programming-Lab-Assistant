/* ═══════════════════════════════════════════════════════════════
   SMART LAB — Focus Fullscreen Controller (fullscreen.js)
   Enforces distraction-free fullscreen mode during lab sessions
   and provides safe exit-to-home navigation.
   ═══════════════════════════════════════════════════════════════ */

const FocusFullscreen = (() => {
  let isFullscreenActive = false;
  let hasUserExplicitlyExited = false;

  function isFullscreen() {
    return !!(
      document.fullscreenElement ||
      document.webkitFullscreenElement ||
      document.mozFullScreenElement ||
      document.msFullscreenElement
    );
  }

  function getHomeUrl() {
    const path = window.location.pathname;
    if (path.includes('/student/') || path.includes('/faculty/')) {
      return '../index.html';
    }
    return 'index.html';
  }

  async function enterFullscreen() {
    if (isFullscreen()) return;
    try {
      const el = document.documentElement;
      if (el.requestFullscreen) {
        await el.requestFullscreen();
      } else if (el.webkitRequestFullscreen) {
        await el.webkitRequestFullscreen();
      } else if (el.mozRequestFullScreen) {
        await el.mozRequestFullScreen();
      } else if (el.msRequestFullscreen) {
        await el.msRequestFullscreen();
      }
      isFullscreenActive = true;
      hasUserExplicitlyExited = false;
      updateUI();
      if (typeof Toast !== 'undefined') {
        Toast.success('Distraction-Free Fullscreen Mode Activated');
      }
    } catch (err) {
      console.warn('[FocusFullscreen] Fullscreen request rejected or unsupported by browser policy', err);
    }
  }

  async function exitFullscreenOnly() {
    try {
      if (isFullscreen()) {
        if (document.exitFullscreen) {
          await document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
          await document.webkitExitFullscreen();
        } else if (document.mozCancelFullScreen) {
          await document.mozCancelFullScreen();
        } else if (document.msExitFullscreen) {
          await document.msExitFullscreen();
        }
      }
    } catch (e) {
      console.warn('[FocusFullscreen] Error exiting fullscreen', e);
    } finally {
      isFullscreenActive = false;
      updateUI();
    }
  }

  async function exitAndReturnHome() {
    hasUserExplicitlyExited = true;
    try {
      if (isFullscreen()) {
        if (document.exitFullscreen) {
          await document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
          await document.webkitExitFullscreen();
        } else if (document.mozCancelFullScreen) {
          await document.mozCancelFullScreen();
        } else if (document.msExitFullscreen) {
          await document.msExitFullscreen();
        }
      }
    } catch (e) {
      console.warn('[FocusFullscreen] Error exiting fullscreen', e);
    } finally {
      isFullscreenActive = false;
      window.location.href = getHomeUrl();
    }
  }

  async function toggleFullscreen() {
    if (isFullscreen()) {
      await exitFullscreenOnly();
    } else {
      await enterFullscreen();
    }
  }

  function updateUI() {
    const active = isFullscreen();
    document.querySelectorAll('[data-fullscreen-btn]').forEach(btn => {
      if (active) {
        btn.innerHTML = '<span>⛶</span> Exit Fullscreen';
        btn.title = 'Exit Fullscreen Mode';
        btn.classList.add('fullscreen-active');
      } else {
        btn.innerHTML = '<span>⛶</span> Focus Fullscreen';
        btn.title = 'Enter Distraction-Free Fullscreen';
        btn.classList.remove('fullscreen-active');
      }
    });

    const floatingExit = document.getElementById('floating-exit-fullscreen-btn');
    if (floatingExit) {
      floatingExit.style.display = active ? 'flex' : 'none';
    }
  }

  function renderFloatingExitButton() {
    if (document.getElementById('floating-exit-fullscreen-btn')) return;

    const btn = document.createElement('button');
    btn.id = 'floating-exit-fullscreen-btn';
    btn.className = 'floating-fullscreen-exit-btn';
    btn.innerHTML = '<span>✕</span> Exit to Home Screen';
    btn.title = 'Exit Fullscreen & Return to Home Page';
    btn.style.cssText = `
      position: fixed;
      top: 14px;
      right: 18px;
      z-index: 99999;
      display: none;
      align-items: center;
      gap: 8px;
      background: rgba(13, 21, 46, 0.95);
      border: 1px solid rgba(239, 68, 68, 0.6);
      border-radius: 8px;
      padding: 8px 16px;
      color: #fff;
      font-family: 'Inter', sans-serif;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 0 20px rgba(239, 68, 68, 0.35);
      backdrop-filter: blur(12px);
      transition: all 0.2s ease;
    `;

    btn.addEventListener('mouseenter', () => {
      btn.style.background = 'rgba(239, 68, 68, 0.95)';
      btn.style.borderColor = '#ef4444';
      btn.style.transform = 'scale(1.04)';
    });

    btn.addEventListener('mouseleave', () => {
      btn.style.background = 'rgba(13, 21, 46, 0.95)';
      btn.style.borderColor = 'rgba(239, 68, 68, 0.6)';
      btn.style.transform = 'scale(1)';
    });

    btn.addEventListener('click', exitAndReturnHome);
    document.body.appendChild(btn);
  }

  function setupAutoFullscreen(targetSelector = '.code-editor-container, .code-textarea, .CodeMirror, #editor-container') {
    const triggerAuto = () => {
      if (!isFullscreen() && !hasUserExplicitlyExited) {
        enterFullscreen();
      }
    };

    // Listen on target elements
    document.querySelectorAll(targetSelector).forEach(el => {
      el.addEventListener('focus', triggerAuto, { passive: true });
      el.addEventListener('click', triggerAuto, { passive: true });
      el.addEventListener('keydown', triggerAuto, { passive: true });
      el.addEventListener('input', triggerAuto, { passive: true });
    });

    // Also listen globally for first keypress / interaction inside lab
    const globalLabContainer = document.getElementById('lab-body') || document.querySelector('.main-content');
    if (globalLabContainer) {
      globalLabContainer.addEventListener('keydown', (e) => {
        if (!isFullscreen() && !hasUserExplicitlyExited && e.key !== 'Escape') {
          enterFullscreen();
        }
      }, { passive: true });
    }
  }

  function init() {
    renderFloatingExitButton();

    document.addEventListener('fullscreenchange', updateUI);
    document.addEventListener('webkitfullscreenchange', updateUI);
    document.addEventListener('mozfullscreenchange', updateUI);
    document.addEventListener('MSFullscreenChange', updateUI);

    // Attach click listeners to data-fullscreen-btn elements
    document.querySelectorAll('[data-fullscreen-btn]').forEach(btn => {
      btn.addEventListener('click', (e) => {
        e.preventDefault();
        toggleFullscreen();
      });
    });

    // Automatically enable auto-fullscreen for any code editor / textarea on page
    setupAutoFullscreen();

    updateUI();
  }

  document.addEventListener('DOMContentLoaded', init);

  return {
    init,
    enterFullscreen,
    exitFullscreenOnly,
    exitAndReturnHome,
    toggleFullscreen,
    isFullscreen,
    setupAutoFullscreen
  };
})();
