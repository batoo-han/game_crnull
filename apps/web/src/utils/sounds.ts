// Простые звуки через Web Audio API (без внешних файлов)
export function playSound(type: "move" | "win" | "gift" | "collect") {
  try {
    const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
    if (!AudioContextClass) return; // Браузер не поддерживает Web Audio API
    
    const audioContext = new AudioContextClass();
    
    const oscillator = audioContext.createOscillator();
    const gainNode = audioContext.createGain();
    
    oscillator.connect(gainNode);
    gainNode.connect(audioContext.destination);
    
    switch (type) {
      case "move":
        oscillator.frequency.value = 440;
        oscillator.type = "sine";
        gainNode.gain.setValueAtTime(0.1, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.1);
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.1);
        break;
      case "win":
        // Победный аккорд
        [440, 554, 659].forEach((freq, idx) => {
          const osc = audioContext.createOscillator();
          const gain = audioContext.createGain();
          osc.connect(gain);
          gain.connect(audioContext.destination);
          osc.frequency.value = freq;
          osc.type = "sine";
          gain.gain.setValueAtTime(0.15, audioContext.currentTime + idx * 0.1);
          gain.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.5 + idx * 0.1);
          osc.start(audioContext.currentTime + idx * 0.1);
          osc.stop(audioContext.currentTime + 0.5 + idx * 0.1);
        });
        break;
      case "gift":
        oscillator.frequency.value = 523;
        oscillator.type = "sine";
        gainNode.gain.setValueAtTime(0.12, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.2);
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.2);
        break;
      case "collect":
        oscillator.frequency.value = 659;
        oscillator.type = "sine";
        gainNode.gain.setValueAtTime(0.12, audioContext.currentTime);
        gainNode.gain.exponentialRampToValueAtTime(0.01, audioContext.currentTime + 0.15);
        oscillator.start(audioContext.currentTime);
        oscillator.stop(audioContext.currentTime + 0.15);
        break;
    }
  } catch (e) {
    // Игнорируем ошибки звука (браузер может блокировать автовоспроизведение)
    console.debug("Sound playback failed:", e);
  }
}

