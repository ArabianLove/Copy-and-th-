# Guida Termux - Copia e Incolla

Apri Termux e copia-incolla ogni blocco, uno alla volta.
Aspetta che finisce prima di fare il prossimo.

## Passo 1: Aggiorna Termux

```
pkg update -y && pkg upgrade -y
```

## Passo 2: Installa Python e strumenti

```
pkg install -y python python-pip git portaudio espeak cmake
```

## Passo 3: Installa Ollama

```
curl -fsSL https://ollama.com/install.sh | sh
```

## Passo 4: Scarica il modello (4.4GB, usa WiFi)

```
ollama serve &
sleep 5
ollama pull dolphin-mistral
```

Aspetta che finisce, ci mette qualche minuto.

## Passo 5: Scarica il codice da GitHub

```
git clone https://github.com/ArabianLove/Copy-and-th-.git agente
cd agente
```

## Passo 6: Installa le librerie Python

```
pip install SpeechRecognition pyttsx3 requests pyaudio vosk
```

## Passo 7: Avvia l'agente

```
python src/voice_agent.py
```

Ti chiede: modalita' 1 (voce) o 2 (testo). Scegli 2 la prima volta per testare.

Scrivi qualcosa e lui risponde.

## Per le volte dopo

Ogni volta che riapri Termux:

```
ollama serve &
sleep 3
cd agente
python src/voice_agent.py
```

Fine.
