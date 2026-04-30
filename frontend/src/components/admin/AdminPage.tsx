import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { ArrowLeft, ExternalLink, Power, BarChart3, Trash2 } from "lucide-react";

import apiClient from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";

const EVAL_DASHBOARD_URL = import.meta.env.VITE_EVAL_DASHBOARD_URL || "";

interface EvalRun {
  run_id: string;
  eval_mode: string;
  question_count: number;
  avg_faithfulness: number;
  avg_answer_relevancy: number;
  avg_context_precision: number;
  passed_count: number;
  evaluated_at: string | null;
}

function ScoreBadge({ score, threshold = 0.7 }: { score: number; threshold?: number }) {
  const pass = score >= threshold;
  return (
    <Badge variant={pass ? "default" : "destructive"} className="font-mono text-xs">
      {score.toFixed(4)}
    </Badge>
  );
}

export default function AdminPage() {
  const navigate = useNavigate();
  const [aiEnabled, setAiEnabled] = useState<boolean | null>(null);
  const [password, setPassword] = useState("");
  const [isToggling, setIsToggling] = useState(false);
  const [evalRuns, setEvalRuns] = useState<EvalRun[]>([]);
  const [loadingRuns, setLoadingRuns] = useState(false);

  useEffect(() => {
    const fetchStatus = async () => {
      try {
        const { data } = await apiClient.get("/api/v1/admin/status");
        setAiEnabled(data.ai_enabled);
      } catch {
        toast.error("Failed to fetch AI status");
      }
    };
    fetchStatus();
  }, []);

  // Fetch eval runs when password is entered
  useEffect(() => {
    if (!password) return;
    const fetchRuns = async () => {
      setLoadingRuns(true);
      try {
        const { data } = await apiClient.get("/api/v1/eval/runs", {
          headers: { "X-Admin-Password": password },
        });
        setEvalRuns(data);
      } catch {
        // Ignore — password might be wrong
      } finally {
        setLoadingRuns(false);
      }
    };
    fetchRuns();
  }, [password]);

  const handleToggle = async () => {
    if (!password) {
      toast.error("Enter the admin password");
      return;
    }
    setIsToggling(true);
    try {
      const { data } = await apiClient.post("/api/v1/admin/toggle", null, {
        headers: { "X-Admin-Password": password },
      });
      setAiEnabled(data.ai_enabled);
      toast.success(data.message);
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Toggle failed");
    } finally {
      setIsToggling(false);
    }
  };

  const handleDeleteRun = async (runId: string) => {
    try {
      await apiClient.delete(`/api/v1/eval/runs/${runId}`, {
        headers: { "X-Admin-Password": password },
      });
      setEvalRuns((prev) => prev.filter((r) => r.run_id !== runId));
      toast.success("Eval run deleted");
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Delete failed");
    }
  };

  return (
    <div className="min-h-screen bg-neutral-50">
      <div className="max-w-2xl mx-auto py-8 px-4 space-y-6">
        <div className="flex items-center gap-3">
          <Button variant="ghost" size="icon" onClick={() => navigate("/dashboard")} aria-label="Back">
            <ArrowLeft className="h-5 w-5" />
          </Button>
          <h1 className="text-2xl font-semibold">Admin Panel</h1>
        </div>

        {/* AI Service Toggle */}
        <Card className="border-neutral-200 shadow-sm rounded-xl">
          <CardHeader className="pb-2">
            <h2 className="text-lg font-semibold">AI Service Control</h2>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm font-medium">AI Service Status</p>
                <p className="text-xs text-muted-foreground">
                  Controls chat, research, and suggested questions
                </p>
              </div>
              <div className={`flex items-center gap-2 px-3 py-1.5 rounded-full text-sm font-medium ${
                aiEnabled ? "bg-green-100 text-green-700" : "bg-red-100 text-red-700"
              }`}>
                <Power className="h-4 w-4" />
                {aiEnabled === null ? "Loading..." : aiEnabled ? "ON" : "OFF"}
              </div>
            </div>

            <div className="space-y-2">
              <Label htmlFor="admin-password">Admin Password</Label>
              <Input
                id="admin-password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter admin password"
                aria-label="Admin password"
              />
            </div>

            <Button
              onClick={handleToggle}
              disabled={isToggling || !password}
              variant={aiEnabled ? "destructive" : "default"}
              className="w-full"
            >
              {isToggling ? "Toggling..." : aiEnabled ? "Disable AI Service" : "Enable AI Service"}
            </Button>
          </CardContent>
        </Card>

        {/* RAGAS Evaluation History */}
        <Card className="border-neutral-200 shadow-sm rounded-xl">
          <CardHeader className="pb-2">
            <div className="flex items-center gap-2">
              <BarChart3 className="h-5 w-5 text-indigo-500" />
              <h2 className="text-lg font-semibold">RAGAS Evaluation History</h2>
            </div>
          </CardHeader>
          <CardContent>
            {loadingRuns ? (
              <p className="text-sm text-muted-foreground">Loading...</p>
            ) : evalRuns.length === 0 ? (
              <p className="text-sm text-muted-foreground">
                No evaluation runs yet. Run evaluations from the Streamlit dashboard.
              </p>
            ) : (
              <div className="space-y-3">
                {evalRuns.map((run) => (
                  <div
                    key={`${run.run_id}-${run.eval_mode}`}
                    className="flex items-center justify-between p-3 rounded-lg border border-neutral-100 bg-white"
                  >
                    <div className="space-y-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm font-mono font-medium">
                          {run.run_id.slice(0, 8)}
                        </span>
                        <Badge variant="outline" className="text-xs">
                          {run.eval_mode === "rag_only" ? "🔵 RAG-Only" : "🟠 Full Pipeline"}
                        </Badge>
                        <span className="text-xs text-muted-foreground">
                          {run.question_count} Q • {run.passed_count} passed
                        </span>
                      </div>
                      <div className="flex gap-3 text-xs">
                        <span>Faith: <ScoreBadge score={run.avg_faithfulness} /></span>
                        <span>Relev: <ScoreBadge score={run.avg_answer_relevancy} /></span>
                        <span>Ctx: <ScoreBadge score={run.avg_context_precision} /></span>
                      </div>
                    </div>
                    <Button
                      variant="ghost"
                      size="icon"
                      onClick={() => handleDeleteRun(run.run_id)}
                      aria-label="Delete run"
                    >
                      <Trash2 className="h-4 w-4 text-red-500" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* RAGAS Dashboard Link */}
        <Card className="border-neutral-200 shadow-sm rounded-xl">
          <CardHeader className="pb-2">
            <h2 className="text-lg font-semibold">RAGAS Evaluation Dashboard</h2>
          </CardHeader>
          <CardContent>
            {EVAL_DASHBOARD_URL ? (
              <a href={EVAL_DASHBOARD_URL} target="_blank" rel="noopener noreferrer">
                <Button variant="outline" className="w-full gap-2">
                  <ExternalLink className="h-4 w-4" />
                  Open Full Evaluation Dashboard
                </Button>
              </a>
            ) : (
              <p className="text-sm text-muted-foreground">
                Evaluation dashboard URL not configured. Set <code>VITE_EVAL_DASHBOARD_URL</code> in your frontend .env file.
              </p>
            )}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
