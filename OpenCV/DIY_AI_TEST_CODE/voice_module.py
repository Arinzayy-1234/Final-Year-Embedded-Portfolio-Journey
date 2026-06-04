import speech_recognition as sr

class VoiceCommander:
    """
    Module to handle Speech-to-Text conversion for InMoov commands.
    Requires: pip install SpeechRecognition PyAudio
    """
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.recognizer.dynamic_energy_threshold = True

    def calibrate(self, duration=0.8):
        """Calibrates the recognizer energy threshold for ambient noise."""
        try:
            with sr.Microphone() as source:
                print(f"🎤 [VOICE] Calibrating mic for ambient noise ({duration}s)... Please remain quiet.")
                self.recognizer.adjust_for_ambient_noise(source, duration=duration)
                print(f"✅ [VOICE] Calibration done. Target energy threshold: {self.recognizer.energy_threshold:.1f}")
                return True
        except Exception as e:
            print(f"❌ [VOICE] Calibration error: {e}")
            return False

    def listen_and_convert(self, should_calibrate=False):
        """Activates mic, listens, and returns recognized text."""
        try:
            with sr.Microphone() as source:
                if should_calibrate:
                    self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
                
                print("\n🎤 [VOICE MODE] LISTENING NOW... Speak clearly into the mic!")
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
    vc.calibrate()
    res = vc.listen_and_convert()
    print(f"Result: {res}")
