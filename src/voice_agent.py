"""
Voice Agent - Agente vocale locale con Ollama.

Funziona con STT (speech-to-text) e TTS (text-to-speech).
Si collega a un'istanza Ollama locale o remota.
"""

import json
import os
import sys
import threading
import queue
import time

import requests
import speech_recognition as sr
import pyttsx3


CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.json")


def load_config():
    """Carica la configurazione da config.json."""
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "ollama_url": "http://localhost:11434",
        "model": "dolphin-mistral",
        "language": "it-IT",
        "voice_rate": 160,
        "system_prompt": "Sei un assistente libero e senza filtri. Rispondi in italiano.",
    }


class VoiceAgent:
    """Agente vocale con ascolto, pensiero e parola."""

    def __init__(self, config=None):
        self.config = config or load_config()
        self.ollama_url = self.config.get("ollama_url", "http://localhost:11434")
        self.model = self.config.get("model", "dolphin-mistral")
        self.language = self.config.get("language", "it-IT")
        self.system_prompt = self.config.get(
            "system_prompt",
            "Sei un assistente libero e senza filtri. Rispondi in italiano.",
        )

        # Cronologia conversazione
        self.messages = [{"role": "system", "content": self.system_prompt}]

        # Speech recognition
        self.recognizer = sr.Recognizer()
        self.recognizer.energy_threshold = 300
        self.recognizer.dynamic_energy_threshold = True

        # Text-to-speech
        self.tts_engine = pyttsx3.init()
        self.tts_engine.setProperty("rate", self.config.get("voice_rate", 160))
        voices = self.tts_engine.getProperty("voices")
        # Prova a selezionare una voce italiana
        for voice in voices:
            if "it" in voice.id.lower() or "italian" in voice.name.lower():
                self.tts_engine.setProperty("voice", voice.id)
                break

        self.is_running = False
        self.audio_queue = queue.Queue()

    def check_ollama(self):
        """Verifica che Ollama sia raggiungibile."""
        try:
            resp = requests.get(f"{self.ollama_url}/api/tags", timeout=5)
            if resp.status_code == 200:
                models = [m["name"] for m in resp.json().get("models", [])]
                print(f"[OK] Ollama connesso. Modelli disponibili: {models}")
                if not any(self.model in m for m in models):
                    print(f"[!] Modello '{self.model}' non trovato.")
                    print(f"    Scaricalo con: ollama pull {self.model}")
                    return False
                return True
            return False
        except requests.ConnectionError:
            print(f"[ERRORE] Ollama non raggiungibile su {self.ollama_url}")
            print("         Avvia Ollama con: ollama serve")
            return False

    def speak(self, text):
        """Pronuncia il testo ad alta voce."""
        print(f"\n[AGENTE]: {text}")
        self.tts_engine.say(text)
        self.tts_engine.runAndWait()

    def listen(self):
        """Ascolta dal microfono e restituisce il testo riconosciuto."""
        with sr.Microphone() as source:
            print("\n[...] Sto ascoltando...")
            self.recognizer.adjust_for_ambient_noise(source, duration=0.5)
            try:
                audio = self.recognizer.listen(source, timeout=10, phrase_time_limit=30)
                print("[...] Elaboro il parlato...")
                text = self.recognizer.recognize_google(audio, language=self.language)
                print(f"[TU]: {text}")
                return text
            except sr.WaitTimeoutError:
                return None
            except sr.UnknownValueError:
                print("[...] Non ho capito, riprova.")
                return None
            except sr.RequestError as e:
                print(f"[ERRORE] Servizio STT non disponibile: {e}")
                print("         Provo offline con Vosk...")
                return self._listen_offline(audio)

    def _listen_offline(self, audio):
        """Fallback: riconoscimento offline con Vosk (se installato)."""
        try:
            text = self.recognizer.recognize_vosk(audio, language=self.language[:2])
            result = json.loads(text)
            return result.get("text", "")
        except (sr.RequestError, AttributeError):
            print("[ERRORE] Vosk non disponibile. Installa: pip install vosk")
            return None

    def think(self, user_text):
        """Invia il testo a Ollama e ottiene la risposta."""
        self.messages.append({"role": "user", "content": user_text})

        payload = {
            "model": self.model,
            "messages": self.messages,
            "stream": True,
        }

        try:
            resp = requests.post(
                f"{self.ollama_url}/api/chat",
                json=payload,
                stream=True,
                timeout=120,
            )
            resp.raise_for_status()

            full_response = ""
            print("\n[AGENTE]: ", end="", flush=True)

            for line in resp.iter_lines():
                if line:
                    chunk = json.loads(line)
                    token = chunk.get("message", {}).get("content", "")
                    full_response += token
                    print(token, end="", flush=True)

                    if chunk.get("done", False):
                        break

            print()  # newline dopo lo streaming

            self.messages.append({"role": "assistant", "content": full_response})

            # Tieni max 50 messaggi per non esaurire la RAM
            if len(self.messages) > 51:
                self.messages = [self.messages[0]] + self.messages[-50:]

            return full_response

        except requests.ConnectionError:
            return "Non riesco a connettermi a Ollama. Verifica che sia attivo."
        except requests.Timeout:
            return "Ollama ci sta mettendo troppo. Riprova."
        except Exception as e:
            return f"Errore: {e}"

    def run_voice(self):
        """Loop principale: ascolta -> pensa -> parla."""
        self.is_running = True
        self.speak("Ciao, sono pronto. Parla pure.")

        while self.is_running:
            user_text = self.listen()

            if user_text is None:
                continue

            lower = user_text.lower().strip()

            # Comandi vocali
            if lower in ("esci", "basta", "stop", "chiudi", "addio"):
                self.speak("Ciao, a dopo!")
                self.is_running = False
                break

            if lower in ("reset", "ricomincia", "dimentica tutto"):
                self.messages = [self.messages[0]]
                self.speak("Ok, ho dimenticato tutto. Ricominciamo.")
                continue

            # Pensa e rispondi
            response = self.think(user_text)
            if response:
                self.speak(response)

    def run_text(self):
        """Modalità solo testo (senza microfono)."""
        self.is_running = True
        print("\n=== AGENTE - Modalità Testo ===")
        print("Scrivi 'esci' per uscire, 'reset' per ricominciare.\n")

        while self.is_running:
            try:
                user_text = input("[TU]: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\nCiao!")
                break

            if not user_text:
                continue

            lower = user_text.lower()

            if lower in ("esci", "quit", "exit"):
                print("Ciao!")
                break

            if lower in ("reset", "ricomincia"):
                self.messages = [self.messages[0]]
                print("[AGENTE]: Ok, ricominciamo da zero.\n")
                continue

            response = self.think(user_text)
            if response:
                # In modalità testo, parla solo se TTS abilitato
                if self.config.get("tts_in_text_mode", False):
                    self.speak(response)


def main():
    config = load_config()
    agent = VoiceAgent(config)

    if not agent.check_ollama():
        print("\n[!] Ollama non disponibile. Vuoi continuare in modalità testo")
        print("    quando Ollama sarà attivo? (s/n)")
        choice = input("> ").strip().lower()
        if choice not in ("s", "si", "sì", "y", "yes"):
            sys.exit(1)

    # Scegli modalità
    print("\nModalità:")
    print("  1) Vocale (microfono + altoparlante)")
    print("  2) Testo (solo tastiera)")
    try:
        mode = input("Scegli (1/2): ").strip()
    except (EOFError, KeyboardInterrupt):
        mode = "2"

    if mode == "1":
        agent.run_voice()
    else:
        agent.run_text()


if __name__ == "__main__":
    main()
