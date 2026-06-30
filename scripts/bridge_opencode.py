#!/usr/bin/env python3
import sys
import subprocess

def call_opencode_headless(prompt_text):
    print(f"[Bridge] Sende Aufgabe an OpenCode (Nutze Free-Cloud-Modell)...")
    
    # Wir zwingen OpenCode, das kostenlose DeepSeek-Modell aus der Cloud zu nutzen
    cmd = [
        "opencode", 
        "--model", "opencode/deepseek-v4-flash-free", 
        "run", 
        prompt_text
    ]
    
    try:
        # Führt OpenCode aus und fängt den reinen Text-Output ab.
        # SAFE: argument-vector form with shell=False — `prompt_text` is passed as a
        # single argv element, never parsed by a shell, so it cannot inject a command.
        # The opengrep "dangerous-subprocess-use-audit" rule is a heuristic false
        # positive here (it flags any non-literal first arg).
        # nosemgrep: python.lang.security.audit.dangerous-subprocess-use-audit
        result = subprocess.run(cmd, capture_output=True, text=True, check=True, shell=False)
        
        print("\n=== OPENCODE OUTPUT AGENT ===")
        if result.stdout.strip():
            print(result.stdout.strip())
        else:
            print("[Bridge] Aufgabe im Hintergrund ausgeführt (Code-Änderungen vorgenommen).")
        print("=============================\n")
        return True
        
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Fehler bei der Ausführung von OpenCode!", file=sys.stderr)
        print(e.stderr, file=sys.stderr)
        return False

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Nutzung: ./bridge_opencode.py '<Dein Prompt>'")
        sys.exit(1)
        
    prompt = sys.argv[1]
    success = call_opencode_headless(prompt)
    sys.exit(0 if success else 1)
