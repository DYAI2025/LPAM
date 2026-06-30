#!/usr/bin/env bash
# pre_llm_call: GUARANTEED shallow recall. Queries gbrain (breadth, not depth),
# injects a compact [gbrain] digest into the user message. Fail-open (always {context} or {}).
#
# Config via env (read from $HERMES_HOME/.env):
#   GBRAIN_MCP_URL        gbrain MCP endpoint (default http://127.0.0.1:3131/mcp)
#   MCP_GBRAIN_API_KEY    bearer token for the gbrain MCP
#   HERMES_HOME           hermes home dir (default ~/.hermes)
set -uo pipefail
HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
LOG="$HERMES_HOME/logs/gbrain_hook.log"
SCORE_FLOOR=0.15     # relevance gate: skip weak hits so irrelevant turns inject nothing
TOPN=4               # breadth: how many candidate pages to surface
set -a; . "$HERMES_HOME/.env" 2>/dev/null || true; set +a
MCP="${GBRAIN_MCP_URL:-http://127.0.0.1:3131/mcp}"
KEY="${MCP_GBRAIN_API_KEY:-}"

payload="$(cat)"
q="$(printf '%s' "$payload" | jq -r '.extra.user_message // .user_message // empty' 2>/dev/null)"
[ -z "$q" ] && { echo '{}'; exit 0; }

req="$(jq -nc --arg q "$q" '{jsonrpc:"2.0",id:1,method:"tools/call",params:{name:"query",arguments:{query:$q,expand:false,autocut:false,limit:5}}}')"
resp="$(curl -sS -m 7 -X POST "$MCP" -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -d "$req" 2>>"$LOG" | grep '^data: ' | sed 's/^data: //')" || { echo "$(date -Is) peek curl-fail" >>"$LOG"; echo '{}'; exit 0; }

# results live as a JSON array string in result.content[0].text
digest="$(printf '%s' "$resp" | jq -r --argjson floor "$SCORE_FLOOR" --argjson n "$TOPN" '
  (.result.content[0].text | fromjson? // []) as $r
  | [ $r[] | select((.score//0) >= $floor) ] [:$n]
  | map("• " + (.slug//"?") + ": " + ((.title//.chunk_text//"")|tostring|.[0:90]))
  | join("\n")' 2>/dev/null)"

[ -z "$digest" ] && { echo "$(date -Is) peek no-hit q=[${q:0:40}]" >>"$LOG"; echo '{}'; exit 0; }
echo "$(date -Is) peek hit q=[${q:0:40}]" >>"$LOG"
jq -nc --arg c "[gbrain] Possibly relevant knowledge in long-term memory (dive with 'query'/'recall' if needed):
$digest" '{context:$c}'
