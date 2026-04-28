import { z } from "zod";

export const researchSchema = z.object({
  topic: z
    .string()
    .min(1, "Topic is required")
    .max(300, "Topic must be 300 characters or less")
    .trim(),
});

export type ResearchFormData = z.infer<typeof researchSchema>;
