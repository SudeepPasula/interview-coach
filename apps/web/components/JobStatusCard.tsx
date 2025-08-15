"use client";

import React from "react";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { JobStatus } from "@/lib/types";

interface JobStatusCardProps {
  jobId?: string;
  onFinished?: () => void;
}

export default function JobStatusCard({ jobId, onFinished }: JobStatusCardProps) {
  const { data: jobStatus, error } = useQuery({
    queryKey: ["job", jobId],
    queryFn: async (): Promise<JobStatus | null> => {
      if (!jobId) return null;
      const { data } = await api.get<JobStatus>(`/jobs/${jobId}`);
      return data;
    },
    refetchInterval: jobId ? 1200 : false,
    enabled: !!jobId,
  });

  // Call onFinished when job completes (only once per job)
  const hasCalledOnFinished = React.useRef(false);
  React.useEffect(() => {
    // Reset when jobId changes
    hasCalledOnFinished.current = false;
  }, [jobId]);

  React.useEffect(() => {
    if (jobStatus?.status === "finished" && onFinished && !hasCalledOnFinished.current) {
      hasCalledOnFinished.current = true;
      onFinished();
    }
  }, [jobStatus?.status, onFinished]);

  if (!jobId) return null;

  const getStatusColor = (status: string) => {
    switch (status) {
      case "queued":
        return "bg-yellow-100 text-yellow-800";
      case "started":
        return "bg-blue-100 text-blue-800";
      case "finished":
        return "bg-green-100 text-green-800";
      case "failed":
        return "bg-red-100 text-red-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case "queued":
        return "⏳";
      case "started":
        return "🔄";
      case "finished":
        return "✅";
      case "failed":
        return "❌";
      default:
        return "⏸️";
    }
  };

  return (
    <div className="bg-white rounded-2xl shadow-sm border p-6 space-y-4">
      <div className="flex items-center justify-between">
        <h2 className="text-lg font-semibold text-gray-900">Processing Status</h2>
        <code className="text-xs bg-gray-100 px-2 py-1 rounded font-mono">
          {jobId.slice(0, 8)}...
        </code>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-3">
          <p className="text-red-700 text-sm">
            Failed to fetch job status. Please try refreshing the page.
          </p>
        </div>
      )}

      {jobStatus && (
        <div className="space-y-3">
          <div className="flex items-center gap-3">
            <span className="text-lg">{getStatusIcon(jobStatus.status)}</span>
            <span className={`px-3 py-1 rounded-full text-sm font-medium ${getStatusColor(jobStatus.status)}`}>
              {jobStatus.status.charAt(0).toUpperCase() + jobStatus.status.slice(1)}
            </span>
          </div>

          {jobStatus.description && (
            <p className="text-sm text-gray-600">{jobStatus.description}</p>
          )}

          {jobStatus.status === "started" && (
            <div className="flex items-center gap-2 text-sm text-gray-600">
              <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
              Processing your audio...
            </div>
          )}

          {jobStatus.status === "failed" && jobStatus.error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3">
              <p className="text-red-700 text-sm font-medium mb-1">Processing failed:</p>
              <pre className="text-red-600 text-xs whitespace-pre-wrap">{jobStatus.error}</pre>
            </div>
          )}

          {jobStatus.status === "finished" && (
            <div className="bg-green-50 border border-green-200 rounded-lg p-3">
              <p className="text-green-700 text-sm font-medium">
                ✅ Analysis complete! Your report is ready below.
              </p>
            </div>
          )}
        </div>
      )}

      {!jobStatus && !error && (
        <div className="flex items-center gap-2 text-sm text-gray-600">
          <div className="w-2 h-2 bg-gray-400 rounded-full animate-pulse"></div>
          Checking job status...
        </div>
      )}
    </div>
  );
}
