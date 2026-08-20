/* ═══════════════════════════════════════════════════════════════
   AI Programming Lab — Animations (animations.js)
   GSAP animation orchestrator & celebration effects
   ═══════════════════════════════════════════════════════════════ */

const Animations = (() => {

  // ── Check for reduced motion preference ─────────────────────
  const prefersReducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // ── GSAP Helpers ────────────────────────────────────────────

  /**
   * Stagger-reveal a set of elements on page load
   * @param {string} selector - CSS selector for elements
   * @param {Object} options - Animation options
   */
  function staggerReveal(selector, options = {}) {
    if (prefersReducedMotion) {
      document.querySelectorAll(selector).forEach(el => {
        el.style.opacity = '1';
        el.style.transform = 'none';
      });
      return;
    }

    const defaults = {
      y: 30,
      opacity: 0,
      duration: 0.6,
      stagger: 0.1,
      ease: "power3.out",
      delay: options.delay || 0,
    };

    const opts = { ...defaults, ...options };

    gsap.from(selector, {
      y: opts.y,
      opacity: opts.opacity,
      duration: opts.duration,
      stagger: opts.stagger,
      ease: opts.ease,
      delay: opts.delay,
    });
  }

  /**
   * Animate a single element entrance
   * @param {Element|string} el - Element or selector
   * @param {Object} options
   */
  function animateIn(el, options = {}) {
    if (prefersReducedMotion) {
      const element = typeof el === 'string' ? document.querySelector(el) : el;
      if (element) {
        element.style.opacity = '1';
        element.style.transform = 'none';
      }
      return;
    }

    gsap.from(el, {
      y: options.y || 20,
      opacity: 0,
      duration: options.duration || 0.5,
      ease: options.ease || "power3.out",
      delay: options.delay || 0,
      onComplete: options.onComplete || null,
    });
  }

  /**
   * Animate a counter from 0 to target value
   * @param {Element} el - The element displaying the number
   * @param {number} target - Target value
   * @param {Object} options
   */
  function countUp(el, target, options = {}) {
    if (!el) return;

    const duration = options.duration || 1.5;
    const decimals = options.decimals || 0;
    const suffix = options.suffix || '';
    const prefix = options.prefix || '';

    if (prefersReducedMotion) {
      el.textContent = prefix + target.toFixed(decimals) + suffix;
      return;
    }

    const obj = { val: 0 };
    gsap.to(obj, {
      val: target,
      duration: duration,
      ease: "power2.out",
      delay: options.delay || 0,
      onUpdate: () => {
        el.textContent = prefix + obj.val.toFixed(decimals) + suffix;
      },
    });
  }

  /**
   * Animate progress bar width
   * @param {Element} el - The fill element
   * @param {number} percentage - Target percentage
   * @param {Object} options
   */
  function animateProgressBar(el, percentage, options = {}) {
    if (!el) return;

    if (prefersReducedMotion) {
      el.style.width = percentage + '%';
      return;
    }

    gsap.fromTo(el,
      { width: '0%' },
      {
        width: percentage + '%',
        duration: options.duration || 1.2,
        ease: "power2.out",
        delay: options.delay || 0,
      }
    );
  }

  // ── Scroll Reveal ───────────────────────────────────────────

  function initScrollReveal() {
    if (prefersReducedMotion) {
      document.querySelectorAll('[data-reveal]').forEach(el => {
        el.classList.add('revealed');
      });
      return;
    }

    const observer = new IntersectionObserver((entries) => {
      entries.forEach(entry => {
        if (entry.isIntersecting) {
          entry.target.classList.add('revealed');
          observer.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15, rootMargin: '0px 0px -50px 0px' });

    document.querySelectorAll('[data-reveal]').forEach(el => {
      observer.observe(el);
    });
  }

  // ── Card Tilt Effect ────────────────────────────────────────

  function initTiltCards() {
    if (prefersReducedMotion) return;

    document.querySelectorAll('.tilt-card').forEach(card => {
      card.addEventListener('mousemove', (e) => {
        const rect = card.getBoundingClientRect();
        const x = e.clientX - rect.left;
        const y = e.clientY - rect.top;
        const centerX = rect.width / 2;
        const centerY = rect.height / 2;
        const rotateX = ((y - centerY) / centerY) * -4;
        const rotateY = ((x - centerX) / centerX) * 4;

        card.style.transform = `perspective(1000px) rotateX(${rotateX}deg) rotateY(${rotateY}deg) translateY(-4px)`;
      });

      card.addEventListener('mouseleave', () => {
        card.style.transform = 'perspective(1000px) rotateX(0) rotateY(0) translateY(0)';
      });
    });
  }

  // ── Celebration Effects ─────────────────────────────────────

  /**
   * Create a particle burst at a position
   * @param {number} x - X position (viewport)
   * @param {number} y - Y position (viewport)
   * @param {Object} options
   */
  function particleBurst(x, y, options = {}) {
    if (prefersReducedMotion) return;

    const count = options.count || 12;
    const colors = options.colors || ['#6366f1', '#a855f7', '#4ade80', '#fbbf24', '#38bdf8'];
    const container = document.body;

    for (let i = 0; i < count; i++) {
      const particle = document.createElement('div');
      particle.className = 'particle';
      particle.style.left = x + 'px';
      particle.style.top = y + 'px';
      particle.style.background = colors[i % colors.length];
      particle.style.setProperty('--tx', (Math.random() - 0.5) * 150 + 'px');
      particle.style.setProperty('--ty', (Math.random() - 0.5) * 150 + 'px');
      particle.style.animationDuration = (0.5 + Math.random() * 0.5) + 's';
      container.appendChild(particle);

      particle.addEventListener('animationend', () => {
        particle.remove();
      });
    }
  }

  /**
   * Create confetti at a position
   */
  function confetti(x, y, options = {}) {
    if (prefersReducedMotion) return;

    const count = options.count || 20;
    const colors = options.colors || ['#6366f1', '#a855f7', '#4ade80', '#fbbf24', '#f87171', '#38bdf8'];
    const container = document.body;

    for (let i = 0; i < count; i++) {
      const piece = document.createElement('div');
      piece.className = 'confetti';
      piece.style.left = (x + (Math.random() - 0.5) * 100) + 'px';
      piece.style.top = y + 'px';
      piece.style.background = colors[i % colors.length];
      piece.style.animationDuration = (0.8 + Math.random() * 0.8) + 's';
      piece.style.animationDelay = (Math.random() * 0.3) + 's';
      container.appendChild(piece);

      piece.addEventListener('animationend', () => {
        piece.remove();
      });
    }
  }

  /**
   * Success celebration — combines particle burst with confetti
   * @param {Element} triggerEl - The element that triggered success
   */
  function celebrate(triggerEl) {
    if (prefersReducedMotion || !triggerEl) return;

    const rect = triggerEl.getBoundingClientRect();
    const x = rect.left + rect.width / 2;
    const y = rect.top + rect.height / 2;

    particleBurst(x, y, { count: 15 });

    // Subtle pulse on the trigger element
    gsap.fromTo(triggerEl,
      { scale: 1 },
      {
        scale: 1.05,
        duration: 0.15,
        yoyo: true,
        repeat: 1,
        ease: "power2.inOut",
      }
    );
  }

  // ── Run Button State Transitions ────────────────────────────

  /**
   * Animate run button through states
   * @param {Element} btn - The button element
   * @param {string} state - 'running' | 'compiling' | 'success' | 'error' | 'ready'
   */
  function runButtonState(btn, state) {
    if (!btn) return;

    const playIcon = '<svg width="11" height="11" viewBox="0 0 12 12" fill="currentColor"><path d="M2 1.5l9 4.5-9 4.5V1.5z"/></svg>';
    const spinnerHTML = '<span class="spinner"></span>';

    btn.classList.remove('compiling', 'success', 'error');

    switch (state) {
      case 'compiling':
        btn.disabled = true;
        btn.classList.add('compiling');
        btn.innerHTML = spinnerHTML + ' Compiling...';
        break;
      case 'executing':
        btn.disabled = true;
        btn.classList.add('compiling');
        btn.innerHTML = spinnerHTML + ' Executing...';
        break;
      case 'success':
        btn.disabled = false;
        btn.classList.add('success');
        btn.innerHTML = '✓ Success';
        setTimeout(() => {
          btn.classList.remove('success');
          btn.innerHTML = playIcon + ' Run Code';
        }, 2500);
        break;
      case 'error':
        btn.disabled = false;
        btn.classList.add('error');
        btn.innerHTML = '! Error Found';
        setTimeout(() => {
          btn.classList.remove('error');
          btn.innerHTML = playIcon + ' Run Code';
        }, 2500);
        break;
      case 'ready':
      default:
        btn.disabled = false;
        btn.innerHTML = playIcon + ' Run Code';
        break;
    }
  }

  // ── AI Panel Staggered Reveal ───────────────────────────────

  function revealAIPanel(panelEl) {
    if (!panelEl) return;

    panelEl.style.display = 'block';

    if (prefersReducedMotion) return;

    const cards = panelEl.querySelectorAll('.ai-card');
    gsap.from(cards, {
      y: 20,
      opacity: 0,
      duration: 0.4,
      stagger: 0.12,
      ease: "power3.out",
      delay: 0.2,
    });
  }

  // ── Score Count-Up Animation ────────────────────────────────

  function animateScoreReveal(scoreEl, score, maxScore) {
    if (!scoreEl) return;

    if (prefersReducedMotion) {
      scoreEl.textContent = score.toFixed(1);
      return;
    }

    // Dramatic reveal
    gsap.from(scoreEl, {
      scale: 0.5,
      opacity: 0,
      duration: 0.6,
      ease: "back.out(1.7)",
    });

    countUp(scoreEl, score, { decimals: 1, duration: 1 });
  }

  // ── Page Init ───────────────────────────────────────────────

  function initPage() {
    initScrollReveal();
    initTiltCards();
  }

  // ── Public API ──────────────────────────────────────────────
  return {
    staggerReveal,
    animateIn,
    countUp,
    animateProgressBar,
    initScrollReveal,
    initTiltCards,
    particleBurst,
    confetti,
    celebrate,
    runButtonState,
    revealAIPanel,
    animateScoreReveal,
    initPage,
    prefersReducedMotion,
  };
})();
