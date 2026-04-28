import { useCallback, useEffect, useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "@/auth/AuthContext";
import { researchApi, type JobStatus } from "@/api/research.api";
import ResearchInput from "./ResearchInput";
import ProgressStepper from "./ProgressStepper";
import ReportDownloadCard from "./ReportDownloadCard";
import JobHistoryPanel from "./JobHistoryPanel";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { ArrowLeft } from "lucide-react";

const POLL_INTERVAL = Number(import.meta.env.VITE_RESEARCH_POLL_INTERVAL_MS) || 3000;

export default function ResearchPage() {
  const { user } = useAuth();
  const navigate = useNavigate();
  const [activeJobId, setActiveJobId] = useState<string | null>(null);
  const [activeJob, setActiveJob] = useState<JobStatus | null>(null);
  const [refreshHistory, setRefreshHistory] = useState(0);
  const pollRef = useRef<ReturnType<typeof setInterval>>();

  const isJobActive = activeJob
    ? ["queued", "planning", "researching", "reflecting", "synthesizing", "writing"].includes(activeJob.status)
    : false;

  const pollStatus = useCallback(async (jobId: string) => {
    try {
      const { data } = await researchApi.getStatus(jobId);
      setActiveJob(data);
      if (data.status === "complete" || data.status === "failed" || data.status === "cancelled") {
        if (pollRef.current) clearInterval(pollRef.current);
        setRefreshHistory((p) => p + 1);
      }
    } catch {
      if (pollRef.current) clearInterval(pollRef.current);
    }
  }, []);

  const handleJobStarted = useCallback((jobId: string) => {
    setActiveJobId(jobId);
    setActiveJob({ job_id: jobId, topic: "", status: "queued", progress: null, confidence: null, confidence_score: null, report_path: null, error_message: null, created_at: null, updated_at: null });

    // Start polling
    if (pollRef.current) clearInterval(pollRef.current);
    pollRef.current = setInterval(() => pollStatus(jobId), POLL_INTERVAL);
    pollStatus(jobId);
  }, [pollStatus]);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollRef.current) clearInterval(pollRef.current);
    };
  }, []);

  return (
    <div className="min-h-screen bg-neutral-50">
      <div className="max-w-3xl mx-auto py-8 px-4 space-y-6">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate("/dashboard")} aria-label="Back to dashboard">
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <div>
            <h1 className="text-2xl font-semibold">Deep Research</h1>
            <p className="text-sm text-muted-foreground">Submit a topic for comprehensive AI-powered research</p>
          </div>
        </div>

        <Card className="border-neutral-200 shadow-sm rounded-xl">
          <CardContent className="p-6">
            <ResearchInput isJobActive={isJobActive} onJobStarted={handleJobStarted} />
          </CardContent>
        </Card>

        {activeJob && (
          <Card className="border-neutral-200 shadow-sm rounded-xl">
            <CardHeader className="pb-2">
              <p className="text-sm font-medium truncate">{activeJob.topic}</p>
            </CardHeader>
            <CardContent className="space-y-4">
              <ProgressStepper job={activeJob} />
              <ReportDownloadCard job={activeJob} />
            </CardContent>
          </Card>
        )}

        <Separator />

        <div>
          <h2 className="text-lg font-semibold mb-3">Past Research</h2>
          <JobHistoryPanel refreshTrigger={refreshHistory} />
        </div>
      </div>
    </div>
  );
}
