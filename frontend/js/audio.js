/* ═══════════════════════════════════════════════════════════════
   Web Audio Synthesizer — Sound Disabled Per User Preference (audio.js)
   ═══════════════════════════════════════════════════════════════ */

const SoundFX = (() => {
  // All sound FX are completely muted per user requirement
  let isMuted = true;

  function toggleMute() {
    isMuted = true;
    return true;
  }

  function getMuted() {
    return true;
  }

  function updateAudioToggleUI() {}

  // Dummy no-op play functions to ensure zero audio output
  function playClick() {}
  function playHover() {}
  function playExecute() {}
  function playSuccess() {}
  function playError() {}
  function playXP() {}
  function playLevelUp() {}
  function playHintUnlock() {}
  function attachButtonSounds() {}

  return {
    toggleMute,
    getMuted,
    playClick,
    playHover,
    playExecute,
    playSuccess,
    playError,
    playXP,
    playLevelUp,
    playHintUnlock,
    attachButtonSounds,
    updateAudioToggleUI
  };
})();
