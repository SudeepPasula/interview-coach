# apps/api/app/scoring.py
from __future__ import annotations

import re
from typing import List, Dict

import numpy as np
from sentence_transformers import SentenceTransformer, util

# Load once per process (API & worker will each keep one in memory)
EMB = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

FILLERS = {
    "um", "uh", "like", "you know", "sort of", "kind of",
    "basically", "actually", "literally"
}

def words_per_minute(text: str, duration_s: float) -> float:
    w = len(text.split())
    return 0.0 if duration_s <= 0 else (w / (duration_s / 60.0))

def filler_stats(text: str) -> Dict:
    lower = text.lower()
    counts = {}
    for f in FILLERS:
        # word-boundary around the whole phrase (handles multi-word fillers)
        pattern = rf"\b{re.escape(f)}\b"
        counts[f] = len(re.findall(pattern, lower))
    return {"counts": counts, "total": int(sum(counts.values()))}

def coverage_score(transcript: str, key_points: List[str]) -> Dict:
    if not key_points or not transcript.strip():
        return {"matched": [], "score": 0.0}
    emb_t = EMB.encode([transcript], convert_to_tensor=True)
    emb_k = EMB.encode(key_points, convert_to_tensor=True)
    sims = util.cos_sim(emb_t, emb_k).cpu().numpy()[0]
    matched = [kp for kp, s in sorted(zip(key_points, sims), key=lambda x: -x[1]) if s > 0.35]
    score = float(np.clip(np.mean(sims), 0, 1))
    return {"matched": matched, "score": round(score, 3)}

def tips_from_metrics(coverage: Dict, fillers: Dict, wpm: float, key_points: List[str]) -> List[str]:
    tips: List[str] = []
    missing = [k for k in key_points if k not in coverage.get("matched", [])]
    if coverage.get("score", 0.0) < 0.6 and missing:
        tips.append("Add missing points: " + ", ".join(missing[:3]))
    if fillers.get("total", 0) > 4:
        tips.append("Reduce filler words—pause instead of saying filler.")
    if wpm < 110:
        tips.append("Increase pace slightly for energy (target 130–160 WPM).")
    if wpm > 170:
        tips.append("Slow down a bit for clarity (target 130–160 WPM).")
    return tips

def overall_score(coverage: Dict, fillers: Dict, wpm: float) -> float:
    cov = coverage.get("score", 0.0)                 # 0..1 higher is better
    fil = 1 - min(fillers.get("total", 0)/10, 1)     # 1 best; 0 worst past 10 fillers
    pace_pen = min(abs(150 - wpm)/150, 1)            # 0 best near 150 WPM
    pace = 1 - pace_pen
    return round(0.6*cov + 0.2*fil + 0.2*pace, 3)

# ---- NEW: public API used by tasks.py ----
def analyze(transcript: str, role: str, key_points: List[str], duration_s: float) -> Dict:
    wpm = words_per_minute(transcript, duration_s)
    fillers = filler_stats(transcript)
    coverage = coverage_score(transcript, key_points)
    tips = tips_from_metrics(coverage, fillers, wpm, key_points)
    overall = overall_score(coverage, fillers, wpm)
    return {
        "role": role,
        "coverage": coverage,
        "filler": fillers,
        "wpm": int(round(wpm)),
        "tips": tips,
        "overall": overall,
    }