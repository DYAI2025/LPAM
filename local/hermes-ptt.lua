-- Hermes push-to-talk for Hammerspoon. Add to ~/.hammerspoon/init.lua (or load it),
-- then reload Hammerspoon. Binds Option+Space to run ONE push-to-talk turn:
-- ptt-turn.sh records (VAD auto-stop), transcribes locally, asks the VPS Hermes
-- brain, and speaks the reply. One-shot per press — mic is only live for that turn.
--
-- ptt-turn.sh self-limits its recording (REC_MAX / VAD), so a single tap is enough;
-- no hold required. Adjust the hotkey below to taste.

local PTT = os.getenv("HOME") .. "/.hermes-bridge/ptt-turn.sh"
local running = false

local function runPTT()
  if running then return end
  running = true
  hs.alert.show("🎙️ Hermes listening…")
  hs.task.new("/bin/bash", function(code, _, _)
    running = false
    if code ~= 0 then hs.alert.show("⚠️ PTT failed (see ptt.log)") end
  end, { PTT }):start()
end

-- Option+Space → one PTT turn
hs.hotkey.bind({ "alt" }, "space", runPTT)
hs.alert.show("Hermes PTT: Option+Space")
