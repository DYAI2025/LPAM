import sys
import speech_recognition as sr

def main():
    if len(sys.argv) < 2:
        print("Usage: voice_stt.py <audio_file>", file=sys.stderr)
        sys.exit(1)

    audio_path = sys.argv[1]
    recognizer = sr.Recognizer()

    try:
        with sr.AudioFile(audio_path) as source:
            audio = recognizer.record(source)
    except FileNotFoundError:
        print(f"Error: Audio file not found: {audio_path}", file=sys.stderr)
        sys.exit(1)
    except Exception as e:
        print(f"Error opening audio file: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        text = recognizer.recognize_google(audio)
        print(text)
    except sr.UnknownValueError:
        print("Error: Google Speech Recognition could not understand audio", file=sys.stderr)
        sys.exit(1)
    except sr.RequestError as e:
        print(f"Error: Could not request results from Google Speech Recognition service; {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
