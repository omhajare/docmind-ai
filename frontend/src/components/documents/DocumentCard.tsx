import { useState } from "react";
import { FileText, Trash2 } from "lucide-react";
import { toast } from "sonner";

import { documentsApi, type Document, type SuggestedQuestion } from "@/api/documents.api";
import SuggestedQuestions from "./SuggestedQuestions";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
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

interface DocumentCardProps {
  document: Document;
  questions: SuggestedQuestion[];
  onDelete: (id: string) => void;
  onQuestionClick: (question: string) => void;
}

export default function DocumentCard({
  document,
  questions,
  onDelete,
  onQuestionClick,
}: DocumentCardProps) {
  const [isDeleting, setIsDeleting] = useState(false);

  const handleDelete = async () => {
    setIsDeleting(true);
    try {
      await documentsApi.delete(document.id);
      onDelete(document.id);
      toast.success(`Deleted ${document.filename}`);
    } catch {
      toast.error("Failed to delete document");
    } finally {
      setIsDeleting(false);
    }
  };

  const formatSize = (kb: number | null) => {
    if (!kb) return "";
    if (kb >= 1024) return `${(kb / 1024).toFixed(1)} MB`;
    return `${kb} KB`;
  };

  const formatDate = (iso: string | null) => {
    if (!iso) return "";
    return new Date(iso).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  };

  return (
    <Card className="border-neutral-200 shadow-sm rounded-xl">
      <CardContent className="p-4">
        <div className="flex items-start justify-between gap-2">
          <div className="flex items-start gap-3 min-w-0">
            <FileText className="h-5 w-5 text-primary mt-0.5 shrink-0" />
            <div className="min-w-0">
              <p className="text-sm font-medium truncate">{document.filename}</p>
              <p className="text-xs text-muted-foreground mt-0.5">
                {formatSize(document.file_size_kb)}
                {document.chunk_count > 0 && ` · ${document.chunk_count} chunks`}
                {document.uploaded_at && ` · ${formatDate(document.uploaded_at)}`}
              </p>
            </div>
          </div>

          <AlertDialog>
            <AlertDialogTrigger asChild>
              <Button
                variant="ghost"
                size="icon"
                className="h-8 w-8 text-muted-foreground hover:text-destructive shrink-0"
                disabled={isDeleting}
                aria-label={`Delete ${document.filename}`}
              >
                <Trash2 className="h-4 w-4" />
              </Button>
            </AlertDialogTrigger>
            <AlertDialogContent>
              <AlertDialogHeader>
                <AlertDialogTitle>Delete document?</AlertDialogTitle>
                <AlertDialogDescription>
                  This will permanently delete "{document.filename}" and all its indexed data.
                  This action cannot be undone.
                </AlertDialogDescription>
              </AlertDialogHeader>
              <AlertDialogFooter>
                <AlertDialogCancel>Cancel</AlertDialogCancel>
                <AlertDialogAction onClick={handleDelete} className="bg-destructive text-destructive-foreground hover:bg-destructive/90">
                  Delete
                </AlertDialogAction>
              </AlertDialogFooter>
            </AlertDialogContent>
          </AlertDialog>
        </div>

        <SuggestedQuestions questions={questions} onQuestionClick={onQuestionClick} />
      </CardContent>
    </Card>
  );
}
