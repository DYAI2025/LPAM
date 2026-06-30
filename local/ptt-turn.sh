#!/bin/bash
# ============================================================================
# Hermes Push-to-Talk — ONE turn, triggered by a hotkey (see local/hermes-ptt.lua).
# Runs in the user's GUI session, so mic/whisper/say work directly (no broker).
#   1. record mic with VAD (sox)
#   2. transcribe locally (whisper.cpp)
#   3. send text to the REAL Hermes agent brain on the VPS (hermes -z, one-shot)
#   4. speak the reply on the Mac (say)
# Mic is active ONLY for this one recording — the push-to-talk safety win over an
# always-listening loop. Settings come from ~/.hermes-bridge/config (see voice.config.example).
# Env override: HERMES_SSH_ALIAS (ssh alias to the VPS brain).
# ============================================================================
export PATH="/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin:$PATH"
CFG="$HOME/.hermes-bridge/config"; [ -f "$CFG" ] && . "$CFG"
ALIAS="${HERMES_SSH_ALIAS:-hermes-brain}"
LOG="$HOME/.hermes-bridge/ptt.log"
ts(){ date "+%Y-%m-%dT%H:%M:%S%z"; }
log(){ printf '%s\t%s\n' "$(ts)" "$*" >>"$LOG"; }

SND_START="/System/Library/Sounds/Tink.aiff"
SND_DONE="/System/Library/Sounds/Pop.aiff"
wav="${TMPDIR:-/tmp}/hermes_ptt_$$_${RANDOM}.wav"

afplay "$SND_START" >/dev/null 2>&1 &
# VAD record: starts on speech, auto-stops on silence; REC_MAX is the hard ceiling.
rec -q -r 16000 -c 1 "$wav" silence ${REC_SILENCE:-1 0.1 2% 1 1.0 2%} trim 0 "${REC_MAX:-15}" >/dev/null 2>&1
afplay "$SND_DONE" >/dev/null 2>&1 &

if [ -n "${STT_PROMPT:-}" ]; then
  TEXT=$(whisper-cli -m "$STT_MODEL" -f "$wav" -l "${STT_LANG:-en}" --prompt "$STT_PROMPT" -nt 2>/dev/null)
else
  TEXT=$(whisper-cli -m "$STT_MODEL" -f "$wav" -l "${STT_LANG:-en}" -nt 2>/dev/null)
fi
rm -f "$wav"
TEXT=$(printf '%s' "$TEXT" | xargs)
log "heard: $TEXT"

case "$TEXT" in
  ""|"(no speech detected)"|*"REC_FAILED"*)
    say "I didn't catch that."; exit 0 ;;
esac

# Send the transcript to the real Hermes brain on the VPS (hermes -z, one-shot).
# base64 keeps arbitrary transcript text injection-safe; `bash -l` gives hermes its
# full login PATH + runtime deps. hermes prints the clean reply on stdout.
B64=$(printf '%s' "$TEXT" | base64 | tr -d '\n')
RESP=$(ssh "$ALIAS" 'bash -l -s' 2>/dev/null <<REMOTE
t=\$(printf '%s' '$B64' | base64 -d)
hermes -z "\$t"
REMOTE
)
RESP="$(printf '%s' "$RESP" | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//')"
[ -z "$RESP" ] && RESP="I understood you, but couldn't generate a reply."
log "reply: $RESP"

say ${TTS_VOICE:+-v "$TTS_VOICE"} ${TTS_RATE:+-r "$TTS_RATE"} -- "$RESP"
