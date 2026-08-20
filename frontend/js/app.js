/* ═══════════════════════════════════════════════════════════════
   AI Programming Lab — App (app.js)
   Application initialization and shared utilities
   ═══════════════════════════════════════════════════════════════ */

const App = (() => {

  /**
   * Initialize a page with common setup
   * @param {Object} options
   * @param {string} options.role - 'student' | 'faculty'
   * @param {string} options.activeNav - Active nav item ID
   * @param {boolean} options.sidebar - Whether to mount sidebar
   * @param {Function} options.onReady - Callback when page is ready
   */
  function init(options = {}) {
    document.addEventListener('DOMContentLoaded', () => {
      // Mount sidebar if requested
      if (options.sidebar !== false) {
        Navigation.mount(options.role || 'student', options.activeNav || '');
      }

      // Initialize GSAP page entrance
      if (typeof gsap !== 'undefined' && typeof Animations !== 'undefined') {
        Animations.initPage();
      }

      // Initialize Chart.js defaults
      if (typeof Chart !== 'undefined' && typeof Charts !== 'undefined') {
        Charts.init();
      }

      // Call page-specific init
      if (options.onReady) {
        options.onReady();
      }
    });
  }

  /**
   * Format a date string to readable format
   * @param {string} dateStr - ISO date string
   * @returns {string}
   */
  function formatDate(dateStr) {
    const d = new Date(dateStr);
    return d.toLocaleDateString('en-IN', {
      day: 'numeric',
      month: 'short',
      year: 'numeric',
    });
  }

  /**
   * Get difficulty color class
   * @param {string} difficulty
   * @returns {string}
   */
  function difficultyClass(difficulty) {
    switch (difficulty) {
      case 'easy':   return 'difficulty-easy';
      case 'medium': return 'difficulty-medium';
      case 'hard':   return 'difficulty-hard';
      default:       return 'difficulty-easy';
    }
  }

  /**
   * Get status class
   * @param {string} status
   * @returns {string}
   */
  function statusClass(status) {
    switch (status) {
      case 'completed': return 'status-completed';
      case 'attempted': return 'status-attempted';
      case 'pending':   return 'status-pending';
      default:          return 'status-pending';
    }
  }

  /**
   * Get status label
   * @param {string} status
   * @returns {string}
   */
  function statusLabel(status) {
    switch (status) {
      case 'completed': return '✓ Completed';
      case 'attempted': return '◌ Attempted';
      case 'pending':   return '○ Not Started';
      default:          return '○ Not Started';
    }
  }

  /**
   * Simulate an API delay for mock data
   * @param {number} ms - Delay in milliseconds
   * @returns {Promise}
   */
  function delay(ms = 300) {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  return {
    init,
    formatDate,
    difficultyClass,
    statusClass,
    statusLabel,
    delay,
  };
})();
