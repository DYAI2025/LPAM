#!/usr/bin/env bash
# post_llm_call: salience-gated consolidation. Returns {} instantly, then runs
# gbrain extract_facts DETACHED (so the hook timeout can't kill the LLM extraction).
# extract_facts is the notability gate — it self-persists durable facts, skips trivia.
#
# Config via env (read from $HERMES_HOME/.env):
#   GBRAIN_MCP_URL, MCP_GBRAIN_API_KEY, HERMES_HOME (see gbrain_peek.sh).
set -uo pipefail
echo '{}'                      # instant hook response — never blocks the turn
payload="$(cat)"
(
  HERMES_HOME="${HERMES_HOME:-$HOME/.hermes}"
  LOG="$HERMES_HOME/logs/gbrain_hook.log"
  set -a; . "$HERMES_HOME/.env" 2>/dev/null || true; set +a
  MCP="${GBRAIN_MCP_URL:-http://127.0.0.1:3131/mcp}"
  KEY="${MCP_GBRAIN_API_KEY:-}"
  user="$(printf '%s' "$payload" | jq -r '.extra.user_message // empty' 2>/dev/null)"
  asst="$(printf '%s' "$payload" | jq -r '.extra.assistant_response // empty' 2>/dev/null)"
  sid="$(printf  '%s' "$payload" | jq -r '.session_id // "hermes"' 2>/dev/null)"
  [ -z "$user$asst" ] && exit 0
  turn="USER: $user
ASSISTANT: $asst"
  req="$(jq -nc --arg t "$turn" --arg s "$sid" '{jsonrpc:"2.0",id:1,method:"tools/call",params:{name:"extract_facts",arguments:{turn_text:$t,session_id:$s}}}')"
  res="$(curl -sS -m 25 -X POST "$MCP" -H "Authorization: Bearer $KEY" -H "Content-Type: application/json" -H "Accept: application/json, text/event-stream" -d "$req" 2>>"$LOG" | grep '^data: ' | sed 's/^data: //')"
  ins="$(printf '%s' "$res" | jq -r '.result.content[0].text | fromjson? | .inserted // 0' 2>/dev/null)"
  echo "$(date -Is) promote inserted=${ins:-?} sid=$sid u=[${user:0:50}]" >>"$LOG"
) </dev/null >/dev/null 2>&1 &
disown 2>/dev/null || true
exit 0
