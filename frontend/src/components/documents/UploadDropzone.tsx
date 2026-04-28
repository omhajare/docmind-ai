import { useCallback, useRef, useState } from "react";
import { Upload } from "lucide-react";
import { toast } from "sonner";

import { documentsApi, type UploadResponse } from "@/api/documents.api";

interface UploadDropzoneProps {
  onUploadComplete: (data: UploadResponse) => void;
}

export default function UploadDropzone({ onUploadComplete }: UploadDropzoneProps) {
  const [isDragging, setIsDragging] = useState(false);
  const [isUploading, setIsUploading] = useState(false);
  const inputRef = useRef<HTMLInputElement>(null);

  const handleFile = useCallback(
    async (file: File) => {
      if (file.type !== "application/pdf") {
        toast.error("Only PDF files are supported");
        return;
      }
      if (file.size > 10 * 1024 * 1024) {
        toast.error("File exceeds maximum size of 10 MB");
        return;
      }

      setIsUploading(true);
      try {
        const { data } = await documentsApi.upload(file);
        onUploadComplete(data);
        toast.success(`Uploaded ${file.name}`);
      } catch (err: any) {
        const detail = err.response?.data?.detail;
        if (typeof detail === "object" && detail?.message) {
          toast.error(detail.message);
        } else {
          toast.error(detail || "Upload failed");
        }
      } finally {
        setIsUploading(false);
      }
    },
    [onUploadComplete]
  );

  const onDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      const file = e.dataTransfer.files[0];
      if (file) handleFile(file);
    },
    [handleFile]
  );

  const onFileSelect = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) handleFile(file);
      e.target.value = "";
    },
    [handleFile]
  );

  return (
    <div
      className={`border-2 border-dashed rounded-xl p-6 text-center cursor-pointer transition-colors ${
        isDragging
          ? "border-primary bg-primary/5"
          : "border-neutral-200 hover:border-primary/50"
      } ${isUploading ? "opacity-50 pointer-events-none" : ""}`}
      onDragOver={(e) => {
        e.preventDefault();
        setIsDragging(true);
      }}
      onDragLeave={() => setIsDragging(false)}
      onDrop={onDrop}
      onClick={() => inputRef.current?.click()}
    >
      <input
        ref={inputRef}
        type="file"
        accept="application/pdf"
        className="hidden"
        onChange={onFileSelect}
      />
      <Upload className="mx-auto h-8 w-8 text-muted-foreground mb-2" />
      {isUploading ? (
        <p className="text-sm text-muted-foreground">Uploading & indexing...</p>
      ) : (
        <>
          <p className="text-sm font-medium">Drop a PDF here or click to browse</p>
          <p className="text-xs text-muted-foreground mt-1">Max 10 MB</p>
        </>
      )}
    </div>
  );
}
