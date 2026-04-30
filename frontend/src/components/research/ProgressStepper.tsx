import { CheckCircle2, Circle, Loader2 } from "lucide-react";
import type { JobStatus } from "@/api/research.api";
import TypewriterText from "./TypewriterText";

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
  const isComplete = job.status === "complete";

  return (
    <div className="space-y-1">
      {STEPS.map((step, i) => {
        const isDone = i < currentIndex || (isComplete && i === currentIndex);
        const isCurrent = i === currentIndex && !isFailed && !isCancelled && !isComplete;

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
              {isCurrent && job.progress?.current_step && (
                <div className="mt-2 flex items-start gap-2 bg-primary/5 rounded-md p-2.5 border border-primary/10 shadow-sm">
                  <span className="flex h-4 w-4 mt-0.5 shrink-0 items-center justify-center relative">
                    <span className="animate-ping absolute inline-flex h-2.5 w-2.5 rounded-full bg-primary opacity-60"></span>
                    <span className="relative inline-flex rounded-full h-1.5 w-1.5 bg-primary"></span>
                  </span>
                  <p className="text-xs font-mono text-primary/90 leading-relaxed">
                    <TypewriterText text={job.progress.current_step} speed={25} />
                  </p>
                </div>
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
