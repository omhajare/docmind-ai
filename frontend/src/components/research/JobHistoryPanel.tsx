import { useEffect, useState } from "react";
import { toast } from "sonner";

import { researchApi, type JobStatus } from "@/api/research.api";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Download, X } from "lucide-react";
import { Skeleton } from "@/components/ui/skeleton";

interface JobHistoryPanelProps {
  refreshTrigger?: number;
}

export default function JobHistoryPanel({ refreshTrigger }: JobHistoryPanelProps) {
  const [jobs, setJobs] = useState<JobStatus[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const load = async () => {
      try {
        const { data } = await researchApi.getHistory();
        setJobs(data);
      } catch {
        // silent
      } finally {
        setIsLoading(false);
      }
    };
    load();
  }, [refreshTrigger]);

  const handleDownload = async (jobId: string) => {
    try {
      const response = await researchApi.download(jobId);
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `docmind_report_${jobId.slice(0, 8)}.docx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      toast.error("Failed to download report");
    }
  };

  const handleCancel = async (jobId: string) => {
    try {
      await researchApi.cancel(jobId);
      setJobs((prev) =>
        prev.map((j) => (j.job_id === jobId ? { ...j, status: "cancelled" } : j))
      );
      toast.success("Job cancelled");
    } catch {
      toast.error("Failed to cancel job");
    }
  };

  const statusColors: Record<string, string> = {
    complete: "bg-green-100 text-green-700",
    failed: "bg-red-100 text-red-700",
    cancelled: "bg-neutral-100 text-neutral-600",
  };

  const formatDate = (iso: string | null) => {
    if (!iso) return "";
    return new Date(iso).toLocaleDateString("en-US", {
      month: "short", day: "numeric", hour: "2-digit", minute: "2-digit",
    });
  };

  if (isLoading) {
    return (
      <div className="space-y-3">
        {Array.from({ length: 2 }).map((_, i) => (
          <Skeleton key={i} className="h-16 rounded-xl" />
        ))}
      </div>
    );
  }

  if (jobs.length === 0) {
    return <p className="text-sm text-muted-foreground text-center py-4">No past research jobs</p>;
  }

  return (
    <div className="space-y-3">
      {jobs.map((job) => {
        const isActive = ["queued", "planning", "researching", "reflecting", "synthesizing", "writing"].includes(job.status);

        return (
          <div key={job.job_id} className="p-3 rounded-xl border border-neutral-200 bg-white space-y-2">
            <div className="flex items-start justify-between gap-2">
              <div className="min-w-0">
                <p className="text-sm font-medium truncate">{job.topic}</p>
                <p className="text-xs text-muted-foreground">{formatDate(job.created_at)}</p>
              </div>
              <Badge className={`${statusColors[job.status] || "bg-primary/10 text-primary"} border-0 text-xs shrink-0`}>
                {job.status}
              </Badge>
            </div>

            <div className="flex gap-2">
              {job.status === "complete" && (
                <Button size="sm" variant="outline" className="gap-1.5 h-7 text-xs" onClick={() => handleDownload(job.job_id)}>
                  <Download className="h-3 w-3" /> Download
                </Button>
              )}
              {isActive && (
                <Button size="sm" variant="outline" className="gap-1.5 h-7 text-xs text-destructive" onClick={() => handleCancel(job.job_id)}>
                  <X className="h-3 w-3" /> Cancel
                </Button>
              )}
            </div>
          </div>
        );
      })}
    </div>
  );
}
