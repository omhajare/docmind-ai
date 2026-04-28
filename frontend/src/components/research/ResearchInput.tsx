import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { toast } from "sonner";
import { Search } from "lucide-react";

import { researchApi } from "@/api/research.api";
import { researchSchema, type ResearchFormData } from "@/lib/validators/researchSchema";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

interface ResearchInputProps {
  isJobActive: boolean;
  onJobStarted: (jobId: string) => void;
}

export default function ResearchInput({ isJobActive, onJobStarted }: ResearchInputProps) {
  const [isSubmitting, setIsSubmitting] = useState(false);

  const {
    register,
    handleSubmit,
    reset,
    formState: { errors },
  } = useForm<ResearchFormData>({
    resolver: zodResolver(researchSchema),
  });

  const onSubmit = async (data: ResearchFormData) => {
    setIsSubmitting(true);
    try {
      const { data: result } = await researchApi.start(data.topic);
      onJobStarted(result.job_id);
      reset();
      toast.success("Research job started!");
    } catch (err: any) {
      toast.error(err.response?.data?.detail || "Failed to start research");
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <form onSubmit={handleSubmit(onSubmit)} className="space-y-3">
      <div className="space-y-2">
        <Label htmlFor="topic">Research Topic</Label>
        <div className="flex gap-2">
          <Input
            id="topic"
            placeholder="e.g., Impact of AI on healthcare diagnostics"
            {...register("topic")}
            disabled={isJobActive || isSubmitting}
            aria-label="Research topic"
            className="flex-1"
          />
          <Button type="submit" disabled={isJobActive || isSubmitting} className="gap-2">
            <Search className="h-4 w-4" />
            {isSubmitting ? "Starting..." : "Research"}
          </Button>
        </div>
        {errors.topic && (
          <p className="text-sm text-destructive">{errors.topic.message}</p>
        )}
        {isJobActive && (
          <p className="text-xs text-amber-600">A research job is in progress. Please wait for it to complete.</p>
        )}
      </div>
    </form>
  );
}
