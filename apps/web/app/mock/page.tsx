"use client";
import { useRef, useState } from "react";
import { api } from "@/lib/api";

type Analysis = {
  overall: number;
  wpm: number;
  filler: { total: number; counts: Record<string, number> };
  coverage: { score: number; matched: string[] };
  tips: string[];
};

type Report = {
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

export default function Mock() {
  const [question, setQuestion] = useState<{ id: number; text: string } | null>(null);
  const [sessionId, setSessionId] = useState<number | null>(null);
  const [rec, setRec] = useState<MediaRecorder | null>(null);
  const chunks = useRef<Blob[]>([]);
  const [transcript, setTranscript] = useState("");
  const [analysis, setAnalysis] = useState<Analysis | null>(null);
  const [report, setReport] = useState<Report | null>(null);
  const [busy, setBusy] = useState(false);
  const [err, setErr] = useState<string | null>(null);

  const apiBase = process.env.NEXT_PUBLIC_API_BASE;

  async function loadQuestion() {
    setErr(null);
    const { data } = await api.get("/questions/SWE");
    const list = Array.isArray(data) ? data : [];
    const q = list[Math.floor(Math.random() * list.length)];
    setQuestion({ id: q.id, text: q.text });
  }

  async function start() {
    setReport(null);
    setTranscript("");
    setAnalysis(null);
    setErr(null);
  
    if (!question) await loadQuestion();
  
    // 1) start a session
    const { data: s } = await api.post("/sessions", {
      role: "SWE",
      question_id: question?.id ?? 1,
    });
    const sid = s.session_id;          // <- use a local const
    setSessionId(sid);                  // update state for UI
  
    // 2) start recording...
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRec = new MediaRecorder(stream);
    const t0 = Date.now();
    chunks.current = [];
  
    mediaRec.ondataavailable = (e) => chunks.current.push(e.data);
  
    mediaRec.onstop = async () => {
      setBusy(true);
      try {
        const secs = Math.max(5, (Date.now() - t0) / 1000);
  
        // 3) transcribe
        const blob = new Blob(chunks.current, { type: "audio/webm" });
        const file = new File([blob], "answer.webm", { type: "audio/webm" });
        const form = new FormData();
        form.append("file", file);
        const tr = await api.post("/transcribe/", form, {
          headers: { "Content-Type": "multipart/form-data" },
        });
        const text = tr.data.transcript || "";
        setTranscript(text);
  
        // 4) analyze
        const an = await api.post("/analyze_text", {
          transcript: text,
          role: "SWE",
          question_id: question?.id ?? 1,
          duration_s: secs,
        });
        setAnalysis(an.data);
  
        // 5) save session (use sid, not sessionId from state)
        await api.post("/sessions/save", {
          session_id: sid,
          transcript: text,
          duration_s: secs,
          metrics: an.data,
        });
  
        // 6) fetch JSON report (again, use sid)
        const rep = await api.get(`/report/${sid}`);
        setReport(rep.data);
      } finally {
        setBusy(false);
      }
    };
  
    mediaRec.start();
    setRec(mediaRec);
  }

  function stop() {
    rec?.stop();
    setRec(null);
  }

  function downloadPdf() {
    if (!sessionId || !apiBase) return;
    const url = `${apiBase}/report/${sessionId}/pdf`;
    // Open in a new tab (will download due to Content-Disposition: attachment)
    window.open(url, "_blank");
  }

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-5">
      <h1 className="text-2xl font-semibold">Mock Interview</h1>

      {!apiBase && (
        <p className="text-sm text-red-600">
          Missing NEXT_PUBLIC_API_BASE in .env.local
        </p>
      )}

      <div className="space-y-2">
        <button className="px-3 py-2 border rounded" onClick={loadQuestion} disabled={busy || !!rec}>
          Load Question
        </button>
        {question && <p className="text-gray-900"><b>Question:</b> {question.text}</p>}
      </div>

      <div className="flex gap-2">
        <button
          className="px-4 py-2 rounded bg-black text-white disabled:opacity-50"
          onClick={start}
          disabled={!!rec || busy}
        >
          Start
        </button>
        <button
          className="px-4 py-2 rounded border disabled:opacity-50"
          onClick={stop}
          disabled={!rec || busy}
        >
          Stop
        </button>
        {sessionId && (
          <button
            className="px-4 py-2 rounded border disabled:opacity-50"
            onClick={downloadPdf}
            disabled={busy}
          >
            Download PDF
          </button>
        )}
      </div>

      {busy && <p className="text-sm opacity-70">Processing…</p>}
      {err && <p className="text-sm text-red-600">{err}</p>}

      {transcript && (
        <div className="p-4 rounded border bg-white">
          <h2 className="font-medium mb-2">Transcript</h2>
          <p className="whitespace-pre-wrap text-gray-900">{transcript}</p>
        </div>
      )}

      {analysis && (
        <div className="p-4 rounded border bg-white space-y-2">
          <h2 className="font-medium">Report Card</h2>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div><b>Overall</b>: {analysis.overall}</div>
            <div><b>WPM</b>: {analysis.wpm}</div>
            <div><b>Coverage</b>: {analysis.coverage.score}</div>
            <div><b>Filler words</b>: {analysis.filler.total}</div>
          </div>
          <div><b>Matched:</b> {analysis.coverage.matched.join(", ") || "—"}</div>
          {analysis.tips.length > 0 && (
            <ul className="list-disc list-inside">
              {analysis.tips.map((t, i) => <li key={i}>{t}</li>)}
            </ul>
          )}
        </div>
      )}

      {report && (
        <div className="p-4 rounded border bg-white space-y-1">
          <h2 className="font-medium">Saved Report (from API)</h2>
          <div className="grid grid-cols-2 gap-2 text-sm">
            <div><b>Overall</b>: {report.overall}</div>
            <div><b>WPM</b>: {report.wpm}</div>
            <div><b>Coverage</b>: {report.coverage_score}</div>
            <div><b>Filler</b>: {report.filler_total}</div>
          </div>
          <div><b>Matched:</b> {report.matched.join(", ") || "—"}</div>
          {report.tips?.length ? (
            <ul className="list-disc list-inside">
              {report.tips.map((t, i) => <li key={i}>{t}</li>)}
            </ul>
          ) : null}
        </div>
      )}
    </div>
  );
}