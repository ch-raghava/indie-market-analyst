import { fetchEventSource } from "@microsoft/fetch-event-source";

export type ToolCallStart = {
  call_id: string | null;
  name: string | null;
  arguments: Record<string, unknown>;
};

export type ToolCallEnd = {
  call_id: string | null;
  name: string | null;
  result: unknown;
  duration_ms: number | null;
};

export type StreamEvent =
  | { kind: "delta"; data: string }
  | { kind: "reasoning_delta"; data: string }
  | { kind: "tool_call_start"; data: ToolCallStart }
  | { kind: "tool_call_end"; data: ToolCallEnd }
  | { kind: "handoff"; data: { to?: string; team?: string; session_id?: string } }
  | { kind: "agent_updated"; data: { name: string } }
  | { kind: "final"; data: { markdown: string; session_id: string } }
  | { kind: "error"; data: string };

export async function streamChat(
  message: string,
  sessionId: string | null,
  onEvent: (ev: StreamEvent) => void,
  opts?: { team?: string; signal?: AbortSignal }
) {
  await fetchEventSource("/chat/stream", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, session_id: sessionId, team: opts?.team }),
    signal: opts?.signal,
    onmessage(ev) {
      try {
        const parsed = JSON.parse(ev.data);
        onEvent({ kind: ev.event as StreamEvent["kind"], data: parsed } as StreamEvent);
      } catch {
        onEvent({ kind: ev.event as StreamEvent["kind"], data: ev.data } as StreamEvent);
      }
    },
    onerror(err) {
      onEvent({ kind: "error", data: String(err) });
      throw err;
    },
  });
}

export type SessionSummary = {
  id: string;
  created_at: number;
  last_activity: number;
  message_count: number;
  preview: string;
  title: string;
};

export type StoredMessage = {
  id: string;
  role: "user" | "assistant";
  content: string;
  payload: Record<string, unknown>;
  created_at: number;
};

export async function listSessions(limit = 200): Promise<SessionSummary[]> {
  const r = await fetch(`/sessions?limit=${limit}`);
  if (!r.ok) return [];
  return r.json();
}

export async function searchSessions(q: string, limit = 50) {
  const r = await fetch(`/sessions/search?q=${encodeURIComponent(q)}&limit=${limit}`);
  if (!r.ok) return [];
  return r.json() as Promise<
    { session_id: string; snippet: string; at: number; role: string }[]
  >;
}

export async function deleteSession(id: string): Promise<boolean> {
  const r = await fetch(`/sessions/${id}`, { method: "DELETE" });
  return r.ok;
}

export async function getSessionMessages(id: string): Promise<StoredMessage[]> {
  const r = await fetch(`/sessions/${id}/messages`);
  if (!r.ok) return [];
  return r.json();
}

export async function listRuns(): Promise<
  { id: string; kind: string; status: string; session_id: string; created_at: number }[]
> {
  const r = await fetch("/runs");
  return r.json();
}
