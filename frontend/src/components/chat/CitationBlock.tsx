import type { SourceInfo } from "@/api/chat.api";
import { FileText, Globe } from "lucide-react";

interface CitationBlockProps {
  sources: SourceInfo | null;
}

export default function CitationBlock({ sources }: CitationBlockProps) {
  if (!sources) return null;

  const hasDocs = sources.document_sources && sources.document_sources.length > 0;
  const hasWeb = sources.web_sources && sources.web_sources.length > 0;

  if (!hasDocs && !hasWeb) return null;

  return (
    <div className="mt-2 space-y-2">
      {hasDocs && (
        <div className="rounded-lg border border-neutral-200 bg-neutral-50 p-3">
          <p className="text-xs font-medium text-muted-foreground mb-2 flex items-center gap-1.5">
            <FileText className="h-3.5 w-3.5" /> From Your Documents
          </p>
          <div className="space-y-1.5">
            {sources.document_sources.map((s, i) => (
              <div key={i} className="text-xs text-muted-foreground">
                <span className="font-medium text-foreground">{s.filename}</span>
                {s.page_number && <span> · p.{s.page_number}</span>}
                <span> · {(s.cosine_score * 100).toFixed(0)}% match</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {hasWeb && (
        <div className="rounded-lg border border-blue-100 bg-blue-50/50 p-3">
          <p className="text-xs font-medium text-muted-foreground mb-2 flex items-center gap-1.5">
            <Globe className="h-3.5 w-3.5" /> From the Web
          </p>
          <div className="space-y-1.5">
            {sources.web_sources.map((s, i) => (
              <div key={i} className="text-xs">
                <a
                  href={s.url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-primary hover:underline font-medium"
                >
                  {s.title}
                </a>
                <p className="text-muted-foreground mt-0.5">{s.snippet.slice(0, 120)}...</p>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
