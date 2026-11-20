/** Bangla text-to-speech through the browser Web Speech API. */
export function speakBn(text: string, onEnd?: () => void): boolean {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) return false;
  window.speechSynthesis.cancel();
  const u = new SpeechSynthesisUtterance(text);
  u.lang = "bn-BD";
  u.rate = 0.9;
  const bn = window.speechSynthesis.getVoices().find((v) => v.lang.toLowerCase().startsWith("bn"));
  if (bn) u.voice = bn;
  u.onend = () => onEnd?.();
  u.onerror = () => onEnd?.();
  window.speechSynthesis.speak(u);
  return true;
}
export const stopSpeech = () => typeof window !== "undefined" && "speechSynthesis" in window && window.speechSynthesis.cancel();
