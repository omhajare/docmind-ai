import { useCallback, useEffect, useState } from "react";
import { MessageSquarePlus, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { chatApi, type Session } from "@/api/chat.api";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from "@/components/ui/alert-dialog";

interface SessionSidebarProps {
  activeSessionId: string | null;
  onSelectSession: (id: string) => void;
  onNewSession: (session: Session) => void;
}

export default function SessionSidebar({
  activeSessionId,
  onSelectSession,
  onNewSession,
}: SessionSidebarProps) {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  const fetchSessions = useCallback(async () => {
    try {
      const { data } = await chatApi.listSessions();
      setSessions(data);
    } catch {
      // silent
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchSessions();
  }, [fetchSessions]);

  // Refresh sessions when active session changes (e.g., title auto-update)
  useEffect(() => {
    if (activeSessionId) {
      const timer = setTimeout(fetchSessions, 1000);
      return () => clearTimeout(timer);
    }
  }, [activeSessionId, fetchSessions]);

  const handleNewSession = async () => {
    try {
      const { data } = await chatApi.createSession();
      setSessions((prev) => [data, ...prev]);
      onNewSession(data);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to create session");
    }
  };

  const handleDelete = async (sessionId: string) => {
    try {
      await chatApi.deleteSession(sessionId);
      setSessions((prev) => prev.filter((s) => s.id !== sessionId));
      if (activeSessionId === sessionId) {
        onSelectSession("");
      }
      toast.success("Chat deleted");
    } catch {
      toast.error("Failed to delete chat");
    }
  };

  return (
    <div className="flex flex-col h-full">
      <Button
        onClick={handleNewSession}
        variant="outline"
        className="w-full justify-start gap-2 mb-3"
      >
        <MessageSquarePlus className="h-4 w-4" />
        New Chat
      </Button>

      <ScrollArea className="flex-1">
        <div className="space-y-1">
          {isLoading ? (
            Array.from({ length: 4 }).map((_, i) => (
              <Skeleton key={i} className="h-9 rounded-lg" />
            ))
          ) : sessions.length === 0 ? (
            <p className="text-xs text-muted-foreground text-center py-4">
              No chats yet
            </p>
          ) : (
            sessions.map((session) => (
              <div
                key={session.id}
                className={`group flex items-center gap-1 rounded-lg px-3 py-2 text-sm cursor-pointer transition-colors ${
                  activeSessionId === session.id
                    ? "bg-primary/10 text-primary font-medium"
                    : "hover:bg-neutral-100 text-foreground"
                }`}
                onClick={() => onSelectSession(session.id)}
              >
                <span className="truncate flex-1">{session.title}</span>
                <AlertDialog>
                  <AlertDialogTrigger asChild>
                    <Button
                      variant="ghost"
                      size="icon"
                      className="h-6 w-6 opacity-0 group-hover:opacity-100 shrink-0"
                      onClick={(e) => e.stopPropagation()}
                      aria-label={`Delete ${session.title}`}
                    >
                      <Trash2 className="h-3 w-3" />
                    </Button>
                  </AlertDialogTrigger>
                  <AlertDialogContent>
                    <AlertDialogHeader>
                      <AlertDialogTitle>Delete chat?</AlertDialogTitle>
                      <AlertDialogDescription>
                        This will permanently delete this chat and all its messages.
                      </AlertDialogDescription>
                    </AlertDialogHeader>
                    <AlertDialogFooter>
                      <AlertDialogCancel>Cancel</AlertDialogCancel>
                      <AlertDialogAction
                        onClick={() => handleDelete(session.id)}
                        className="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                      >
                        Delete
                      </AlertDialogAction>
                    </AlertDialogFooter>
                  </AlertDialogContent>
                </AlertDialog>
              </div>
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
