// Photo files live in frontend/public/fighter_photos/<First>_<Last>.jpg.
// card.json stores absolute URLs but analyses.json sometimes has null — derive
// from name as a fallback. The browser's onError handler swaps in a letter
// circle if the file 404s, so an incorrect guess degrades gracefully.

export function fighterPhotoUrl(name: string | undefined | null): string | null {
  if (!name) return null;
  const safe = name
    .trim()
    .replace(/[^A-Za-z0-9 ]/g, "") // strip punctuation
    .replace(/\s+/g, "_");
  if (!safe) return null;
  return `/fighter_photos/${safe}.jpg`;
}

export function resolvePhotoUrl(
  explicit: string | null | undefined,
  fighterName: string | undefined | null
): string | null {
  // 1. Use explicit URL if provided (already full URL or relative path)
  if (explicit) {
    // Strip the legacy localhost:8000 prefix that older code injected.
    if (explicit.startsWith("http://localhost:8000")) {
      return explicit.replace("http://localhost:8000", "");
    }
    return explicit;
  }
  // 2. Otherwise derive from name
  return fighterPhotoUrl(fighterName);
}
