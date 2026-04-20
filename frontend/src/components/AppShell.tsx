import { Outlet, useNavigate } from "react-router-dom";
import { Sidebar } from "./Sidebar";
import { useSession } from "../stores/session";
import { getSessionMessages } from "../lib/api";
import type { ChatMessage } from "../stores/session";

export function AppShell() {
  const navigate = useNavigate();
  const setSession = useSession((s) => s.setSession);
  const loadMessages = useSession((s) => s.loadMessages);
  const resetConversation = useSession((s) => s.resetConversation);

  const handleSelectSession = async (id: string) => {
    const rows = await getSessionMessages(id);
    const messages: ChatMessage[] = rows.map((r) => ({
      id: r.id,
      role: r.role,
      text: r.content,
    }));
    setSession(id);
    loadMessages(messages);
    navigate("/chat");
  };

  const handleNewChat = () => {
    resetConversation();
    navigate("/chat");
  };

  return (
    <div className="app">
      <Sidebar
        onSelectSession={handleSelectSession}
        onNewChat={handleNewChat}
      />
      <main className="main">
        <Outlet />
      </main>
    </div>
  );
}
