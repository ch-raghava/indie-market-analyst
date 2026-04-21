import { useMemo } from "react";
import clsx from "clsx";
import { Trash2 } from "lucide-react";
import type { SessionSummary } from "../lib/api";

type Group = { label: string; rows: SessionSummary[] };

function groupSessions(rows: SessionSummary[]): Group[] {
  const now = Date.now() / 1000;
  const day = 86400;
  const buckets: Record<string, SessionSummary[]> = {
    Today: [],
    Yesterday: [],
    "Last 7 days": [],
    Older: [],
  };
  for (const r of rows) {
    const age = now - (r.last_activity || r.created_at);
    if (age < day) buckets.Today.push(r);
    else if (age < 2 * day) buckets.Yesterday.push(r);
    else if (age < 7 * day) buckets["Last 7 days"].push(r);
    else buckets.Older.push(r);
  }
  return (["Today", "Yesterday", "Last 7 days", "Older"] as const)
    .map((label) => ({ label, rows: buckets[label] }))
    .filter((g) => g.rows.length > 0);
}

type Props = {
  sessions: SessionSummary[];
  activeId: string | null;
  onSelect: (id: string) => void;
  onDelete: (id: string) => void;
  loading: boolean;
};

export function SessionList({ sessions, activeId, onSelect, onDelete, loading }: Props) {
  const groups = useMemo(() => groupSessions(sessions), [sessions]);

  if (loading && sessions.length === 0) {
    return <div className="session-list-empty">Loading…</div>;
  }
  if (sessions.length === 0) {
    return <div className="session-list-empty">No chats yet.</div>;
  }

  return (
    <div className="session-list">
      {groups.map((g) => (
        <div key={g.label} className="session-group">
          <div className="session-group-label">{g.label}</div>
          {g.rows.map((s) => (
            <div
              key={s.id}
              className={clsx("session-row", s.id === activeId && "active")}
              onClick={() => onSelect(s.id)}
              role="button"
              tabIndex={0}
              onKeyDown={(e) => {
                if (e.key === "Enter") onSelect(s.id);
              }}
            >
              <div className="title">{s.title}</div>
              <button
                type="button"
                className="delete"
                aria-label="Delete chat"
                onClick={(e) => {
                  e.stopPropagation();
                  if (confirm("Delete this chat? This cannot be undone.")) {
                    onDelete(s.id);
                  }
                }}
              >
                <Trash2 size={13} />
              </button>
            </div>
          ))}
        </div>
      ))}
    </div>
  );
}
