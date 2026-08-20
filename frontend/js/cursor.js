/* ═══════════════════════════════════════════════════════════════
   CODEVERSE — Custom Cyber Cursor & Magnetic Buttons (cursor.js)
   Minimalistic glowing cyber cursor with trailing follower and
   magnetic pull physics on interactive CTA elements
   ═══════════════════════════════════════════════════════════════ */

const CyberCursor = (() => {
  let cursorDot = null;
  let cursorFollower = null;
  let mouseX = -100;
  let mouseY = -100;
  let followerX = -100;
  let followerY = -100;
  let isHovering = false;
  let isReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  let isTouch = window.matchMedia('(pointer: coarse)').matches;

  function init() {
    if (isReducedMotion || isTouch) return;

    // Create cursor elements if not present
    if (!document.getElementById('cyber-cursor-dot')) {
      cursorDot = document.createElement('div');
      cursorDot.id = 'cyber-cursor-dot';
      cursorDot.className = 'custom-cursor';
      document.body.appendChild(cursorDot);

      cursorFollower = document.createElement('div');
      cursorFollower.id = 'cyber-cursor-follower';
      cursorFollower.className = 'custom-cursor-follower';
      document.body.appendChild(cursorFollower);
    } else {
      cursorDot = document.getElementById('cyber-cursor-dot');
      cursorFollower = document.getElementById('cyber-cursor-follower');
    }

    // Mouse movement listener
    window.addEventListener('mousemove', (e) => {
      mouseX = e.clientX;
      mouseY = e.clientY;

      if (cursorDot) {
        cursorDot.style.left = `${mouseX}px`;
        cursorDot.style.top = `${mouseY}px`;
      }
    }, { passive: true });

    // Smooth animation loop for follower
    function render() {
      // Lerp smoothing
      followerX += (mouseX - followerX) * 0.2;
      followerY += (mouseY - followerY) * 0.2;

      if (cursorFollower) {
        cursorFollower.style.left = `${followerX}px`;
        cursorFollower.style.top = `${followerY}px`;
      }

      requestAnimationFrame(render);
    }
    requestAnimationFrame(render);

    // Attach hover expansions
    attachCursorEvents();
    initMagneticButtons();
  }

  function attachCursorEvents() {
    const hoverTargets = 'a, button, .btn, .mission-card, .tilt-card, input, select, textarea, [data-cursor-hover]';
    document.querySelectorAll(hoverTargets).forEach(el => {
      if (!el.dataset.cursorBound) {
        el.dataset.cursorBound = 'true';
        el.addEventListener('mouseenter', () => {
          if (cursorDot) cursorDot.classList.add('active');
          if (cursorFollower) cursorFollower.classList.add('active');
        });
        el.addEventListener('mouseleave', () => {
          if (cursorDot) cursorDot.classList.remove('active');
          if (cursorFollower) cursorFollower.classList.remove('active');
        });
      }
    });
  }

  // ── Magnetic Button Physics ─────────────────────────────────
  function initMagneticButtons() {
    if (isReducedMotion || isTouch) return;

    const magneticElements = document.querySelectorAll('.btn-primary, .btn-run, .btn-submit, [data-magnetic]');
    magneticElements.forEach(btn => {
      if (btn.dataset.magneticBound) return;
      btn.dataset.magneticBound = 'true';

      btn.addEventListener('mousemove', (e) => {
        const rect = btn.getBoundingClientRect();
        const btnCenterX = rect.left + rect.width / 2;
        const btnCenterY = rect.top + rect.height / 2;

        const deltaX = (e.clientX - btnCenterX) * 0.25;
        const deltaY = (e.clientY - btnCenterY) * 0.25;

        btn.style.transform = `translate(${deltaX}px, ${deltaY}px)`;
      });

      btn.addEventListener('mouseleave', () => {
        btn.style.transform = 'translate(0px, 0px)';
      });
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    init();
  });

  return {
    init,
    attachCursorEvents,
    initMagneticButtons
  };
})();
