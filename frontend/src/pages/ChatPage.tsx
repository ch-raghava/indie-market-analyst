import { useEffect, useRef, useState } from "react";
import { ArrowUp } from "lucide-react";
import { listSessions, streamChat } from "../lib/api";
import { useSession } from "../stores/session";
import { MessageBubble } from "../components/MessageBubble";
import { ProcessingIndicator } from "../components/ProcessingIndicator";

export function ChatPage() {
  const messages = useSession((s) => s.messages);
  const sessionId = useSession((s) => s.sessionId);
  const streaming = useSession((s) => s.streaming);
  const activeTool = useSession((s) => s.activeTool);
  const {
    pushUser,
    startAssistant,
    appendDelta,
    appendReasoning,
    pushHandoff,
    startToolCall,
    endToolCall,
    finalizeAssistant,
    setSession,
    setStreaming,
    setActiveTool,
    setSessions,
  } = useSession.getState();

  const [input, setInput] = useState("");
  const abortRef = useRef<AbortController | null>(null);
  const scrollRef = useRef<HTMLDivElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement | null>(null);

  useEffect(() => {
    scrollRef.current?.scrollTo({
      top: scrollRef.current.scrollHeight,
      behavior: "smooth",
    });
  }, [messages, streaming]);

  useEffect(() => {
    const el = textareaRef.current;
    if (!el) return;
    el.style.height = "auto";
    el.style.height = Math.min(el.scrollHeight, 200) + "px";
  }, [input]);

  const send = async () => {
    if (!input.trim() || streaming) return;
    pushUser(input);
    const assistantId = startAssistant();
    const prompt = input;
    setInput("");
    setStreaming(true);
    setActiveTool(null);
    abortRef.current = new AbortController();

    try {
      await streamChat(
        prompt,
        sessionId,
        (ev) => {
          if (ev.kind === "delta") {
            appendDelta(assistantId, String(ev.data));
          } else if (ev.kind === "reasoning_delta") {
            appendReasoning(assistantId, String(ev.data));
          } else if (ev.kind === "tool_call_start") {
            const d = ev.data;
            const cid = d.call_id || crypto.randomUUID();
            setActiveTool(d.name || "tool");
            startToolCall(assistantId, {
              call_id: cid,
              name: d.name || "tool",
              arguments: d.arguments || {},
              status: "running",
              started_at: Date.now(),
            });
          } else if (ev.kind === "tool_call_end") {
            const d = ev.data;
            if (d.call_id) {
              endToolCall(assistantId, d.call_id, d.result, d.duration_ms);
            }
            setActiveTool(null);
          } else if (ev.kind === "handoff") {
            const d = ev.data;
            if (d.session_id) setSession(d.session_id);
            if (d.to) pushHandoff(assistantId, d.to);
          } else if (ev.kind === "agent_updated") {
            pushHandoff(assistantId, ev.data.name);
          } else if (ev.kind === "final") {
            const d = ev.data;
            if (d.session_id) setSession(d.session_id);
            if (d.markdown) finalizeAssistant(assistantId, d.markdown);
          } else if (ev.kind === "error") {
            finalizeAssistant(
              assistantId,
              `**Error.** ${String(ev.data)}`
            );
          }
        },
        { signal: abortRef.current.signal }
      );
    } finally {
      setStreaming(false);
      setActiveTool(null);
      listSessions().then(setSessions).catch(() => {});
    }
  };

  const empty = messages.length === 0;

  return (
    <div className="chat">
      <div className="messages" ref={scrollRef}>
        {empty && (
          <div className="chat-empty">
            <h2>What do you want to research?</h2>
            <p>
              Ask about a stock, a setup, or request an end-of-day report.
              Tools and reasoning appear above the answer.
            </p>
          </div>
        )}
        {messages.map((m) => {
          const isLast = m.id === messages[messages.length - 1]?.id;
          return (
            <MessageBubble
              key={m.id}
              message={m}
              streaming={streaming && m.role === "assistant" && isLast}
              activeTool={
                streaming && m.role === "assistant" && isLast ? activeTool : null
              }
            />
          );
        })}
      </div>

      <div className="composer-area">
        <ProcessingIndicator streaming={streaming} activeTool={activeTool} />
        <form
          className="composer"
          onSubmit={(e) => {
            e.preventDefault();
            send();
          }}
        >
          <textarea
            ref={textareaRef}
            placeholder="Ask about a stock, setup, or request an EOD report…"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => {
              if (e.key === "Enter" && !e.shiftKey) {
                e.preventDefault();
                send();
              }
            }}
            rows={1}
            disabled={streaming}
          />
          <button
            type="submit"
            className="send"
            disabled={streaming || !input.trim()}
            aria-label="Send"
          >
            <ArrowUp size={16} />
          </button>
        </form>
        <div className="composer-hint">
          Research only. Not investment advice. Free-tier OpenRouter models by default.
        </div>
      </div>
    </div>
  );
}
