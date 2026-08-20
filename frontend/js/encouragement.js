/* ═══════════════════════════════════════════════════════════════
   AI Programming Lab — Encouragement Engine (encouragement.js)
   Context-aware motivational messaging system
   ═══════════════════════════════════════════════════════════════ */

const Encouragement = (() => {
  // Track recently shown messages to prevent repetition
  const recentMessages = new Map(); // event -> [lastShownIndices]
  const MAX_RECENT = 3; // Track last 3 messages per event

  // ── Message Pools ───────────────────────────────────────────

  const messages = {
    first_run: [
      { text: "🎉 Your first program is running!", sub: "Welcome to the lab." },
      { text: "You just ran your first program!", sub: "This is where it all begins." },
      { text: "Great start!", sub: "Your first step into C programming." },
    ],

    compile_success: [
      { text: "✓ Nice! Your code compiled successfully.", sub: null },
      { text: "Great work — your program is running.", sub: null },
      { text: "Clean compile! Let's see what your program does.", sub: null },
      { text: "✓ Compiled without errors. Good job.", sub: null },
      { text: "Your code compiled cleanly.", sub: "Nice attention to syntax." },
      { text: "✓ No compiler errors. Well done.", sub: null },
      { text: "Compiled on first try! Looking good.", sub: null },
    ],

    execution_success: [
      { text: "🎉 Excellent! Your program produced the expected result.", sub: null },
      { text: "🔥 Nice work! All test cases passed.", sub: null },
      { text: "Great job — you got the correct output.", sub: null },
      { text: "That's a successful run!", sub: "Your program works as expected." },
      { text: "✓ Output matches perfectly.", sub: null },
      { text: "Your program is producing the right results!", sub: null },
      { text: "All outputs are correct. Excellent work.", sub: null },
    ],

    error_detected: [
      { text: "Something needs your attention.", sub: "Let's debug this together." },
      { text: "Your program has a small issue.", sub: "Check the hint below." },
      { text: "Almost there — there's a small problem to fix.", sub: null },
      { text: "Let's take a look at this error.", sub: "Debugging is part of learning." },
      { text: "Not quite right yet.", sub: "Check the highlighted line." },
      { text: "There's something to fix here.", sub: "Read the compiler message carefully." },
    ],

    error_fixed: [
      { text: "🎉 You fixed it!", sub: null },
      { text: "Nice debugging! You found the issue yourself.", sub: null },
      { text: "Great catch!", sub: "That's exactly what debugging is about." },
      { text: "You found the problem and solved it yourself. Nice!", sub: null },
      { text: "Bug squashed! Good work.", sub: null },
      { text: "That's the fix! Great debugging skills.", sub: null },
      { text: "Error resolved. You're getting better at this.", sub: null },
    ],

    all_tests_passed: [
      { text: "🎉 All test cases passed!", sub: "Your solution is correct." },
      { text: "✓ Every test case succeeded.", sub: "Excellent work!" },
      { text: "100% test pass rate!", sub: "Your program handles all cases." },
      { text: "All tests green. Perfect execution.", sub: null },
    ],

    score_improved: [
      { text: "⚡ Great improvement!", sub: null },
      { text: "You're doing better than your previous attempt.", sub: null },
      { text: "Your debugging is getting stronger.", sub: null },
      { text: "Nice progress — fewer attempts this time!", sub: null },
      { text: "Your score went up. Keep it going.", sub: null },
      { text: "Better than before! You're improving.", sub: null },
    ],

    personal_best: [
      { text: "🏆 New personal best!", sub: "You've beaten your previous score." },
      { text: "⚡ That's your best score on this problem!", sub: null },
      { text: "New high score! You're getting better.", sub: null },
      { text: "Personal record broken! Nice work.", sub: null },
    ],

    creative_solution: [
      { text: "✦ Interesting approach!", sub: null },
      { text: "You solved this using a different valid technique.", sub: null },
      { text: "Nice thinking — your approach is different from the common solution.", sub: null },
      { text: "That's the kind of experimentation we want to see.", sub: null },
      { text: "Creative problem-solving! You explored an alternative path.", sub: null },
    ],

    difficult_problem_completed: [
      { text: "🔥 You conquered a difficult problem!", sub: null },
      { text: "That one wasn't easy. Great persistence.", sub: null },
      { text: "Excellent work! You pushed through a challenging problem.", sub: null },
      { text: "Hard problem defeated! Your skills are growing.", sub: null },
      { text: "Impressive! You handled that tough challenge well.", sub: null },
    ],

    streak: [
      { text: "🔥 You're on a streak!", sub: null },
      { text: "Consistent practice pays off. Keep going!", sub: null },
      { text: "Another day of coding! Your streak continues.", sub: null },
      { text: "Your dedication is showing. Great consistency.", sub: null },
    ],

    attempt_improved: [
      { text: "You're getting closer.", sub: null },
      { text: "Not quite there yet — but this attempt is better than the last one.", sub: null },
      { text: "Good attempt. Look at the hint and try again.", sub: null },
      { text: "Debugging takes practice. Keep going.", sub: null },
      { text: "You've found part of the problem. Now let's find the rest.", sub: null },
      { text: "Better than before. You're narrowing it down.", sub: null },
      { text: "Progress! Each attempt gets you closer.", sub: null },
    ],

    // Fallback for neutral events
    neutral: [
      { text: "Keep going.", sub: null },
      { text: "Good effort.", sub: null },
      { text: "Let's keep working on this.", sub: null },
    ],
  };

  // ── Core Selection Logic ────────────────────────────────────

  /**
   * Get a non-repetitive random message from a pool
   * @param {string} event - The event type
   * @returns {Object} { text, sub }
   */
  function pickMessage(event) {
    const pool = messages[event] || messages.neutral;
    if (!pool || pool.length === 0) return { text: "Keep going.", sub: null };

    // Get recently used indices for this event
    let recent = recentMessages.get(event) || [];

    // Find available indices (not recently used)
    let available = pool.map((_, i) => i).filter(i => !recent.includes(i));

    // If all used up, reset
    if (available.length === 0) {
      recent = [];
      available = pool.map((_, i) => i);
    }

    // Random pick from available
    const idx = available[Math.floor(Math.random() * available.length)];

    // Track this pick
    recent.push(idx);
    if (recent.length > MAX_RECENT) recent.shift();
    recentMessages.set(event, recent);

    return pool[idx];
  }

  // ── Main API ────────────────────────────────────────────────

  /**
   * Get contextual encouragement based on event and context
   * @param {Object} ctx
   * @param {string} ctx.event - Event type
   * @param {boolean} [ctx.scoreImproved] - Did score improve?
   * @param {boolean} [ctx.isPersonalBest] - Is this a personal best?
   * @param {boolean} [ctx.isCreative] - Was the solution creative?
   * @param {boolean} [ctx.isDifficult] - Was the problem difficult?
   * @param {boolean} [ctx.isFirstRun] - Is this the student's first run?
   * @param {number}  [ctx.attemptNumber] - Current attempt number
   * @param {boolean} [ctx.allTestsPassed] - Did all tests pass?
   * @param {number}  [ctx.streak] - Current streak days
   * @returns {Object} { text, sub, event }
   */
  function getEncouragement(ctx) {
    let event = ctx.event || "neutral";

    // Priority overrides
    if (ctx.isFirstRun && event === "execution_success") {
      event = "first_run";
    } else if (ctx.isCreative && event === "execution_success") {
      event = "creative_solution";
    } else if (ctx.isDifficult && event === "execution_success") {
      event = "difficult_problem_completed";
    } else if (ctx.isPersonalBest && event === "execution_success") {
      event = "personal_best";
    } else if (ctx.allTestsPassed && event === "execution_success") {
      event = "all_tests_passed";
    } else if (ctx.scoreImproved && event === "error_detected") {
      event = "attempt_improved";
    } else if (ctx.streak && ctx.streak >= 3 && event === "compile_success") {
      // Occasionally mention streak
      if (Math.random() < 0.3) event = "streak";
    }

    const msg = pickMessage(event);
    return { ...msg, event };
  }

  /**
   * Get a random daily motivational message
   * @returns {Object} { quote, sub }
   */
  function getDailyMotivation() {
    return MockData.getDailyMessage();
  }

  // ── Public API ──────────────────────────────────────────────
  return {
    getEncouragement,
    getDailyMotivation,
    messages, // exposed for testing
  };
})();
