import { useEffect, useState } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "sonner";
import { ArrowLeft, ExternalLink, Power } from "lucide-react";

import apiClient from "@/api/client";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

const EVAL_DASHBOARD_URL = import.meta.env.VITE_EVAL_DASHBOARD_URL || "";

export default function AdminPage() {
  const navigate = useNavigate();
  const [aiEnabled, setAiEnabled] = useState<boolean | null>(null);
  const [password, setPassword] = useState("");
  const [isToggling, setIsToggling] = useState(false);

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

  return (
    <div className="min-h-screen bg-neutral-50">
      <div className="max-w-lg mx-auto py-8 px-4 space-y-6">
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
                  Open Evaluation Dashboard
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
