// Consts
const KEY = "intentdiff.annotator";

// validAnnotator reports whether a name is safe to use as part of a filename.
export function validAnnotator(name: string): boolean {
  return /^[A-Za-z0-9_-]{1,32}$/.test(name);
}

// getAnnotator returns the remembered annotator, or an empty string if none.
export function getAnnotator(): string {
  try {
    const stored = localStorage.getItem(KEY) ?? "";
    return validAnnotator(stored) ? stored : "";
  } catch {
    return ""; // private window, or site data blocked
  }
}

// setAnnotator remembers the annotator for the next session, if storage allows.
export function setAnnotator(name: string) {
  try {
    localStorage.setItem(KEY, name);
  } catch {
  }
}
