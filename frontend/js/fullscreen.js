/* ═══════════════════════════════════════════════════════════════
   SMART LAB — Focus Fullscreen Controller (fullscreen.js)
   Enforces distraction-free fullscreen mode during lab sessions
   and provides safe exit-to-home navigation.
   ═══════════════════════════════════════════════════════════════ */

const FocusFullscreen = (() => {
  let isFullscreenActive = false;

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
    try {
      const el = document.documentElement;
      if (el.requestFullscreen) {
        await el.requestFullscreen();
      } else if (el.webkitRequestFullscreen) {
        await el.webkitRequestFullscreen();
      } else if (el.msRequestFullscreen) {
        await el.msRequestFullscreen();
      }
      isFullscreenActive = true;
      updateUI();
      if (typeof Toast !== 'undefined') {
        Toast.success('Distraction-Free Fullscreen Mode Activated');
      }
    } catch (err) {
      console.warn('[FocusFullscreen] Fullscreen request rejected or unsupported', err);
    }
  }

  async function exitAndReturnHome() {
    try {
      if (isFullscreen()) {
        if (document.exitFullscreen) {
          await document.exitFullscreen();
        } else if (document.webkitExitFullscreen) {
          await document.webkitExitFullscreen();
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

  function updateUI() {
    const active = isFullscreen();
    document.querySelectorAll('[data-fullscreen-btn]').forEach(btn => {
      if (active) {
        btn.innerHTML = '<span>✕</span> Exit to Home';
        btn.title = 'Exit Fullscreen & Return to Home';
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
      top: 16px;
      right: 16px;
      z-index: 99999;
      display: none;
      align-items: center;
      gap: 8px;
      background: rgba(13, 21, 46, 0.9);
      border: 1px solid rgba(239, 68, 68, 0.5);
      border-radius: 8px;
      padding: 8px 16px;
      color: #fff;
      font-family: 'Inter', sans-serif;
      font-size: 12px;
      font-weight: 700;
      cursor: pointer;
      box-shadow: 0 0 20px rgba(239, 68, 68, 0.3);
      backdrop-filter: blur(10px);
      transition: all 0.2s ease;
    `;

    btn.addEventListener('mouseenter', () => {
      btn.style.background = 'rgba(239, 68, 68, 0.9)';
      btn.style.borderColor = '#ef4444';
      btn.style.transform = 'scale(1.04)';
    });

    btn.addEventListener('mouseleave', () => {
      btn.style.background = 'rgba(13, 21, 46, 0.9)';
      btn.style.borderColor = 'rgba(239, 68, 68, 0.5)';
      btn.style.transform = 'scale(1)';
    });

    btn.addEventListener('click', exitAndReturnHome);
    document.body.appendChild(btn);
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
        if (isFullscreen()) {
          exitAndReturnHome();
        } else {
          enterFullscreen();
        }
      });
    });

    updateUI();
  }

  document.addEventListener('DOMContentLoaded', init);

  return {
    init,
    enterFullscreen,
    exitAndReturnHome,
    isFullscreen
  };
})();
