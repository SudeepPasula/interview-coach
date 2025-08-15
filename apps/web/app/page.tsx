"use client";

import { useState } from "react";
import { useMutation } from "@tanstack/react-query";
import { api, API_BASE } from "@/lib/api";
import type { ReportJson } from "@/lib/types";
import QuestionCard from "@/components/QuestionCard";
import RecorderCard from "@/components/RecorderCard";
import JobStatusCard from "@/components/JobStatusCard";
import ReportCard from "@/components/ReportCard";
import Toast from "@/components/Toast";

type Question = { id: number; text: string };

export default function Dashboard() {
  const [question, setQuestion] = useState<Question | null>(null);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [jobId, setJobId] = useState<string | null>(null);
  const [report, setReport] = useState<ReportJson | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Start session mutation
  const startSession = useMutation({
    mutationFn: async (questionId: number) => {
      const { data } = await api.post("/sessions", {
        role: "SWE",
        question_id: questionId,
      });
      return data.session_id;
    },
    onSuccess: (sessionId) => {
      setSessionId(sessionId);
      setError(null);
    },
    onError: (err) => {
      console.error("Failed to start session:", err);
      setError("Failed to start session. Please try again.");
    },
  });

  // Enqueue job mutation
  const enqueueJob = useMutation({
    mutationFn: async (file: File) => {
      if (!sessionId) throw new Error("No session ID");

      const form = new FormData();
      form.append("file", file);

      const { data } = await api.post<{ job_id: string }>(
        `/jobs/enqueue?session_id=${sessionId}`,
        form,
        { headers: { "Content-Type": "multipart/form-data" } }
      );
      return data;
    },
    onSuccess: (data) => {
      setJobId(data.job_id);
      setError(null);
    },
    onError: (err) => {
      console.error("Failed to enqueue job:", err);
      setError("Failed to process audio. Please try again.");
    },
  });

  // Fetch report when job finishes
  const fetchReport = useMutation({
    mutationFn: async () => {
      if (!sessionId) throw new Error("No session ID");
      const { data } = await api.get<ReportJson>(`/report/${sessionId}`);
      return data;
    },
    onSuccess: (data) => {
      setReport(data);
      setError(null);
    },
    onError: (err) => {
      console.error("Failed to fetch report:", err);
      setError("Failed to load report. Please try again.");
    },
  });

  const handleQuestionLoad = (loadedQuestion: Question) => {
    setQuestion(loadedQuestion);
    setError(null);
  };

  const handleStartSession = async () => {
    if (!question) {
      setError("Please load a question first.");
      return;
    }
    startSession.mutate(question.id);
  };

  const handleFileReady = async (file: File) => {
    // Start session if not already started
    if (!sessionId) {
      await startSession.mutateAsync(question!.id);
    }

    // Enqueue the job
    enqueueJob.mutate(file);
  };

  const handleJobFinished = () => {
    fetchReport.mutate();
  };

  const handleNewSession = () => {
    setQuestion(null);
    setSessionId(null);
    setJobId(null);
    setReport(null);
    setError(null);
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white border-b border-gray-200">
        <div className="max-w-4xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <h1 className="text-2xl font-bold text-gray-900">Interview Coach</h1>
            <a
              href={`${API_BASE}/docs`}
              target="_blank"
              rel="noopener noreferrer"
              className="text-sm text-blue-600 hover:text-blue-700 underline"
            >
              API Docs
            </a>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-4xl mx-auto px-6 py-8 space-y-6">
        {/* Error Toast */}
        {error && (
          <Toast
            message={error}
            type="error"
            onClose={() => setError(null)}
          />
        )}

        {/* Question Card */}
        <QuestionCard question={question} onLoad={handleQuestionLoad} />

        {/* Recording Section */}
        {question && (
          <div className="space-y-4">
            <RecorderCard
              disabled={!sessionId || enqueueJob.isPending}
              onFile={handleFileReady}
            />

            {!sessionId && (
              <div className="text-center">
                <button
                  onClick={handleStartSession}
                  disabled={startSession.isPending}
                  className="px-6 py-3 bg-green-600 text-white rounded-lg hover:bg-green-700 disabled:opacity-50 disabled:cursor-not-allowed font-medium transition-colors"
                >
                  {startSession.isPending ? "Starting Session..." : "Start Session"}
                </button>
              </div>
            )}
          </div>
        )}

        {/* Job Status */}
        {jobId && (
          <JobStatusCard jobId={jobId} onFinished={handleJobFinished} />
        )}

        {/* Report */}
        {report && (
          <div className="space-y-4">
            <ReportCard report={report} />
            <div className="text-center">
              <button
                onClick={handleNewSession}
                className="px-6 py-3 bg-gray-600 text-white rounded-lg hover:bg-gray-700 font-medium transition-colors"
              >
                Start New Session
              </button>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
