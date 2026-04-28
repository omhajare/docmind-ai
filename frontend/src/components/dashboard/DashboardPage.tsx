import { useState, useCallback } from "react";
import { useAuth } from "@/auth/AuthContext";
import { Button } from "@/components/ui/button";
import DocumentPanel from "@/components/documents/DocumentPanel";
import SessionSidebar from "@/components/chat/SessionSidebar";
import ChatWindow from "@/components/chat/ChatWindow";
import { LogOut, FlaskConical, Shield } from "lucide-react";
import { useNavigate, Link } from "react-router-dom";
import type { Session } from "@/api/chat.api";

export default function DashboardPage() {
  const { user, logout } = useAuth();
  const navigate = useNavigate();
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);
  const [initialQuery, setInitialQuery] = useState<string>("");

  const handleLogout = async () => {
    await logout();
    navigate("/login");
  };

  const handleNewSession = useCallback((session: Session) => {
    setActiveSessionId(session.id);
  }, []);

  const handleQuestionClick = useCallback(
    async (question: string) => {
      if (!activeSessionId) {
        // Create a session first, then send the question
        const { chatApi } = await import("@/api/chat.api");
        try {
          const { data } = await chatApi.createSession();
          setActiveSessionId(data.id);
          setInitialQuery(question);
        } catch {
          // If we have sessions, just set the query
          setInitialQuery(question);
        }
      } else {
        setInitialQuery(question);
      }
    },
    [activeSessionId]
  );

  return (
    <div className="flex h-screen bg-neutral-50">
      {/* Left Sidebar — Chat Sessions */}
      <aside className="w-64 border-r border-neutral-200 bg-white p-4 flex flex-col">
        <h1 className="text-lg font-semibold text-primary mb-4">DocMind AI</h1>
        <div className="flex-1 overflow-hidden">
          <SessionSidebar
            activeSessionId={activeSessionId}
            onSelectSession={setActiveSessionId}
            onNewSession={handleNewSession}
          />
        </div>
        <div className="border-t border-neutral-200 pt-3 mt-3 space-y-1">
          <Link to="/research">
            <Button variant="ghost" size="sm" className="w-full justify-start gap-2">
              <FlaskConical className="h-4 w-4" />
              Deep Research
            </Button>
          </Link>
          <Link to="/admin">
            <Button variant="ghost" size="sm" className="w-full justify-start gap-2">
              <Shield className="h-4 w-4" />
              Admin
            </Button>
          </Link>
          <p className="text-xs text-muted-foreground truncate pt-2 px-2">{user?.email}</p>
          <Button variant="ghost" size="sm" className="w-full justify-start gap-2" onClick={handleLogout}>
            <LogOut className="h-4 w-4" />
            Sign out
          </Button>
        </div>
      </aside>

      {/* Center — Chat Window */}
      <main className="flex-1 flex flex-col">
        <ChatWindow
          sessionId={activeSessionId}
          initialQuery={initialQuery}
          onClearInitialQuery={() => setInitialQuery("")}
        />
      </main>

      {/* Right Panel — Documents */}
      <aside className="w-80 border-l border-neutral-200 bg-white p-4">
        <DocumentPanel onQuestionClick={handleQuestionClick} />
      </aside>
    </div>
  );
}
