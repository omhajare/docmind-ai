import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Download } from "lucide-react";
import { toast } from "sonner";

import { researchApi, type JobStatus } from "@/api/research.api";

interface ReportDownloadCardProps {
  job: JobStatus;
}

export default function ReportDownloadCard({ job }: ReportDownloadCardProps) {
  if (job.status !== "complete") return null;

  const handleDownload = async () => {
    try {
      const response = await researchApi.download(job.job_id);
      const blob = new Blob([response.data]);
      const url = window.URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `docmind_report_${job.job_id.slice(0, 8)}.docx`;
      a.click();
      window.URL.revokeObjectURL(url);
    } catch {
      toast.error("Failed to download report");
    }
  };

  const confColors = {
    high: "bg-green-100 text-green-700",
    medium: "bg-amber-100 text-amber-700",
    low: "bg-red-100 text-red-700",
  };

  return (
    <div className="flex items-center gap-3 p-3 rounded-xl border border-neutral-200 bg-white">
      {job.confidence && (
        <Badge className={`${confColors[job.confidence]} border-0`}>
          {job.confidence.toUpperCase()}
          {job.confidence_score !== null && ` (${(job.confidence_score * 100).toFixed(0)}%)`}
        </Badge>
      )}
      <Button onClick={handleDownload} size="sm" className="gap-2 ml-auto">
        <Download className="h-4 w-4" />
        Download Report
      </Button>
    </div>
  );
}
