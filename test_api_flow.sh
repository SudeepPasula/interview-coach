#!/usr/bin/env bash
set -euo pipefail

API="http://localhost:8000"
ROLE="SWE"
QID=1
AUDIO="${1:-$HOME/ideal_answer.wav}"   # usage: ./test_api_flow.sh /path/to/file.wav

if [[ ! -f "$AUDIO" ]]; then
  echo "Audio file not found: $AUDIO" >&2
  exit 1
fi

echo "1) Create session…"
SESSION_ID=$(curl -s -X POST "$API/sessions" \
  -H 'Content-Type: application/json' \
  -d "{\"role\":\"$ROLE\",\"question_id\":$QID}" | jq -r .session_id)
echo "   session_id=$SESSION_ID"

echo "2) Enqueue job…"
JOB_ID=$(curl -s -X POST "$API/jobs/enqueue?session_id=$SESSION_ID" \
  -F "file=@${AUDIO}" | jq -r .job_id)
echo "   job_id=$JOB_ID"

echo "3) Poll job until finished…"
for i in {1..60}; do
  STATUS=$(curl -s "$API/jobs/$JOB_ID" | jq -r .status)
  echo "   [$i] status=$STATUS"
  [[ "$STATUS" == "finished" ]] && break
  sleep 1
done

if [[ "$STATUS" != "finished" ]]; then
  echo "Job did not finish in time. Inspect logs:" >&2
  echo "  docker compose logs -f worker" >&2
  exit 2
fi

echo "4) Fetch JSON report…"
curl -s "$API/report/$SESSION_ID" | jq .

echo "5) Download PDF…"
curl -s -OJ "$API/report/$SESSION_ID/pdf"
PDF_NAME=$(ls -t report-s${SESSION_ID}-*.pdf | head -n1 || true)
[[ -n "${PDF_NAME:-}" ]] && { echo "Saved: $PDF_NAME"; } || echo "PDF saved (name shown above by curl)."

# macOS convenience: open the PDF
if command -v open >/dev/null 2>&1 && [[ -n "${PDF_NAME:-}" ]]; then
  open "$PDF_NAME"
fi
