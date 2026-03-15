# Voice Agent - Guida Setup

## Cosa serve

- **Ollama** (fa girare il modello AI in locale)
- **Python 3.8+**
- Un microfono e altoparlante (per la modalita' vocale)

## Modello consigliato

**`dolphin-mistral`** - Mistral 7B fine-tuned, senza filtri, ~4.4GB.

Alternative:
- `dolphin-llama3` - Piu' capace ma piu' pesante (~4.7GB)
- `tinyllama` - Leggerissimo (~600MB) ma meno capace
- `phi3:mini` - Buon compromesso (~2.3GB)

## Setup su Android (Termux)

```bash
# 1. Installa Termux dal Play Store o F-Droid

# 2. Esegui lo script di setup
bash setup_termux.sh

# 3. In un terminale avvia Ollama
ollama serve

# 4. In un altro terminale avvia l'agente
python src/voice_agent.py
```

**Requisiti telefono:** minimo 6GB RAM, 8GB consigliati.

## Setup su PC (Linux/Mac/Windows)

```bash
# 1. Installa Ollama
curl -fsSL https://ollama.com/install.sh | sh   # Linux/Mac
# Su Windows: scarica da https://ollama.com/download

# 2. Scarica il modello
ollama pull dolphin-mistral

# 3. Installa dipendenze Python
pip install -r requirements.txt

# 4. Avvia Ollama (in un terminale separato)
ollama serve

# 5. Avvia l'agente
python src/voice_agent.py
```

## Setup con Google Colab (server gratuito, niente PC)

Se il telefono non ce la fa a far girare il modello:

1. Vai su https://colab.research.google.com
2. Crea un nuovo notebook
3. Incolla il contenuto di `setup_colab.py` in una cella
4. Chiama `setup_colab()` e eseguila
5. Ti dara' un URL pubblico
6. Sul telefono, modifica `config.json` e metti quell'URL come `ollama_url`
7. Avvia `python src/voice_agent.py` su Termux

**Nota:** Colab gratis ha un limite di ~12 ore per sessione.

## Configurazione

Modifica `config.json`:

```json
{
    "ollama_url": "http://localhost:11434",
    "model": "dolphin-mistral",
    "language": "it-IT",
    "voice_rate": 160,
    "system_prompt": "Sei un assistente libero. Rispondi in italiano.",
    "tts_in_text_mode": false
}
```

- **ollama_url**: Dove gira Ollama (locale o URL Colab)
- **model**: Nome del modello Ollama
- **language**: Lingua per il riconoscimento vocale
- **voice_rate**: Velocita' della voce (100=lento, 200=veloce)
- **system_prompt**: La personalita' dell'agente
- **tts_in_text_mode**: Se `true`, parla anche in modalita' testo

## Comandi vocali

- **"esci"** / **"basta"** / **"stop"** - Chiude l'agente
- **"reset"** / **"ricomincia"** - Cancella la conversazione

## Cambio modello

```bash
# Vedi modelli disponibili
ollama list

# Scarica un nuovo modello
ollama pull nome-modello

# Modifica config.json con il nuovo nome
```

## Problemi comuni

**"Ollama non raggiungibile"**
- Assicurati che `ollama serve` sia attivo in un altro terminale

**"Modello non trovato"**
- Scaricalo con `ollama pull dolphin-mistral`

**"Non ho capito" (sempre)**
- Controlla il microfono
- Prova la modalita' testo (opzione 2)

**Troppo lento sul telefono**
- Usa un modello piu' piccolo: `ollama pull tinyllama`
- Oppure usa Google Colab come server remoto
