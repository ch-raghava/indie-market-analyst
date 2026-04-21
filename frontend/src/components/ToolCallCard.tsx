import { useState } from "react";
import clsx from "clsx";
import { ChevronDown, ChevronRight } from "lucide-react";
import type { ToolCall } from "../stores/session";

function formatArgs(args: Record<string, unknown>): string {
  const entries = Object.entries(args);
  if (entries.length === 0) return "";
  return entries
    .map(([k, v]) => `${k}: ${typeof v === "string" ? v : JSON.stringify(v)}`)
    .join("  ");
}

function summarizeResult(result: unknown): string {
  if (result == null) return "—";
  if (typeof result === "string")
    return result.length > 120 ? result.slice(0, 117) + "…" : result;
  if (typeof result === "number" || typeof result === "boolean") return String(result);
  try {
    const s = JSON.stringify(result);
    return s.length > 120 ? s.slice(0, 117) + "…" : s;
  } catch {
    return String(result);
  }
}

export function ToolCallCard({ call }: { call: ToolCall }) {
  const [open, setOpen] = useState(false);
  const running = call.status === "running";
  const duration =
    call.duration_ms != null
      ? call.duration_ms < 1000
        ? `${call.duration_ms}ms`
        : `${(call.duration_ms / 1000).toFixed(2)}s`
      : "…";

  return (
    <div className={clsx("tool-card", running && "running")}>
      <div
        className="tool-card-head"
        onClick={() => setOpen((v) => !v)}
      >
        <span className="name">{call.name || "tool"}</span>
        <span className="duration">{duration}</span>
        <div className={clsx("status-dot", call.status)} />
      </div>
      {open && (
        <div className="tool-card-body">
          <div className="args">
            {JSON.stringify(call.arguments, null, 2)}
          </div>
          <div className="result">
            {running
              ? "running…"
              : typeof call.result === "string"
              ? call.result
              : JSON.stringify(call.result, null, 2)}
          </div>
        </div>
      )}
    </div>
  );
}
