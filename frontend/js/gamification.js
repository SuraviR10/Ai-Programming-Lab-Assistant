/* ═══════════════════════════════════════════════════════════════
   CODEVERSE — Gamification & Progression Engine (gamification.js)
   XP Calculations, Level 1-20 Ladder, Ranks, Real-time XP Floaters,
   and Cinematic Level-Up Modal Overlay
   ═══════════════════════════════════════════════════════════════ */

const Gamification = (() => {
  // ── Ranks Ladder ────────────────────────────────────────────
  const ranks = [
    { minLevel: 1,  title: "Novice Coder",     badge: "◈", color: "#94a3b8" },
    { minLevel: 3,  title: "Explorer",         badge: "✦", color: "#38bdf8" },
    { minLevel: 6,  title: "Debugger",         badge: "🛠", color: "#818cf8" },
    { minLevel: 10, title: "Problem Solver",   badge: "⚡", color: "#00f5d4" },
    { minLevel: 14, title: "Code Architect",   badge: "◆", color: "#a855f7" },
    { minLevel: 18, title: "Algorithm Master", badge: "👑", color: "#ffd166" }
  ];

  // ── State Initialization from localStorage or MockData ──────
  let currentXP = parseInt(localStorage.getItem('codeverse_xp')) || 2840;
  let streakDays = parseInt(localStorage.getItem('codeverse_streak')) || 5;

  // ── XP & Level Calculations ─────────────────────────────────
  // Level threshold formula: Level L requires 350 * L total XP
  function getLevelForXP(xp) {
    let level = 1;
    while (xp >= getXPForLevel(level + 1)) {
      level++;
    }
    return level;
  }

  function getXPForLevel(level) {
    if (level <= 1) return 0;
    // Cumulative XP curve
    return Math.floor(250 * Math.pow(level, 1.45));
  }

  function getLevelProgress(xp) {
    const currentLevel = getLevelForXP(xp);
    const levelStartXP = getXPForLevel(currentLevel);
    const nextLevelXP = getXPForLevel(currentLevel + 1);
    const xpInLevel = xp - levelStartXP;
    const xpNeededForLevel = nextLevelXP - levelStartXP;
    const percent = Math.min(100, Math.max(0, Math.floor((xpInLevel / xpNeededForLevel) * 100)));

    return {
      currentLevel,
      currentXP: xp,
      levelStartXP,
      nextLevelXP,
      xpInLevel,
      xpNeededForLevel,
      xpToNext: nextLevelXP - xp,
      percent,
      rank: getRankForLevel(currentLevel)
    };
  }

  function getRankForLevel(level) {
    let matched = ranks[0];
    for (const r of ranks) {
      if (level >= r.minLevel) {
        matched = r;
      }
    }
    return matched;
  }

  // ── Real-Time XP Award & Floating Visuals ────────────────────
  /**
   * Award XP with visual and sound feedback
   * @param {number} amount - XP amount
   * @param {string} reason - Description (e.g., 'Error Debugged', 'Mission Complete')
   * @param {Element|{clientX: number, clientY: number}} [source] - Source for fly-up animation
   */
  function awardXP(amount, reason = '', source = null) {
    const prevProgress = getLevelProgress(currentXP);
    currentXP += amount;
    localStorage.setItem('codeverse_xp', currentXP);
    const newProgress = getLevelProgress(currentXP);

    // 1. Play Sound
    if (typeof SoundFX !== 'undefined') {
      SoundFX.playXP();
    }

    // 2. Spawn Floating `+XP` particle
    spawnXPFloater(amount, source);

    // 3. Show Toast Notice
    if (typeof Toast !== 'undefined') {
      Toast.info(`<strong>+${amount} Points</strong> · ${reason}`);
    }


    // 4. Update HUD elements on page
    updateHUDDisplays(prevProgress, newProgress);

    // 5. Check for Level-Up
    if (newProgress.currentLevel > prevProgress.currentLevel) {
      setTimeout(() => {
        triggerLevelUpModal(newProgress.currentLevel, newProgress.rank);
      }, 700);
    }

    return newProgress;
  }

  // ── Spawn Floating XP Animation ─────────────────────────────
  function spawnXPFloater(amount, source) {
    const floater = document.createElement('div');
    floater.className = 'xp-flyup';
    floater.textContent = `+${amount} XP`;

    let x = window.innerWidth / 2;
    let y = window.innerHeight / 2;

    if (source && source.getBoundingClientRect) {
      const rect = source.getBoundingClientRect();
      x = rect.left + rect.width / 2;
      y = rect.top + rect.height / 2;
    } else if (source && source.clientX !== undefined) {
      x = source.clientX;
      y = source.clientY;
    }

    floater.style.left = `${x}px`;
    floater.style.top = `${y}px`;
    document.body.appendChild(floater);

    setTimeout(() => {
      if (floater.parentNode) floater.remove();
    }, 1500);
  }

  // ── Update HUD Displays Across Page ─────────────────────────
  function updateHUDDisplays(oldProg, newProg) {
    // XP Counters
    document.querySelectorAll('[data-hud-xp]').forEach(el => {
      if (typeof Animations !== 'undefined') {
        Animations.countUp(el, newProg.currentXP);
      } else {
        el.textContent = newProg.currentXP.toLocaleString();
      }
    });

    // Level Badges
    document.querySelectorAll('[data-hud-level]').forEach(el => {
      el.textContent = `LEVEL ${String(newProg.currentLevel).padStart(2, '0')}`;
    });

    // Rank Titles
    document.querySelectorAll('[data-hud-rank]').forEach(el => {
      el.textContent = newProg.rank.title;
      if (el.style) el.style.color = newProg.rank.color;
    });

    // XP Progress Bars
    document.querySelectorAll('[data-hud-xp-fill]').forEach(el => {
      el.style.width = `${newProg.percent}%`;
    });

    // XP Metrics Text
    document.querySelectorAll('[data-hud-xp-text]').forEach(el => {
      el.textContent = `${newProg.xpInLevel.toLocaleString()} / ${newProg.xpNeededForLevel.toLocaleString()} XP (${newProg.xpToNext.toLocaleString()} XP TO NEXT LEVEL)`;
    });
  }

  // ── Level-Up Cinematic Modal Overlay ────────────────────────
  function triggerLevelUpModal(level, rank) {
    if (typeof SoundFX !== 'undefined') {
      SoundFX.playLevelUp();
    }

    let overlay = document.getElementById('codeverse-levelup-modal');
    if (!overlay) {
      overlay = document.createElement('div');
      overlay.id = 'codeverse-levelup-modal';
      overlay.className = 'levelup-overlay';
      overlay.innerHTML = `
        <div class="levelup-card">
          <div class="levelup-stars">✦ ✦ ✦</div>
          <div class="levelup-banner">LEVEL UPGRADED</div>
          <div class="levelup-level-num" id="modal-levelup-num">LEVEL 00</div>
          <div class="levelup-rank" id="modal-levelup-rank">RANK: NOVICE</div>
          <button class="btn btn-primary btn-lg" onclick="Gamification.closeLevelUpModal()" style="width: 100%;">
            CLAIM ADVANCEMENT →
          </button>
        </div>
      `;
      document.body.appendChild(overlay);
    }

    document.getElementById('modal-levelup-num').textContent = `LEVEL ${String(level).padStart(2, '0')}`;
    document.getElementById('modal-levelup-rank').innerHTML = `CODING RANK: <span style="color: ${rank.color}; font-weight: 800;">${rank.title}</span>`;

    overlay.classList.add('active');

    // Confetti celebration
    if (typeof Animations !== 'undefined') {
      setTimeout(() => {
        Animations.confetti(window.innerWidth / 2, window.innerHeight / 2 - 100, { count: 35 });
      }, 200);
    }
  }

  function closeLevelUpModal() {
    const overlay = document.getElementById('codeverse-levelup-modal');
    if (overlay) {
      overlay.classList.remove('active');
    }
  }

  // ── Initialize on Page Load ─────────────────────────────────
  function init() {
    const progress = getLevelProgress(currentXP);
    updateHUDDisplays(progress, progress);
  }

  document.addEventListener('DOMContentLoaded', init);

  return {
    getCurrentXP: () => currentXP,
    getStreakDays: () => streakDays,
    getProgress: () => getLevelProgress(currentXP),
    awardXP,
    triggerLevelUpModal,
    closeLevelUpModal,
    ranks
  };
})();
