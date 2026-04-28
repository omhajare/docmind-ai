interface ConfidenceBarProps {
  confidence: "high" | "medium" | "low" | null;
}

export default function ConfidenceBar({ confidence }: ConfidenceBarProps) {
  if (!confidence) return null;

  const config = {
    high: { dots: 5, color: "bg-green-500", label: "High confidence" },
    medium: { dots: 3, color: "bg-amber-500", label: "Medium confidence" },
    low: { dots: 2, color: "bg-red-500", label: "Low confidence" },
  };

  const { dots, color, label } = config[confidence];

  return (
    <div className="flex items-center gap-1" title={label} aria-label={label}>
      {Array.from({ length: 5 }).map((_, i) => (
        <span
          key={i}
          className={`inline-block h-1.5 w-1.5 rounded-full ${
            i < dots ? color : "bg-neutral-200"
          }`}
        />
      ))}
      <span className="text-[10px] text-muted-foreground ml-1">{label}</span>
    </div>
  );
}
