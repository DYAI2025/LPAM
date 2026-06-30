#!/usr/bin/env python3
"""model_health_check — keep Hermes off retired OpenRouter models.

Daily cron. Detects models referenced in config.yaml (model.default + the
fallback_model chain) that have been PULLED from OpenRouter — detection is
/models membership, which is free and cleanly separates *pulled* (absent) from
merely *throttled* (present, returns 429). When a referenced model is gone it is
auto-replaced with the first WORKING free model from a curated priority list
(each candidate is probed with a tiny completion → must return 200), the dead id
is scrubbed from config.yaml AND from state.db session pins (sessions.model /
model_config / system_prompt) so nothing keeps calling it, the Hermes services
are restarted so the new default loads, and a Telegram message is sent.

Requires PyYAML (the Hermes venv python has it). Reads config/keys from
$HERMES_HOME (default ~/.hermes).

Flags: --dry-run (detect + report, no writes / no restart / no notify).
Safe-guards: aborts if /models returns implausibly few models; backs up
config.yaml + state.db before any write; restores config on YAML-parse failure.
"""
import os, re, sys, json, time, shutil, sqlite3, subprocess, urllib.request, urllib.error

HERMES  = os.environ.get("HERMES_HOME") or os.path.expanduser("~/.hermes")
CONFIG  = f"{HERMES}/config.yaml"
DB      = f"{HERMES}/state.db"
ENVFILE = f"{HERMES}/.env"
LOG     = f"{HERMES}/logs/model-health.log"
OR_BASE = "https://openrouter.ai/api/v1"
SERVICES = ["hermes-dashboard", "hermes-control", "hermes-gateway"]

# Curated free replacement priority — reliability first (mid-size models stay
# available; the largest free models throttle hardest). Edit this list to taste.
PRIORITY = [
    "nvidia/nemotron-3-ultra-550b-a55b:free",
    "google/gemma-4-31b-it:free",
    "nvidia/nemotron-3-super-120b-a12b:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "qwen/qwen3-next-80b-a3b-instruct:free",
    "openai/gpt-oss-120b:free",
]

DRY = "--dry-run" in sys.argv


def log(msg):
    line = f"{time.strftime('%Y-%m-%d %H:%M:%S')} {'[dry] ' if DRY else ''}{msg}"
    print(line)
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a") as f:
            f.write(line + "\n")
    except Exception:
        pass


def read_env(key):
    try:
        for ln in open(ENVFILE, encoding="utf-8"):
            ln = ln.strip()
            if ln.startswith(key + "="):
                v = ln.split("=", 1)[1].strip()
                v = re.sub(r"\s+#.*$", "", v)  # strip shell-style trailing inline comment (matches `. .env`)
                return v.strip("'\" ").strip()
    except Exception as e:
        log(f"ERROR reading {key} from .env: {e}")
    return None


def http_json(url, key, method="GET", payload=None, timeout=30):
    data = json.dumps(payload).encode() if payload is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    req.add_header("Authorization", f"Bearer {key}")
    if data:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, json.loads(r.read().decode())


def valid_model_ids(key):
    try:
        status, body = http_json(f"{OR_BASE}/models", key)
        ids = {m["id"] for m in body.get("data", [])}
        return ids
    except Exception as e:
        log(f"ERROR fetching /models: {e}")
        return set()


def probe(model, key):
    """True if model returns a 200 completion right now (not 429/404)."""
    payload = {"model": model, "messages": [{"role": "user", "content": "hi"}], "max_tokens": 2}
    try:
        status, _ = http_json(f"{OR_BASE}/chat/completions", key, "POST", payload, timeout=40)
        return status == 200
    except urllib.error.HTTPError:
        return False
    except Exception as e:
        log(f"  probe {model} error: {e}")
        return False


def referenced_models():
    import yaml
    cfg = yaml.safe_load(open(CONFIG, encoding="utf-8"))
    default = (cfg.get("model") or {}).get("default")
    fb = cfg.get("fallback_model") or []
    if isinstance(fb, dict):
        fb = [fb]
    fb_ids = [e.get("model") for e in fb if isinstance(e, dict) and e.get("model")]
    return default, fb_ids


def pick_replacement(valid, key, exclude):
    for cand in PRIORITY:
        if cand in exclude:
            continue
        if cand in valid and probe(cand, key):
            return cand
    return None


