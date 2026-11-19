import sys
import speech_recognition as sr

def listen():
    r = sr.Recognizer()
    r.dynamic_energy_threshold = True
    r.pause_threshold = 1.2  # 1.2s de silence comme Orion
    
    with sr.Microphone() as source:
        # Calibration rapide du bruit ambiant
        r.adjust_for_ambient_noise(source, duration=0.8)
        print('MICROPHONE_ACTIVE_LISTENING', flush=True)
        try:
            audio = r.listen(source, timeout=25, phrase_time_limit=25)
            # Reconnaissance en francais canadien / francais
            text = r.recognize_google(audio, language='fr-CA')
            print(f'CHRISTIAN_VOICE: {text}', flush=True)
        except sr.WaitTimeoutError:
            print('TIMEOUT_SILENCE', flush=True)
        except sr.UnknownValueError:
            print('AUDIO_UNCLEAR', flush=True)
        except Exception as e:
            print(f'ERROR: {e}', flush=True)

if __name__ == '__main__':
    listen()
