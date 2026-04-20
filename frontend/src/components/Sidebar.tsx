import { useCallback, useEffect, useMemo, useState } from "react";
import { NavLink } from "react-router-dom";
import { Plus, Search } from "lucide-react";
import {
  deleteSession,
  listSessions,
  searchSessions,
  type SessionSummary,
} from "../lib/api";
import { useSession } from "../stores/session";
import { SessionList } from "./SessionList";
import { ThemeToggle } from "./ThemeToggle";

export function Sidebar({
  onSelectSession,
  onNewChat,
}: {
  onSelectSession: (id: string) => void;
  onNewChat: () => void;
}) {
  const sessions = useSession((s) => s.sessions);
  const setSessions = useSession((s) => s.setSessions);
  const setLoading = useSession((s) => s.setSessionsLoading);
  const loading = useSession((s) => s.sessionsLoading);
  const activeId = useSession((s) => s.sessionId);
  const removeLocal = useSession((s) => s.removeSessionLocally);

  const [query, setQuery] = useState("");
  const [searchRows, setSearchRows] = useState<SessionSummary[] | null>(null);

  const refresh = useCallback(async () => {
    setLoading(true);
    try {
      const rows = await listSessions();
      setSessions(rows);
    } finally {
      setLoading(false);
    }
  }, [setLoading, setSessions]);

  useEffect(() => {
    refresh();
  }, [refresh]);

  useEffect(() => {
    const q = query.trim();
    if (!q) {
      setSearchRows(null);
      return;
    }
    const timer = setTimeout(async () => {
      const matches = await searchSessions(q);
      const ids = new Set(matches.map((m) => m.session_id));
      setSearchRows(sessions.filter((s) => ids.has(s.id)));
    }, 220);
    return () => clearTimeout(timer);
  }, [query, sessions]);

  const displayed = useMemo(
    () => (searchRows !== null ? searchRows : sessions),
    [searchRows, sessions]
  );

  const handleDelete = async (id: string) => {
    const ok = await deleteSession(id);
    if (ok) removeLocal(id);
  };

  return (
    <aside className="sidebar">
      <div className="sidebar-header">
        <div className="brand">indie-market-analyst</div>
        <button
          type="button"
          className="new-chat-btn"
          onClick={() => {
            onNewChat();
            refresh();
          }}
        >
          <Plus size={14} />
          New chat
        </button>
      </div>

      <div className="sidebar-search">
        <Search size={14} />
        <input
          type="text"
          placeholder="Search chats"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
      </div>

      <SessionList
        sessions={displayed}
        activeId={activeId}
        onSelect={onSelectSession}
        onDelete={handleDelete}
        loading={loading}
      />

      <nav className="sidebar-nav">
        <NavLink to="/chat" className={({ isActive }) => (isActive ? "active" : "")}>
          Chat
        </NavLink>
        <NavLink to="/runs" className={({ isActive }) => (isActive ? "active" : "")}>
          Runs
        </NavLink>
      </nav>

      <div className="sidebar-footer">
        <ThemeToggle />
      </div>
    </aside>
  );
}
