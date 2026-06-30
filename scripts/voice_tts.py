import sys
from gtts import gTTS

OUTPUT_PATH = "/tmp/voice_output.mp3"
LANG = "de"

def main():
    if len(sys.argv) < 2:
        print("Usage: voice_tts.py <text> [output_file]", file=sys.stderr)
        sys.exit(1)

    text = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else OUTPUT_PATH

    if not text.strip():
        print("Error: Text cannot be empty", file=sys.stderr)
        sys.exit(1)

    try:
        tts = gTTS(text=text, lang=LANG)
        tts.save(output_path)
        print(f"Audio saved to {output_path}")
    except Exception as e:
        print(f"Error generating speech: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
