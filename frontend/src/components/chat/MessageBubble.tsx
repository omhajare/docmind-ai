import type { Message } from "@/api/chat.api";
import CitationBlock from "./CitationBlock";
import ConfidenceBar from "./ConfidenceBar";
import ToolBadge from "./ToolBadge";
import { Trash2 } from "lucide-react";
import { Button } from "@/components/ui/button";

interface MessageBubbleProps {
  message: Message;
  onDelete?: (id: string) => void;
}

export default function MessageBubble({ message, onDelete }: MessageBubbleProps) {
  const isUser = message.role === "user";

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} group`}>
      <div
        className={`max-w-[80%] rounded-2xl px-4 py-3 ${
          isUser
            ? "bg-primary text-primary-foreground"
            : "bg-neutral-100 text-foreground"
        }`}
      >
        <div className="text-sm whitespace-pre-wrap break-words">{message.content}</div>

        {!isUser && (
          <div className="mt-2 space-y-1.5">
            <div className="flex items-center gap-2">
              <ConfidenceBar confidence={message.confidence} />
              <ToolBadge tools={message.tools_used} />
            </div>
            <CitationBlock sources={message.sources} />
          </div>
        )}

        {isUser && onDelete && (
          <div className="flex justify-end mt-1 opacity-0 group-hover:opacity-100 transition-opacity">
            <Button
              variant="ghost"
              size="icon"
              className="h-5 w-5 text-primary-foreground/60 hover:text-primary-foreground"
              onClick={() => onDelete(message.id)}
              aria-label="Delete message"
            >
              <Trash2 className="h-3 w-3" />
            </Button>
          </div>
        )}
      </div>
    </div>
  );
}
