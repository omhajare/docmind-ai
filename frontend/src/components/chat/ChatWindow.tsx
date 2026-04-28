import { useCallback, useEffect, useRef, useState } from "react";
import { Send } from "lucide-react";
import { toast } from "sonner";

import { chatApi, type Message } from "@/api/chat.api";
import MessageBubble from "./MessageBubble";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Skeleton } from "@/components/ui/skeleton";

interface ChatWindowProps {
  sessionId: string | null;
  initialQuery?: string;
  onClearInitialQuery?: () => void;
}

export default function ChatWindow({ sessionId, initialQuery, onClearInitialQuery }: ChatWindowProps) {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [isSending, setIsSending] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const bottomRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    bottomRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Load messages when session changes
  useEffect(() => {
    if (!sessionId) {
      setMessages([]);
      return;
    }
    const load = async () => {
      setIsLoading(true);
      try {
        const { data } = await chatApi.getMessages(sessionId, 50, 0);
        setMessages(data);
      } catch {
        toast.error("Failed to load messages");
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [sessionId]);

  useEffect(scrollToBottom, [messages]);

  // Handle initial query from suggested questions
  useEffect(() => {
    if (initialQuery && sessionId && !isSending) {
      setInput(initialQuery);
      onClearInitialQuery?.();
      // Auto-submit
      handleSend(initialQuery);
    }
  }, [initialQuery, sessionId]);

  const handleSend = async (queryOverride?: string) => {
    const query = queryOverride || input.trim();
    if (!query || !sessionId || isSending) return;

    setInput("");
    setIsSending(true);

    // Optimistic user message
    const tempUserMsg: Message = {
      id: `temp-${Date.now()}`,
      session_id: sessionId,
      role: "user",
      content: query,
      sources: null,
      tools_used: null,
      confidence: null,
      created_at: new Date().toISOString(),
    };
    setMessages((prev) => [...prev, tempUserMsg]);

    try {
      const { data } = await chatApi.sendMessage(sessionId, query);
      // Replace temp message with real ones and add assistant response
      setMessages((prev) => {
        const withoutTemp = prev.filter((m) => m.id !== tempUserMsg.id);
        return [
          ...withoutTemp,
          { ...tempUserMsg, id: `user-${Date.now()}` },
          data,
        ];
      });
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to send message");
      setMessages((prev) => prev.filter((m) => m.id !== tempUserMsg.id));
    } finally {
      setIsSending(false);
    }
  };

  const handleDelete = async (messageId: string) => {
    try {
      await chatApi.deleteMessage(messageId);
      setMessages((prev) => prev.filter((m) => m.id !== messageId));
    } catch {
      toast.error("Failed to delete message");
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  if (!sessionId) {
    return (
      <div className="flex-1 flex items-center justify-center">
        <p className="text-muted-foreground">Select a chat or start a new one</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      <ScrollArea className="flex-1 px-4 py-4">
        <div className="space-y-4 max-w-3xl mx-auto">
          {isLoading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <div key={i} className={`flex ${i % 2 === 0 ? "justify-end" : "justify-start"}`}>
                <Skeleton className="h-16 w-64 rounded-2xl" />
              </div>
            ))
          ) : messages.length === 0 ? (
            <p className="text-center text-muted-foreground py-20">
              Start a conversation by typing a message below
            </p>
          ) : (
            messages.map((m) => (
              <MessageBubble key={m.id} message={m} onDelete={m.role === "user" ? handleDelete : undefined} />
            ))
          )}

          {isSending && (
            <div className="flex justify-start">
              <div className="bg-neutral-100 rounded-2xl px-4 py-3">
                <div className="flex items-center gap-1">
                  <span className="h-2 w-2 bg-primary/60 rounded-full animate-bounce [animation-delay:0ms]" />
                  <span className="h-2 w-2 bg-primary/60 rounded-full animate-bounce [animation-delay:150ms]" />
                  <span className="h-2 w-2 bg-primary/60 rounded-full animate-bounce [animation-delay:300ms]" />
                </div>
              </div>
            </div>
          )}
          <div ref={bottomRef} />
        </div>
      </ScrollArea>

      <div className="border-t border-neutral-200 p-4">
        <div className="flex gap-2 max-w-3xl mx-auto">
          <Input
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="Ask a question..."
            disabled={isSending}
            aria-label="Chat message input"
            className="flex-1"
          />
          <Button
            onClick={() => handleSend()}
            disabled={!input.trim() || isSending}
            size="icon"
            aria-label="Send message"
          >
            <Send className="h-4 w-4" />
          </Button>
        </div>
      </div>
    </div>
  );
}
