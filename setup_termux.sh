#!/bin/bash
# ============================================
# Setup per Termux (Android)
# Installa tutto il necessario per il voice agent
# ============================================

echo "=== Setup Voice Agent per Termux ==="
echo ""

# Aggiorna pacchetti
pkg update -y && pkg upgrade -y

# Installa Python e dipendenze di sistema
pkg install -y python python-pip
pkg install -y portaudio espeak
pkg install -y cmake ninja build-essential

# Installa Ollama per Termux
echo ""
echo "=== Installazione Ollama ==="
curl -fsSL https://ollama.com/install.sh | sh

# Installa dipendenze Python
pip install SpeechRecognition
pip install pyttsx3
pip install requests
pip install pyaudio
pip install vosk  # per STT offline

# Scarica il modello (dolphin-mistral, ~4.4GB)
echo ""
echo "=== Download modello dolphin-mistral ==="
echo "Questo scarica ~4.4GB, assicurati di avere spazio e WiFi."
echo ""
read -p "Vuoi scaricare il modello ora? (s/n): " choice
if [ "$choice" = "s" ] || [ "$choice" = "S" ]; then
    ollama pull dolphin-mistral
    echo "[OK] Modello scaricato!"
else
    echo "[!] Ricorda di scaricarlo dopo con: ollama pull dolphin-mistral"
fi

echo ""
echo "=== Setup completato! ==="
echo ""
echo "Per usare l'agente:"
echo "  1) In un terminale: ollama serve"
echo "  2) In un altro terminale: python src/voice_agent.py"
echo ""
