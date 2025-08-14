# apps/api/app/scoring.py
from __future__ import annotations

import re
import math
from typing import List, Dict

import numpy as np
from sentence_transformers import SentenceTransformer, util

# ---- One-time model load per process (API / worker will each keep their own) ----
EMB = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

# ---- Heuristics ----
FILLERS = {
    "um", "uh", "like", "you know", "sort of", "kind of",
    "basically", "actually", "literally"
}

# Optional: prioritize which key points matter most when crafting tips
IMPORTANCE = {
    "impact": 3,
    "root cause analysis": 3,
    "debugging steps": 2,
    "lesson learned": 2,
    "tools used": 1,
}


# -------------------- Metrics --------------------
def words_per_minute(text: str, duration_s: float) -> float:
    """Compute words per minute from transcript length and audio duration."""
    w = len(text.split())
    return 0.0 if duration_s <= 0 else (w / (duration_s / 60.0))


def filler_stats(text: str) -> Dict:
    """Count common filler words/phrases (case-insensitive, phrase-aware)."""
    lower = text.lower()
    counts = {}
    for f in FILLERS:
        # word-boundary around the whole phrase (handles multi-word fillers)
        pattern = rf"\b{re.escape(f)}\b"
        counts[f] = len(re.findall(pattern, lower))
    return {"counts": counts, "total": int(sum(counts.values()))}


def coverage_score(transcript: str, key_points: List[str]) -> Dict:
    """
    Score how well the transcript covers the provided key_points by combining:
      - Substring hits (exact-ish phrase presence, case-insensitive)
      - Embedding similarity (Sentence-BERT) with a lenient threshold
      - Robust aggregate: 60% hit-rate + 40% top-K similarity mean

    Returns:
      {
        "matched": [list of key_points recognized],
        "score": float in [0,1]
      }
    """
    if not key_points or not transcript.strip():
        return {"matched": [], "score": 0.0}

    # Normalize text/phrases
    t_norm = transcript.lower()
    kp_norm = [kp.lower() for kp in key_points]

    # 1) Substring (exact-ish) matches first
    substring_matched = set()
    for kp in kp_norm:
        # Simple contiguous substring check (robust to basic punctuation/spacing)
        if kp in t_norm:
            substring_matched.add(kp)

    # 2) Embedding similarity as fallback/confirmation
    emb_t = EMB.encode([transcript], convert_to_tensor=True)
    emb_k = EMB.encode(key_points, convert_to_tensor=True)
    sims = util.cos_sim(emb_t, emb_k).cpu().numpy()[0]  # shape: (len(key_points),)

    # Slightly relaxed threshold to avoid being overly stingy
    THRESH = 0.30

    # Build list of (original_kp, sim, matched_bool) with small boost for substring hits
    scored = []
    for kp_raw, kp_lower, s in zip(key_points, kp_norm, sims):
        s = float(s)
        substring_hit = kp_lower in substring_matched
        matched = substring_hit or (s >= THRESH)
        if substring_hit:
            # Floor-boost similarity when the exact phrase appears in transcript
            s = max(s, 0.80)
        scored.append((kp_raw, s, matched))

    matched = [kp for kp, s, m in scored if m]

    # Robust aggregate:
    n = len(key_points)
    hit_rate = len(matched) / n

    # Top-K mean similarity (K ≈ 60% of N; at least 1)
    K = max(1, math.ceil(0.6 * n))
    topk_mean = float(np.mean(sorted([s for _, s, _ in scored], reverse=True)[:K]))

    score = round(0.6 * hit_rate + 0.4 * np.clip(topk_mean, 0, 1), 3)
    return {"matched": matched, "score": score}


def tips_from_metrics(coverage: Dict, fillers: Dict, wpm: float, key_points: List[str]) -> List[str]:
    """Produce a concise, actionable list of coaching tips."""
    tips: List[str] = []

    matched = set(coverage.get("matched", []))
    # sort missing by priority if known
    missing = [k for k in key_points if k not in matched]
    missing_sorted = sorted(
        missing, key=lambda k: -IMPORTANCE.get(k.lower(), 1)
    )

    if coverage.get("score", 0.0) < 0.6 and missing_sorted:
        tips.append("Add missing points: " + ", ".join(missing_sorted[:3]))
    if fillers.get("total", 0) > 4:
        tips.append("Reduce filler words—pause instead of saying filler.")
    if wpm < 110:
        tips.append("Increase pace slightly for energy (target 130–160 WPM).")
    if wpm > 170:
        tips.append("Slow down a bit for clarity (target 130–160 WPM).")

    return tips


def overall_score(coverage: Dict, fillers: Dict, wpm: float) -> float:
    """
    Weighted final score with emphasis on content coverage.
    - coverage: 60%
    - filler discipline: 20%
    - pace clarity: 20%
    """
    cov = coverage.get("score", 0.0)                 # 0..1, higher is better
    fil = 1 - min(fillers.get("total", 0) / 10, 1)   # 1 best; 0 worst past 10 fillers
    pace_pen = min(abs(150 - wpm) / 150, 1)          # 0 best near 150 WPM
    pace = 1 - pace_pen
    return round(0.6 * cov + 0.2 * fil + 0.2 * pace, 3)


# -------------------- Public API --------------------
def analyze(transcript: str, role: str, key_points: List[str], duration_s: float) -> Dict:
    """
    Main entry point used by tasks.py / API:
      - Computes WPM, filler stats, coverage, tips, and overall score.
    """
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