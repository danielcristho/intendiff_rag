// Consts
export const LOGGED_OUT = "intentdiff:logged-out";
// SESSION_PATHS answer 401 as part of logging in, so they must not trigger a logout.
const SESSION_PATHS = ["/api/login", "/api/session"];

// validAnnotator reports whether a name is safe to use as part of a filename.
export function validAnnotator(name: string): boolean {
  return /^[A-Za-z0-9_-]{1,32}$/.test(name);
}

// endsSession reports whether a response means the session cookie is gone or expired.
export function endsSession(path: string, status: number): boolean {
  return status === 401 && !SESSION_PATHS.includes(path);
}

export function announceLogout() {
  window.dispatchEvent(new Event(LOGGED_OUT));
}
