/* ═══════════════════════════════════════════════════════════════
   CODEVERSE — Navigation (navigation.js)
   Cyberpunk Sidebar with Live Player HUD, Sound FX Toggle & Active Glows
   ═══════════════════════════════════════════════════════════════ */

const Navigation = (() => {

  const icons = {
    dashboard: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>',
    problems: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"/><polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/><line x1="16" y1="17" x2="8" y2="17"/></svg>',
    lab: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/><line x1="14" y1="4" x2="10" y2="20"/></svg>',
    progress: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/></svg>',
    achievements: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="8" r="6"/><path d="M15.477 12.89L17 22l-5-3-5 3 1.523-9.11"/></svg>',
    students: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M17 21v-2a4 4 0 0 0-4-4H5a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M23 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/></svg>',
    analytics: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21.21 15.89A10 10 0 1 1 8 2.83"/><path d="M22 12A10 10 0 0 0 12 2v10z"/></svg>',
    sessions: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="10"/><polyline points="12 6 12 12 16 14"/></svg>',
    exams: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="11" width="18" height="11" rx="2" ry="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>',
    logout: '<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4"/><polyline points="16 17 21 12 16 7"/><line x1="21" y1="12" x2="9" y2="12"/></svg>',
  };

  const studentMenu = [
    { id: 'dashboard',    label: 'Dashboard',         icon: 'dashboard',    href: 'student/dashboard.html' },
    { id: 'problems',     label: 'Lab Problems',      icon: 'problems',     href: 'student/problems.html' },
    { id: 'exams',        label: 'Exams & Write-ups', icon: 'exams',        href: 'student/exams.html' },
    { id: 'lab',          label: 'C Code Editor',     icon: 'lab',          href: 'student/lab.html' },
    { id: 'progress',     label: 'My Progress',       icon: 'progress',     href: 'student/progress.html' },
    { id: 'achievements', label: 'Milestones',        icon: 'achievements', href: 'student/achievements.html' },
  ];

  const facultyMenu = [
    { id: 'dashboard',   label: 'Faculty Dashboard', icon: 'dashboard', href: 'faculty/dashboard.html' },
    { id: 'manual',      label: 'Lab Manual Upload',  icon: 'problems',  href: 'faculty/manual.html' },
    { id: 'students',    label: 'Student Roster',    icon: 'students',  href: 'faculty/students.html' },
  ];

  function resolveHref(href) {
    const path = window.location.pathname;
    if (path.includes('/student/') || path.includes('/faculty/')) {
      return '../' + href;
    }
    return href;
  }

  function renderSidebar(role = 'student', activeId = '') {
    const menu = role === 'faculty' ? facultyMenu : studentMenu;
    const userName = role === 'faculty' ? MockData.faculty.name : MockData.student.name;
    const userRole = role === 'faculty' ? 'Instructor' : 'C Student';
    const isMuted = typeof SoundFX !== 'undefined' ? SoundFX.getMuted() : false;

    const sidebar = document.createElement('aside');
    sidebar.className = 'sidebar';
    sidebar.id = 'main-sidebar';

    sidebar.innerHTML = `
      <div class="sidebar-logo">
        <div class="sidebar-logo-icon" style="background: linear-gradient(135deg, #00f2fe, #7c3aed); box-shadow: 0 0 15px rgba(0, 242, 254, 0.4);">⚡</div>
        <div>
          <div style="font-family: var(--font-cyber); font-weight: 800; font-size: 14px; color: #fff; letter-spacing: 0.1em;">AI LAB ASSISTANT</div>
          <div style="font-size: 10px; font-family: var(--font-mono); color: var(--neon-cyan);">C Programming Lab</div>
        </div>
      </div>


      <nav class="sidebar-nav" aria-label="Main navigation">
        <div style="padding: 0 12px 8px; font-size: 10px; font-weight: 700; color: var(--text-ghost); letter-spacing: 0.08em; text-transform: uppercase;">
          ${role === 'faculty' ? 'FACULTY PORTAL' : 'STUDENT PORTAL'}
        </div>
        ${menu.map(item => `
          <a href="${resolveHref(item.href)}"
             class="nav-item ${item.id === activeId ? 'active' : ''}"
             data-nav-id="${item.id}"
             aria-current="${item.id === activeId ? 'page' : 'false'}">
            ${icons[item.icon] || ''}
            <span>${item.label}</span>
          </a>
        `).join('')}
      </nav>

      <div class="sidebar-footer">
        ${role === 'student' ? `
          <div style="margin-bottom: 14px; padding: 10px; background: var(--bg-deepest); border: 1px solid var(--border-subtle); border-radius: var(--radius-md);">
            <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
              <span style="font-size: 10px; font-family: var(--font-cyber); color: var(--neon-cyan);" data-hud-level>LEVEL 08</span>
              <span style="font-size: 10px; font-family: var(--font-mono); color: var(--xp-gold);" data-hud-xp>2,840 Points</span>
            </div>
            <div class="xp-bar-container" style="height: 4px;">
              <div class="xp-bar-fill" data-hud-xp-fill style="width: 78%;"></div>
            </div>
          </div>
        ` : ''}

        <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px;">
          <div style="display: flex; align-items: center; gap: 10px;">
            <div style="width: 32px; height: 32px; border-radius: 50%; background: var(--gradient-primary); display: flex; align-items: center; justify-content: center; color: white; font-weight: 700; font-size: 13px; box-shadow: 0 0 10px rgba(99, 102, 241, 0.4);">
              ${userName.charAt(0)}
            </div>
            <div>
              <div style="font-size: 13px; font-weight: 700; color: var(--text-primary);">${userName}</div>
              <div style="font-size: 10px; color: var(--text-faint); font-family: var(--font-mono);">${userRole}</div>
            </div>
          </div>
          <button class="btn-audio-toggle ${isMuted ? 'muted' : ''}" onclick="SoundFX.toggleMute()" title="Toggle Sound FX" style="padding: 4px 8px;">
            ${isMuted ? '🔇' : '🔊'}
          </button>
        </div>

        <a href="${resolveHref('login.html')}" class="nav-item" style="color: var(--text-faint); margin-bottom: 0;">
          ${icons.logout}
          <span>Sign Out</span>
        </a>
      </div>

    `;

    return sidebar;
  }

  function mount(role = 'student', activeId = '') {
    const sidebar = renderSidebar(role, activeId);
    document.body.prepend(sidebar);

    const main = document.querySelector('.main-content');
    if (main) {
      main.style.marginLeft = '260px';
    }

    if (typeof SoundFX !== 'undefined') {
      SoundFX.attachButtonSounds();
    }
    if (typeof CyberCursor !== 'undefined') {
      CyberCursor.attachCursorEvents();
    }

    return sidebar;
  }

  return {
    mount,
    renderSidebar,
    icons
  };
})();
