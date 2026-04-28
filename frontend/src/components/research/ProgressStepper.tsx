import { CheckCircle2, Circle, Loader2 } from "lucide-react";
import type { JobStatus } from "@/api/research.api";

const STEPS = [
  { key: "queued", label: "Queued" },
  { key: "planning", label: "Planning" },
  { key: "researching", label: "Researching" },
  { key: "reflecting", label: "Reflecting" },
  { key: "synthesizing", label: "Synthesizing" },
  { key: "writing", label: "Writing Report" },
  { key: "complete", label: "Complete" },
];

interface ProgressStepperProps {
  job: JobStatus;
}

export default function ProgressStepper({ job }: ProgressStepperProps) {
  const currentIndex = STEPS.findIndex((s) => s.key === job.status);
  const isFailed = job.status === "failed";
  const isCancelled = job.status === "cancelled";

  return (
    <div className="space-y-1">
      {STEPS.map((step, i) => {
        const isDone = i < currentIndex;
        const isCurrent = i === currentIndex && !isFailed && !isCancelled;

        return (
          <div key={step.key} className="flex items-center gap-3 py-1.5">
            {isDone ? (
              <CheckCircle2 className="h-5 w-5 text-green-500 shrink-0" />
            ) : isCurrent ? (
              <Loader2 className="h-5 w-5 text-primary animate-spin shrink-0" />
            ) : (
              <Circle className="h-5 w-5 text-neutral-300 shrink-0" />
            )}

            <div className="flex-1 min-w-0">
              <p
                className={`text-sm ${
                  isDone
                    ? "text-muted-foreground"
                    : isCurrent
                    ? "text-foreground font-medium"
                    : "text-neutral-300"
                }`}
              >
                {step.label}
              </p>
              {isCurrent && step.key === "researching" && job.progress?.current_step && (
                <p className="text-xs text-primary mt-0.5">{job.progress.current_step}</p>
              )}
            </div>
          </div>
        );
      })}

      {isFailed && (
        <div className="mt-2 p-3 rounded-lg bg-red-50 border border-red-200">
          <p className="text-sm text-red-700 font-medium">Job Failed</p>
          <p className="text-xs text-red-600 mt-1">{job.error_message || "Unknown error"}</p>
        </div>
      )}

      {isCancelled && (
        <div className="mt-2 p-3 rounded-lg bg-amber-50 border border-amber-200">
          <p className="text-sm text-amber-700">Job was cancelled</p>
        </div>
      )}
    </div>
  );
}
