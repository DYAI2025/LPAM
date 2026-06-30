#!/usr/bin/env python3
"""Minimal stdio MCP server over an Obsidian vault.
Zero deps. Exposes keyword search + read + graph-link tools so any local MCP
client (Claude Code, Hermes desktop, etc.) can use the vault as permanent
knowledge/context. Vault: $VAULT_DIR or ~/SemanticMind-Vault.
Logs to stderr only (stdout = protocol)."""
import sys, os, json, re, glob

VAULT = os.environ.get("VAULT_DIR", os.path.expanduser("~/SemanticMind-Vault"))

def log(*a): print(*a, file=sys.stderr, flush=True)

def pages():
    return sorted(glob.glob(os.path.join(VAULT, "**", "*.md"), recursive=True))

def page_name(p):
    return os.path.splitext(os.path.basename(p))[0]

def find_page(name):
    name = name.strip().lower()
    cands = pages()
    for p in cands:
        if page_name(p).lower() == name:
            return p
    for p in cands:
        if name in page_name(p).lower():
            return p
    return None

# ---- tools ----
def t_search(query, limit=8):
    q = (query or "").lower().strip()
    terms = [t for t in re.split(r"\s+", q) if len(t) > 1]
    if not terms:
        return "empty query"
    scored = []
    for p in pages():
        try:
            text = open(p, encoding="utf-8").read()
        except Exception:
            continue
        low = text.lower()
        score = sum(low.count(t) for t in terms)
        name_bonus = sum(3 for t in terms if t in page_name(p).lower())
        score += name_bonus
        if score > 0:
            snip = ""
            for line in text.splitlines():
                if any(t in line.lower() for t in terms) and not line.startswith("---"):
                    snip = line.strip()[:160]; break
            rel = os.path.relpath(p, VAULT)
            scored.append((score, rel, page_name(p), snip))
    scored.sort(reverse=True)
    if not scored:
        return f"No vault pages match: {query}"
    out = [f"{len(scored)} hits for '{query}' (top {min(limit,len(scored))}):"]
    for sc, rel, nm, snip in scored[:limit]:
        out.append(f"• [[{nm}]] ({rel}) — {snip}")
    return "\n".join(out)

def t_read(page):
    p = find_page(page)
    if not p:
        return f"page not found: {page}"
    txt = open(p, encoding="utf-8").read()
    return txt[:24000]

def t_map():
    p = os.path.join(VAULT, "_MOC.md")
    return open(p, encoding="utf-8").read() if os.path.exists(p) else "no _MOC.md"

def t_links(page):
    p = find_page(page)
    if not p:
        return f"page not found: {page}"
    text = open(p, encoding="utf-8").read()
    out_links = sorted(set(re.findall(r"\[\[([^\]\|]+)", text)))
    nm = page_name(p)
    back = []
    for q in pages():
        if q == p:
            continue
        try:
            qt = open(q, encoding="utf-8").read()
        except Exception:
            continue
        if re.search(r"\[\[" + re.escape(nm) + r"(\||\])", qt):
            back.append(page_name(q))
    return json.dumps({"page": nm, "outgoing": out_links, "backlinks": sorted(set(back))}, ensure_ascii=False, indent=2)

TOOLS = [
    {"name":"vault_search","description":"Keyword search across the Obsidian vault (project knowledge base). Returns ranked pages + snippets. Use FIRST when a question touches any project.",
     "inputSchema":{"type":"object","properties":{"query":{"type":"string"},"limit":{"type":"integer"}},"required":["query"]}},
    {"name":"vault_read","description":"Read a full vault page by name/slug (project or concept). Fuzzy match.",
     "inputSchema":{"type":"object","properties":{"page":{"type":"string"}},"required":["page"]}},
    {"name":"vault_map","description":"Read _MOC.md — the map of content (clusters + central concept nodes). Start here to orient.",
     "inputSchema":{"type":"object","properties":{}}},
    {"name":"vault_links","description":"Outgoing wikilinks + backlinks for a page (graph neighbours).",
     "inputSchema":{"type":"object","properties":{"page":{"type":"string"}},"required":["page"]}},
]

def call(name, args):
    args = args or {}
    if name == "vault_search": return t_search(args.get("query",""), int(args.get("limit",8)))
    if name == "vault_read":   return t_read(args.get("page",""))
    if name == "vault_map":    return t_map()
    if name == "vault_links":  return t_links(args.get("page",""))
    return f"unknown tool: {name}"

def send(obj):
    sys.stdout.write(json.dumps(obj) + "\n"); sys.stdout.flush()

def main():
    log(f"vault-mcp up, VAULT={VAULT}, pages={len(pages())}")
    for line in sys.stdin:
        line = line.strip()
        if not line: continue
        try:
            msg = json.loads(line)
        except Exception as e:
            log("bad json", e); continue
        mid = msg.get("id"); method = msg.get("method")
        if method == "initialize":
            send({"jsonrpc":"2.0","id":mid,"result":{
                "protocolVersion":"2024-11-05",
                "capabilities":{"tools":{}},
                "serverInfo":{"name":"obsidian-vault","version":"1.0.0"}}})
        elif method == "notifications/initialized":
            pass
        elif method == "tools/list":
            send({"jsonrpc":"2.0","id":mid,"result":{"tools":TOOLS}})
        elif method == "tools/call":
            params = msg.get("params",{})
            try:
                text = call(params.get("name"), params.get("arguments"))
                send({"jsonrpc":"2.0","id":mid,"result":{"content":[{"type":"text","text":text}]}})
            except Exception as e:
                send({"jsonrpc":"2.0","id":mid,"result":{"content":[{"type":"text","text":f"error: {e}"}],"isError":True}})
        elif method == "ping":
            send({"jsonrpc":"2.0","id":mid,"result":{}})
        elif mid is not None:
            send({"jsonrpc":"2.0","id":mid,"error":{"code":-32601,"message":f"method not found: {method}"}})

if __name__ == "__main__":
    main()
