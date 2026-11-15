export function safeMedia(value) {
  if (typeof value !== "string" || !value || /[\s\\\u0000-\u001f]/.test(value)) return null;
  if (value.startsWith("/media/")) return value;
  try { const u = new URL(value); return u.protocol === "https:" && !u.username && !u.password ? value : null; } catch { return null; }
}
export function isImageUrl(value) {
  return !!safeMedia(value) && /\.(png|jpe?g|gif|webp|avif)(?:[?#]|$)/i.test(value);
}
export function isVideoUrl(value) {
  return !!safeMedia(value) && /\.(mp4|webm)(?:[?#]|$)/i.test(value);
}
