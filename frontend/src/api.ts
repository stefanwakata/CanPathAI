import type { ChatResponse, StatsResponse, UserProfile } from "./types";

const BASE = import.meta.env.VITE_API_URL ?? "";

async function request<T>(path: string, init?: RequestInit): Promise<T> {
  const resp = await fetch(`${BASE}${path}`, {
    headers: { "Content-Type": "application/json" },
    ...init,
  });
  if (!resp.ok) {
    const detail = await resp.text().catch(() => "");
    throw new Error(`HTTP ${resp.status}: ${detail.slice(0, 300)}`);
  }
  return resp.json() as Promise<T>;
}

export function sendChat(
  message: string,
  sessionId: string | null,
  language: string,
  profile: UserProfile | null,
): Promise<ChatResponse> {
  return request<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({
      message,
      session_id: sessionId,
      language,
      profile: profile ?? undefined,
    }),
  });
}

export function saveProfile(profile: UserProfile, sessionId: string | null): Promise<{ session_id: string }> {
  const qs = sessionId ? `?session_id=${encodeURIComponent(sessionId)}` : "";
  return request(`/api/profile${qs}`, { method: "POST", body: JSON.stringify(profile) });
}

export function fetchStats(): Promise<StatsResponse> {
  return request<StatsResponse>("/api/stats");
}