def scrub_statedb(dead, repl):
    bak = f"{DB}.healthbak"
    try:
        if os.path.exists(bak):
            os.remove(bak)
        con = sqlite3.connect(DB, timeout=10)
        # VACUUM INTO cannot bind its target path; `bak` is a server-side constant
        # (derived from the DB const), never user input.
        con.execute(f"VACUUM INTO '{bak}'")  # nosemgrep: python.sqlalchemy.security.sqlalchemy-execute-raw-query
        con.close()
    except Exception:
        try: shutil.copy(DB, bak)
        except Exception: pass
    con = sqlite3.connect(DB, timeout=10)
    con.execute("PRAGMA busy_timeout=10000")
    n = 0
    # `col` iterates a FIXED literal allowlist (never user input); the dead/replacement
    # values are bound as parameters. Only the allowlisted column identifier is interpolated.
    for col in ("model", "model_config", "system_prompt"):
        cur = con.execute(  # nosemgrep: python.sqlalchemy.security.sqlalchemy-execute-raw-query
            f"UPDATE sessions SET {col}=REPLACE({col}, ?, ?) WHERE {col} LIKE ?",
            (dead, repl, f"%{dead}%"))
        n += cur.rowcount
    con.commit(); con.close()
    return n


def notify(token, chat, text):
    if not (token and chat):
        log("notify skipped (no telegram token/chat)")
        return
    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {"chat_id": chat, "text": text, "disable_notification": False}
        data = json.dumps(payload).encode()
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        with urllib.request.urlopen(req, timeout=20) as r:
            ok = r.status == 200
        log(f"telegram notify sent: {ok}")
    except Exception as e:
        log(f"telegram notify error: {e}")


def main():
    key = read_env("OPENROUTER_API_KEY")
    tg_token = read_env("TELEGRAM_BOT_TOKEN")
    tg_chat = read_env("TELEGRAM_HOME_CHANNEL")
    if not key:
        log("FATAL: no OPENROUTER_API_KEY"); sys.exit(1)

    valid = valid_model_ids(key)
    if len(valid) < 50:
        log(f"ABORT: /models returned only {len(valid)} ids — refusing to act on incomplete data")
        sys.exit(1)

    default, fb_ids = referenced_models()
    referenced = [default] + fb_ids
    dead = [m for m in dict.fromkeys(referenced) if m and m not in valid]

    if not dead:
        log(f"OK: all {len([m for m in referenced if m])} referenced models alive "
            f"(default={default}, fallbacks={fb_ids})")
        return

    log(f"PULLED models detected: {dead}")
    cfg_text = open(CONFIG, encoding="utf-8").read()
    changes = []
    for d in dead:
        repl = pick_replacement(valid, key, exclude=set(dead))
        if not repl:
            log(f"CRITICAL: no working free replacement found for {d}")
            if not DRY:
                notify(tg_token, tg_chat,
                       f"⚠️ Hermes: model {d} was pulled from OpenRouter and NO working "
                       f"free replacement was found. Manual action needed.")
            continue
        changes.append((d, repl))
        log(f"plan: replace {d} -> {repl}")

    if DRY:
        log("dry-run: no writes performed")
        return
    if not changes:
        return

    # backup + edit config.yaml via text replace (preserves formatting)
    ts = time.strftime("%Y%m%d-%H%M%S")
    shutil.copy(CONFIG, f"{CONFIG}.health-{ts}.bak")
    for d, repl in changes:
        cfg_text = cfg_text.replace(d, repl)
    open(CONFIG, "w", encoding="utf-8").write(cfg_text)

    # validate YAML still parses and the new default resolves to a live model
    try:
        import yaml
        parsed = yaml.safe_load(cfg_text)  # raises on bad YAML
        nd = (parsed.get("model") or {}).get("default")
        if nd not in valid:
            raise ValueError(f"new default {nd} not in valid set")
    except Exception as e:
        shutil.copy(f"{CONFIG}.health-{ts}.bak", CONFIG)
        log(f"VALIDATION FAILED ({e}) — config.yaml restored from backup")
        notify(tg_token, tg_chat, f"⚠️ Hermes model-health auto-fix FAILED validation, "
                                  f"config restored. Models still dead: {dead}")
        sys.exit(1)

    # scrub state.db session pins for each dead id
    total = 0
    for d, repl in changes:
        total += scrub_statedb(d, repl)
    log(f"state.db scrubbed: {total} session-column updates")

    # restart services so the new default loads.
    # SAFE: list-form, shell=False, SERVICES is a fixed module constant → no shell, not injectable.
    subprocess.run(["systemctl", "restart"] + SERVICES, check=False, shell=False)  # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
    log(f"restarted: {SERVICES}")

    summary = "; ".join(f"{d} → {r}" for d, r in changes)
    notify(tg_token, tg_chat,
           f"✅ Hermes model-health: pulled model(s) auto-replaced.\n{summary}\n"
           f"config.yaml + {total} session pins updated, services restarted.")
    log("done")


if __name__ == "__main__":
    main()
