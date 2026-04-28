import { Badge } from "@/components/ui/badge";
import type { SuggestedQuestion } from "@/api/documents.api";

interface SuggestedQuestionsProps {
  questions: SuggestedQuestion[];
  onQuestionClick: (question: string) => void;
}

export default function SuggestedQuestions({
  questions,
  onQuestionClick,
}: SuggestedQuestionsProps) {
  if (questions.length === 0) return null;

  return (
    <div className="flex flex-wrap gap-1.5 mt-2">
      {questions.map((q) => (
        <Badge
          key={q.id}
          variant="secondary"
          className="cursor-pointer hover:bg-primary/10 hover:text-primary text-xs font-normal"
          onClick={(e) => {
            e.stopPropagation();
            onQuestionClick(q.question);
          }}
        >
          {q.question.length > 60 ? q.question.slice(0, 57) + "..." : q.question}
        </Badge>
      ))}
    </div>
  );
}
