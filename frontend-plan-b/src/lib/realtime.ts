function resolveWsBaseUrl() {
  const configuredUrl = import.meta.env.VITE_WS_BASE_URL as string | undefined;
  if (configuredUrl) {
    return configuredUrl;
  }

  if (typeof window !== "undefined") {
    const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
    return `${protocol}//${window.location.hostname}:8000`;
  }

  return "ws://localhost:8000";
}

const WS_BASE_URL = resolveWsBaseUrl();

export function buildRoomSocketUrl(roomId: string, token: string) {
  return `${WS_BASE_URL}/ws/sync/${roomId}?token=${encodeURIComponent(token)}`;
}
