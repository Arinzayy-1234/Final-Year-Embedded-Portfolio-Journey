import speech_recognition as sr

class VoiceCommander:
    """
    Module to handle Speech-to-Text conversion for InMoov commands.
    Requires: pip install SpeechRecognition PyAudio
    """
    def __init__(self):
        self.recognizer = sr.Recognizer()
        # We don't initialize Microphone here to avoid keeping the mic "open" 
        # until the user actually presses the voice key.

    def listen_and_convert(self):
        """Activates mic, listens, and returns recognized text."""
        try:
            with sr.Microphone() as source:
                print("\n🎤 [VOICE MODE] Listening... Speak clearly into the mic.")
                self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                audio = self.recognizer.listen(source, timeout=5, phrase_time_limit=5)

            print("🧠 Processing voice...")
            text = self.recognizer.recognize_google(audio)
            print(f"✅ Recognized: '{text}'")
            return text.lower()

        except sr.WaitTimeoutError:
            print("⚠️ Timeout: No speech detected.")
            return None
        except sr.UnknownValueError:
            print("❌ ERROR: Could not understand audio.")
            return None
        except sr.RequestError as e:
            print(f"❌ ERROR: Speech Service unavailable; {e}")
            return None
        except Exception as e:
            print(f"❌ UNEXPECTED ERROR: {e}")
            return None

if __name__ == "__main__":
    # Test script
    vc = VoiceCommander()
    res = vc.listen_and_convert()
    print(f"Result: {res}")
