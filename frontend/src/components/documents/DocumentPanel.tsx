import { useCallback, useEffect, useState } from "react";
import { Search } from "lucide-react";

import {
  documentsApi,
  type Document,
  type SuggestedQuestion,
  type UploadResponse,
} from "@/api/documents.api";
import UploadDropzone from "./UploadDropzone";
import DocumentCard from "./DocumentCard";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { ScrollArea } from "@/components/ui/scroll-area";

interface DocumentPanelProps {
  onQuestionClick?: (question: string) => void;
}

export default function DocumentPanel({ onQuestionClick }: DocumentPanelProps) {
  const [documents, setDocuments] = useState<Document[]>([]);
  const [questionsMap, setQuestionsMap] = useState<Record<string, SuggestedQuestion[]>>({});
  const [docCount, setDocCount] = useState(0);
  const [docLimit, setDocLimit] = useState(5);
  const [searchQuery, setSearchQuery] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  const fetchDocuments = useCallback(async () => {
    try {
      const { data } = await documentsApi.list();
      setDocuments(data.documents);
      setDocCount(data.document_count);
      setDocLimit(data.document_limit);
    } catch {
      // silent — user might not be authenticated yet
    } finally {
      setIsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchDocuments();
  }, [fetchDocuments]);

  const handleUploadComplete = useCallback((data: UploadResponse) => {
    setDocuments((prev) => [data.document, ...prev]);
    setDocCount((prev) => prev + 1);
    if (data.suggested_questions.length > 0) {
      setQuestionsMap((prev) => ({
        ...prev,
        [data.document.id]: data.suggested_questions,
      }));
    }
  }, []);

  const handleDelete = useCallback((docId: string) => {
    setDocuments((prev) => prev.filter((d) => d.id !== docId));
    setDocCount((prev) => prev - 1);
    setQuestionsMap((prev) => {
      const copy = { ...prev };
      delete copy[docId];
      return copy;
    });
  }, []);

  const loadQuestions = useCallback(
    async (docId: string) => {
      if (questionsMap[docId]) return;
      try {
        const { data } = await documentsApi.getSuggestedQuestions(docId);
        setQuestionsMap((prev) => ({ ...prev, [docId]: data }));
      } catch {
        // silent
      }
    },
    [questionsMap]
  );

  // Load questions for each document on mount
  useEffect(() => {
    documents.forEach((d) => loadQuestions(d.id));
  }, [documents, loadQuestions]);

  const filteredDocs = searchQuery
    ? documents.filter((d) =>
        d.filename.toLowerCase().includes(searchQuery.toLowerCase())
      )
    : documents;

  return (
    <div className="flex flex-col h-full gap-4">
      <div>
        <div className="flex items-center justify-between mb-3">
          <h2 className="text-lg font-semibold">Documents</h2>
          <span className="text-xs text-muted-foreground">
            {docCount} / {docLimit}
          </span>
        </div>
        <UploadDropzone onUploadComplete={handleUploadComplete} />
      </div>

      {documents.length > 0 && (
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input
            placeholder="Search documents..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="pl-9"
            aria-label="Search documents"
          />
        </div>
      )}

      <ScrollArea className="flex-1">
        <div className="space-y-3 pr-2">
          {isLoading ? (
            Array.from({ length: 3 }).map((_, i) => (
              <Skeleton key={i} className="h-20 rounded-xl" />
            ))
          ) : filteredDocs.length === 0 ? (
            <p className="text-sm text-muted-foreground text-center py-8">
              {searchQuery ? "No documents match your search" : "No documents uploaded yet"}
            </p>
          ) : (
            filteredDocs.map((doc) => (
              <DocumentCard
                key={doc.id}
                document={doc}
                questions={questionsMap[doc.id] || []}
                onDelete={handleDelete}
                onQuestionClick={onQuestionClick || (() => {})}
              />
            ))
          )}
        </div>
      </ScrollArea>
    </div>
  );
}
