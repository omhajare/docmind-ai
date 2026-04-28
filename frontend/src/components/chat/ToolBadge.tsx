import { Badge } from "@/components/ui/badge";

interface ToolBadgeProps {
  tools: string[] | null;
}

export default function ToolBadge({ tools }: ToolBadgeProps) {
  if (!tools || tools.length === 0) return null;

  const labels: Record<string, string> = {
    rag_search: "Documents",
    web_search: "Web",
  };

  return (
    <div className="flex gap-1">
      {tools.map((tool) => (
        <Badge key={tool} variant="outline" className="text-[10px] px-1.5 py-0 h-4 font-normal">
          {labels[tool] || tool}
        </Badge>
      ))}
    </div>
  );
}
