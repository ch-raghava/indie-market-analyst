import { create } from "zustand";
import type { SessionSummary } from "../lib/api";

export type ToolCall = {
  call_id: string;
  name: string;
  arguments: Record<string, unknown>;
  result?: unknown;
  duration_ms?: number | null;
  status: "running" | "done";
  started_at: number;
};

export type ChatMessage = {
  id: string;
  role: "user" | "assistant";
  text: string;
  reasoning?: string;
  toolCalls?: ToolCall[];
  handoffs?: string[];
  durationMs?: number;
};

type Theme = "light" | "dark";

type State = {
  // current conversation
  sessionId: string | null;
  messages: ChatMessage[];
  streaming: boolean;
  activeTool: string | null;

  // sidebar / sessions
  sessions: SessionSummary[];
  sessionsLoading: boolean;

  // theme
  theme: Theme;

  // actions — conversation
  setSession: (id: string | null) => void;
  resetConversation: () => void;
  loadMessages: (messages: ChatMessage[]) => void;
  pushUser: (text: string) => string;
  startAssistant: () => string;
  appendDelta: (id: string, delta: string) => void;
  appendReasoning: (id: string, delta: string) => void;
  pushHandoff: (id: string, to: string) => void;
  startToolCall: (id: string, call: ToolCall) => void;
  endToolCall: (
    id: string,
    call_id: string | null,
    result: unknown,
    duration_ms: number | null
  ) => void;
  finalizeAssistant: (id: string, text: string) => void;
  setStreaming: (b: boolean) => void;
  setActiveTool: (name: string | null) => void;

  // actions — sidebar
  setSessions: (rows: SessionSummary[]) => void;
  setSessionsLoading: (b: boolean) => void;
  removeSessionLocally: (id: string) => void;

  // actions — theme
  setTheme: (t: Theme) => void;
  toggleTheme: () => void;
};

const readInitialTheme = (): Theme => {
  if (typeof document === "undefined") return "light";
  const attr = document.documentElement.dataset.theme;
  if (attr === "light" || attr === "dark") return attr;
  return "light";
};

export const useSession = create<State>((set, get) => ({
  sessionId: null,
  messages: [],
  streaming: false,
  activeTool: null,
  sessions: [],
  sessionsLoading: false,
  theme: readInitialTheme(),

  setSession: (id) => set({ sessionId: id }),
  resetConversation: () =>
    set({ sessionId: null, messages: [], activeTool: null, streaming: false }),
  loadMessages: (messages) => set({ messages }),

  pushUser: (text) => {
    const id = crypto.randomUUID();
    set({ messages: [...get().messages, { id, role: "user", text }] });
    return id;
  },
  startAssistant: () => {
    const id = crypto.randomUUID();
    set({
      messages: [
        ...get().messages,
        {
          id,
          role: "assistant",
          text: "",
          reasoning: "",
          toolCalls: [],
          handoffs: [],
        },
      ],
    });
    return id;
  },
  appendDelta: (id, delta) =>
    set({
      messages: get().messages.map((m) =>
        m.id === id ? { ...m, text: m.text + delta } : m
      ),
    }),
  appendReasoning: (id, delta) =>
    set({
      messages: get().messages.map((m) =>
        m.id === id ? { ...m, reasoning: (m.reasoning || "") + delta } : m
      ),
    }),
  pushHandoff: (id, to) =>
    set({
      messages: get().messages.map((m) =>
        m.id === id ? { ...m, handoffs: [...(m.handoffs || []), to] } : m
      ),
    }),
  startToolCall: (id, call) =>
    set({
      messages: get().messages.map((m) =>
        m.id === id ? { ...m, toolCalls: [...(m.toolCalls || []), call] } : m
      ),
    }),
  endToolCall: (id, call_id, result, duration_ms) =>
    set({
      messages: get().messages.map((m) => {
        if (m.id !== id) return m;
        const calls = (m.toolCalls || []).slice();
        let idx = call_id ? calls.findIndex((c) => c.call_id === call_id) : -1;
        if (idx < 0) {
          for (let i = calls.length - 1; i >= 0; i--) {
            if (calls[i].status === "running") { idx = i; break; }
          }
        }
        if (idx >= 0) {
          calls[idx] = { ...calls[idx], result, duration_ms, status: "done" };
        }
        return { ...m, toolCalls: calls };
      }),
    }),
  finalizeAssistant: (id, text) =>
    set({
      messages: get().messages.map((m) =>
        m.id === id ? { ...m, text } : m
      ),
    }),
  setStreaming: (b) => set({ streaming: b }),
  setActiveTool: (name) => set({ activeTool: name }),

  setSessions: (rows) => set({ sessions: rows }),
  setSessionsLoading: (b) => set({ sessionsLoading: b }),
  removeSessionLocally: (id) =>
    set({
      sessions: get().sessions.filter((s) => s.id !== id),
      ...(get().sessionId === id ? { sessionId: null, messages: [] } : {}),
    }),

  setTheme: (t) => {
    try {
      localStorage.setItem("ima-theme", t);
    } catch {
      /* ignore */
    }
    if (typeof document !== "undefined") {
      document.documentElement.dataset.theme = t;
    }
    set({ theme: t });
  },
  toggleTheme: () => {
    const next: Theme = get().theme === "light" ? "dark" : "light";
    get().setTheme(next);
  },
}));
