import { useState } from "react";
import clsx from "clsx";
import { Brain, ChevronDown, ChevronRight } from "lucide-react";
import type { ChatMessage } from "../stores/session";
import { ToolCallCard } from "./ToolCallCard";

export function ThinkingDrawer({
  message,
  streaming,
  activeTool,
}: {
  message: ChatMessage;
  streaming: boolean;
  activeTool: string | null;
}) {
  const [open, setOpen] = useState(false);
  const toolCount = message.toolCalls?.length || 0;
  const handoffs = message.handoffs || [];
  const reasoning = (message.reasoning || "").trim();

  if (!streaming && toolCount === 0 && handoffs.length === 0 && !reasoning) {
    return null;
  }

  const totalDuration = (message.toolCalls || [])
    .filter((c) => typeof c.duration_ms === "number")
    .reduce((sum, c) => sum + (c.duration_ms || 0), 0);
  const durationLabel =
    totalDuration > 0
      ? totalDuration < 1000
        ? `${totalDuration}ms`
        : `${(totalDuration / 1000).toFixed(1)}s`
      : null;

  return (
    <div className={clsx("thinking", streaming && "streaming")}>
      <button
        type="button"
        className="thinking-summary"
        onClick={() => setOpen((v) => !v)}
      >
        <span className="thinking-icon">
          <Brain size={14} />
        </span>
        {streaming ? (
          <span className="thinking-label">
            Thinking{activeTool ? ` · running ${activeTool}` : "…"}
          </span>
        ) : (
          <span className="thinking-label">
            Reasoning
            {toolCount > 0 && ` · ${toolCount} tool${toolCount === 1 ? "" : "s"}`}
            {durationLabel && ` · ${durationLabel}`}
          </span>
        )}
        <span className="thinking-caret">
          {open ? <ChevronDown size={14} /> : <ChevronRight size={14} />}
        </span>
      </button>

      {open && (
        <div className="thinking-body">
          {handoffs.length > 0 && (
            <div className="handoff-line">
              {handoffs.map((h, i) => (
                <span key={i} className="handoff-pill">
                  → {h}
                </span>
              ))}
            </div>
          )}
          {(message.toolCalls || []).map((c) => (
            <ToolCallCard key={c.call_id} call={c} />
          ))}
          {reasoning && <div className="reasoning-text">{reasoning}</div>}
        </div>
      )}
    </div>
  );
}
