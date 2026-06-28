#!/bin/bash

# Farben für schönere Terminal-Ausgaben
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0;3m' # No Color

echo -e "${BLUE}🎙️ [Jarvis-Mode] Sprachschleife gestartet. Ich höre ununterbrochen zu...${NC}"
ssh mac say "Sprachschleife aktiviert. Ich höre zu, Chef." 2>/dev/null

while true; do
    echo -e "\n${BLUE}➔ Lausche... (Sprich jetzt)${NC}"
    
    # 1. Mac-Mikrofon aktivieren und das Transkript abfangen
    # Nutzt das von Claude optimierte VAD-System
    USER_TEXT=$(ssh mac listen 15 2>/dev/null)
    
    # Bereinigung von Whitespaces
    USER_TEXT=$(echo "$USER_TEXT" | xargs)
    
    # Filter für Stille, Fehlzündungen oder typische Whisper-Halluzinationen bei Stille
    if [[ -z "$USER_TEXT" || "$USER_TEXT" == *"(no speech detected)"* || "$USER_TEXT" == *"REC_FAILED"* || "$USER_TEXT" == *"(Bedrohliche Musik)"* || "$USER_TEXT" == *"Untertitel"* ]]; then
        # Wenn nichts gesagt wurde, Schleife ohne Verzögerung neu starten
        sleep 0.2
        continue
    fi
    
    echo -e "${GREEN}👤 Du:${NC} $USER_TEXT"
    echo -e "${BLUE}🤖 Hermes denkt nach...${NC}"
    
    # 2. Den Text an unser pfeilschnelles, kostenloses OpenCode-Cloud-Modell übergeben
    # Wir fügen einen System-Prompt hinzu, damit Hermes als Voice-Assistent antwortet und nicht als Debugger
    SYSTEM_PROMPT="Du bist Hermes, ein smarter, prägnanter Voice-Assistent. Antworte kurz, natürlich und direkt an deinen Chef. Vermeide technischen Meta-Talk oder Erklärungen über das Modell selbst. User sagt: "
    RAW_RESPONSE=$(/root/lpam/scripts/bridge_opencode.py "$SYSTEM_PROMPT$USER_TEXT" 2>/dev/null)
    
    # Extrahiert den Text zwischen den OpenCode-Agenten-Markern
    RESPONSE=$(echo "$RAW_RESPONSE" | sed -n '/=== OPENCODE OUTPUT AGENT ===/,/=============================/p' | sed '1d;$d' | xargs)
    
    # Falls die Extraktion fehlschlägt, nehmen wir den rohen Output
    if [ -z "$RESPONSE" ]; then
        RESPONSE=$(echo "$RAW_RESPONSE" | grep -v "Bridge" | grep -v "==" | xargs)
    fi
    
    # Sicherheits-Fallback falls leer
    if [ -z "$RESPONSE" ]; then
        RESPONSE="Ich habe dich verstanden, konnte aber keine Antwort generieren."
    fi
    
    echo -e "${GREEN}🤖 Hermes:${NC} $RESPONSE"
    
    # 3. Die Antwort direkt über deine Mac-Lautsprecher ausgeben
    ssh mac say "$RESPONSE" 2>/dev/null
    
    # Kurze Atempause vor der nächsten Aufnahme
    sleep 0.5
done
