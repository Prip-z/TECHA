import type { GameDraftState, StaffUser } from "../types/models";

const TOKEN_KEY = "mafia-organizator-token";
const USER_KEY = "mafia-organizator-user";

export function saveSession(token: string, user: StaffUser) {
  localStorage.setItem(TOKEN_KEY, token);
  localStorage.setItem(USER_KEY, JSON.stringify(user));
}

export function loadSession() {
  const token = localStorage.getItem(TOKEN_KEY);
  const userRaw = localStorage.getItem(USER_KEY);
  if (!token || !userRaw) {
    return null;
  }

  try {
    return {
      token,
      user: JSON.parse(userRaw) as StaffUser,
    };
  } catch {
    return null;
  }
}

export function clearSession() {
  localStorage.removeItem(TOKEN_KEY);
  localStorage.removeItem(USER_KEY);
}

function draftKey(gameId: number) {
  return `mafia-organizator-draft-${gameId}`;
}

export function loadGameDraft(gameId: number): GameDraftState | null {
  const raw = localStorage.getItem(draftKey(gameId));
  if (!raw) {
    return null;
  }
  try {
    return JSON.parse(raw) as GameDraftState;
  } catch {
    return null;
  }
}

export function saveGameDraft(gameId: number, draft: GameDraftState) {
  localStorage.setItem(draftKey(gameId), JSON.stringify(draft));
}
