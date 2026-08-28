/**
 * Platform-Wide Anti-Cheat & Copy-Paste Protection (security.js)
 * Completely disables copy, cut, paste, right-click context menu,
 * drag-and-drop, and shortcut keys across the entire platform.
 */

(function () {
  'use strict';

  function showBlockMessage(action) {
    const msg = `🚫 ${action} is completely disabled on this platform to ensure authentic programming practice.`;
    if (typeof Toast !== 'undefined' && typeof Toast.show === 'function') {
      Toast.show(msg, 'error', 3000);
    } else if (typeof Toast !== 'undefined' && typeof Toast.error === 'function') {
      Toast.error(msg);
    } else {
      // Create lightweight floating warning banner if Toast is not yet loaded
      let banner = document.getElementById('security-banner');
      if (!banner) {
        banner = document.createElement('div');
        banner.id = 'security-banner';
        banner.style.cssText = 'position:fixed;bottom:24px;left:50%;transform:translateX(-50%);background:#ef4444;color:#fff;font-family:sans-serif;font-weight:700;font-size:13px;padding:10px 20px;border-radius:8px;z-index:999999;box-shadow:0 10px 30px rgba(0,0,0,0.6);border:1px solid #fca5a5;';
        document.body.appendChild(banner);
      }
      banner.textContent = msg;
      banner.style.display = 'block';
      setTimeout(() => { if (banner) banner.style.display = 'none'; }, 2800);
    }
  }

  // 1. Disable Clipboard Events (Copy, Cut, Paste) Globally
  document.addEventListener('copy', (e) => {
    e.preventDefault();
    showBlockMessage('Copying code');
  }, true);

  document.addEventListener('cut', (e) => {
    e.preventDefault();
    showBlockMessage('Cutting code');
  }, true);

  document.addEventListener('paste', (e) => {
    e.preventDefault();
    showBlockMessage('Pasting code');
  }, true);

  // 2. Disable Keyboard Shortcuts (Ctrl/Cmd + C, V, X, Insert)
  document.addEventListener('keydown', (e) => {
    const isCtrlOrCmd = e.ctrlKey || e.metaKey;
    const key = (e.key || '').toLowerCase();

    // Copy (Ctrl+C), Paste (Ctrl+V), Cut (Ctrl+X)
    if (isCtrlOrCmd && (key === 'c' || key === 'v' || key === 'x')) {
      e.preventDefault();
      e.stopPropagation();
      showBlockMessage(key === 'v' ? 'Pasting' : (key === 'c' ? 'Copying' : 'Cutting'));
      return false;
    }

    // Shift+Insert (Paste on Windows/Linux), Ctrl+Insert (Copy)
    if ((e.shiftKey && e.key === 'Insert') || (e.ctrlKey && e.key === 'Insert')) {
      e.preventDefault();
      e.stopPropagation();
      showBlockMessage('Clipboard shortcut');
      return false;
    }
  }, true);

  // 3. Disable Context Menu
  document.addEventListener('contextmenu', (e) => {
    e.preventDefault();
  }, true);

  // 4. Disable Drag and Drop into Textareas / Code Editors
  document.addEventListener('dragover', (e) => {
    e.preventDefault();
  }, true);

  document.addEventListener('drop', (e) => {
    e.preventDefault();
    showBlockMessage('Drag and drop');
  }, true);

  // 5. CodeMirror Hook Helper
  window.attachCodeMirrorCopyPasteBlock = function (cmInstance) {
    if (!cmInstance) return;

    // Block beforeChange paste origins
    cmInstance.on('beforeChange', (instance, change) => {
      if (change.origin === 'paste') {
        change.cancel();
        showBlockMessage('Pasting into editor');
      } else if (change.origin === '+input' && change.text && change.text.length > 1 && change.text.join('').trim().length > 10) {
        // Block multi-line drop or paste simulation
        change.cancel();
        showBlockMessage('Pasting multi-line code');
      }
    });

    // Block DOM paste events inside CodeMirror wrapper
    const wrapper = cmInstance.getWrapperElement();
    if (wrapper) {
      wrapper.addEventListener('paste', (e) => {
        e.preventDefault();
        e.stopPropagation();
        showBlockMessage('Pasting into editor');
      }, true);

      wrapper.addEventListener('copy', (e) => {
        e.preventDefault();
        e.stopPropagation();
        showBlockMessage('Copying from editor');
      }, true);
    }
  };

})();
