// apps/web/lib/types.ts
export type Analysis = {
    role: string;
    coverage: { matched: string[]; score: number };
    filler: { counts: Record<string, number>; total: number };
    wpm: number;
    tips: string[];
    overall: number;
  };

  export type ReportJson = {
    session_id: number;
    overall: number;
    wpm: number;
    filler_total: number;
    coverage_score: number;
    matched: string[];
    tips: string[];
    transcript: string;
    created_at: string;
  };

  export type JobStatus = {
    id: string;
    status: "queued" | "started" | "deferred" | "finished" | "failed";
    enqueued_at?: string;
    started_at?: string;
    ended_at?: string;
    description?: string;
    result?: Analysis;
    error?: string;
  };
