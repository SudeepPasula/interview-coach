"use client";
import { useRef, useState } from "react";
import axios from "axios";

type Analysis = {
  overall: number;
  wpm: number;
  filler: { total: number; counts: Record<string, number> };
  coverage: { score: number; matched: string[] };
  tips: string[];
};

export default function Mock() {
  const [rec, setRec] = useState<MediaRecorder|null>(null);
  const chunks = useRef<Blob[]>([]);
  const [transcript, setTranscript] = useState("");
  const [analysis, setAnalysis] = useState<Analysis|null>(null);
  const [busy, setBusy] = useState(false);
  const [duration, setDuration] = useState(0);

  async function start() {
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    const mediaRec = new MediaRecorder(stream);
    const t0 = Date.now();
    mediaRec.ondataavailable = e => chunks.current.push(e.data);
    mediaRec.onstop = async () => {
      setBusy(true);
      const t1 = Date.now();
      const secs = Math.max(5, (t1 - t0)/1000);
      setDuration(secs);

      // Build audio file
      const blob = new Blob(chunks.current, { type: "audio/webm" });
      chunks.current = [];
      const file = new File([blob], "answer.webm", { type: "audio/webm" });

      // 1) transcribe
      const form = new FormData();
      form.append("file", file);
      const tr = await axios.post("http://127.0.0.1:8000/transcribe/", form, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      const text = tr.data.transcript || "";
      setTranscript(text);

      // 2) analyze
      const an = await axios.post("http://127.0.0.1:8000/analyze_text", {
        transcript: text,
        role: "SWE",
        question_id: 1,
        duration_s: secs,
      });
      setAnalysis(an.data);
      setBusy(false);
    };
    mediaRec.start();
    setRec(mediaRec);
  }

  function stop() { rec?.stop(); setRec(null); }

  return (
    <div className="p-6 max-w-3xl mx-auto space-y-5">
      <h1 className="text-2xl font-semibold">Mock Interview</h1>
      <div className="flex gap-2">
        <button className="px-4 py-2 rounded bg-black text-white disabled:opacity-50" onClick={start} disabled={!!rec || busy}>Start</button>
        <button className="px-4 py-2 rounded border" onClick={stop} disabled={!rec || busy}>Stop</button>
      </div>
      {busy && <p className="text-sm opacity-70">Processing…</p>}

      {transcript && (
        <div className="p-4 rounded border bg-white">
          <h2 className="font-medium mb-2">Transcript</h2>
          <p className="whitespace-pre-wrap">{transcript}</p>
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
          <div>
            <b>Matched key points:</b> {analysis.coverage.matched.join(", ") || "—"}
          </div>
          {analysis.tips.length > 0 && (
            <ul className="list-disc list-inside">
              {analysis.tips.map((t, i) => <li key={i}>{t}</li>)}
            </ul>
          )}
        </div>
      )}
    </div>
  );
}