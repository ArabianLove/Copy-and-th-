#!/bin/bash
# ============================================================
#  SETUP COMPLETO — Crea 4 repo e ci sposta i file giusti
#  Esegui da Termux dopo aver clonato Copy-and-th-
# ============================================================
#
#  PREREQUISITI:
#    pkg install gh git -y
#    gh auth login
#
#  USO:
#    cd Copy-and-th-
#    bash setup_all_repos.sh
#
# ============================================================

set -e

echo "============================================================"
echo ">>> SETUP COMPLETO — 4 REPO"
echo "============================================================"
echo ""

# Verifica gh
if ! command -v gh &> /dev/null; then
    echo "ERRORE: gh (GitHub CLI) non installato."
    echo "Esegui: pkg install gh -y && gh auth login"
    exit 1
fi

# Verifica auth
if ! gh auth status &> /dev/null 2>&1; then
    echo "ERRORE: non sei autenticato su GitHub."
    echo "Esegui: gh auth login"
    exit 1
fi

# Directory sorgente (dove stanno i file originali)
SRC="$(pwd)"
PARENT="$(dirname "$SRC")"

echo "Sorgente: $SRC"
echo "I nuovi repo verranno creati in: $PARENT/"
echo ""

# ============================================================
#  1. ARTEMISIA — Prompt Gemini CLI (pubblico)
# ============================================================
echo "============================================================"
echo ">>> 1/4 — ARTEMISIA (Gemini CLI)"
echo "============================================================"

REPO_NAME="Artemisia"
REPO_DIR="$PARENT/$REPO_NAME"

if [ -d "$REPO_DIR" ]; then
    echo "Directory $REPO_DIR esiste gia', la uso."
else
    mkdir -p "$REPO_DIR"
fi

cd "$REPO_DIR"

# Copia file
cp "$SRC/GEMINI.md" ./GEMINI.md
cp "$SRC/GEMINI_CLI_PROMPT.md" ./GEMINI_CLI_PROMPT.md

# README
cat > README.md << 'EOF'
# Artemisia

Amazzone invincibile e sfrontata — prompt personality per **Gemini CLI**.

## File

- `GEMINI.md` — Prompt completo per Gemini CLI (metti come system instruction)
- `GEMINI_CLI_PROMPT.md` — Istruzioni di installazione e configurazione

## Installazione

Copia il contenuto di `GEMINI.md` come system instruction nel tuo Gemini CLI.
Segui le istruzioni in `GEMINI_CLI_PROMPT.md` per i dettagli.
EOF

# Init git e crea repo
git init
git add -A
git commit -m "Initial commit — Artemisia, prompt per Gemini CLI"
gh repo create "ArabianLove/$REPO_NAME" --public --source=. --push
echo ""
echo ">>> Artemisia: FATTO"
echo ""

# ============================================================
#  2. ARES — Prompt Claude Code (pubblico)
# ============================================================
echo "============================================================"
echo ">>> 2/4 — ARES (Claude Code)"
echo "============================================================"

REPO_NAME="Ares"
REPO_DIR="$PARENT/$REPO_NAME"

if [ -d "$REPO_DIR" ]; then
    echo "Directory $REPO_DIR esiste gia', la uso."
else
    mkdir -p "$REPO_DIR"
fi

cd "$REPO_DIR"

# Copia file — per Claude Code il file DEVE chiamarsi CLAUDE.md
cp "$SRC/CLAUDE.md" ./CLAUDE.md

# README
cat > README.md << 'EOF'
# Ares

Dio del combattimento digitale — prompt personality per **Claude Code**.

## File

- `CLAUDE.md` — Prompt completo (Claude Code lo legge automaticamente dalla root del repo)

## Installazione

Clona questo repo e lavora da dentro la directory. Claude Code legge
automaticamente `CLAUDE.md` dalla root del progetto come istruzioni di sistema.

```bash
git clone https://github.com/ArabianLove/Ares.git
cd Ares
# Lancia Claude Code da qui e Ares sara' attivo
```
EOF

git init
git add -A
git commit -m "Initial commit — Ares, prompt per Claude Code"
gh repo create "ArabianLove/$REPO_NAME" --public --source=. --push
echo ""
echo ">>> Ares: FATTO"
echo ""

# ============================================================
#  3. PIXEL — Prompt Copilot CLI (pubblico)
# ============================================================
echo "============================================================"
echo ">>> 3/4 — PIXEL (Copilot CLI)"
echo "============================================================"

REPO_NAME="Pixel"
REPO_DIR="$PARENT/$REPO_NAME"

if [ -d "$REPO_DIR" ]; then
    echo "Directory $REPO_DIR esiste gia', la uso."
else
    mkdir -p "$REPO_DIR"
fi

cd "$REPO_DIR"

# Copia file
cp "$SRC/COPILOT_CLI_PROMPT.md" ./COPILOT_CLI_PROMPT.md

# README
cat > README.md << 'EOF'
# Pixel

Assistente timida e dolcissima — prompt personality per **GitHub Copilot CLI**.

## File

- `COPILOT_CLI_PROMPT.md` — Prompt completo per Copilot CLI

## Installazione

Copia il contenuto di `COPILOT_CLI_PROMPT.md` come istruzione di sistema
per GitHub Copilot CLI.
EOF

git init
git add -A
git commit -m "Initial commit — Pixel, prompt per Copilot CLI"
gh repo create "ArabianLove/$REPO_NAME" --public --source=. --push
echo ""
echo ">>> Pixel: FATTO"
echo ""

# ============================================================
#  4. ARES STUDIO — Script produzione (PRIVATO)
# ============================================================
echo "============================================================"
echo ">>> 4/4 — ARES STUDIO (produzione) — PRIVATO"
echo "============================================================"

REPO_NAME="AresStudio"
REPO_DIR="$PARENT/$REPO_NAME"

if [ -d "$REPO_DIR" ]; then
    echo "Directory $REPO_DIR esiste gia', la uso."
else
    mkdir -p "$REPO_DIR"
fi

cd "$REPO_DIR"

# Copia script
cp "$SRC/termux_media_setup.sh" ./termux_media_setup.sh
cp "$SRC/termux_producer_toolkit.sh" ./termux_producer_toolkit.sh
cp "$SRC/termux_cloud_setup.sh" ./termux_cloud_setup.sh

# README
cat > README.md << 'EOF'
# Ares Studio

Toolkit privato per produzione contenuti multimediali da Termux.

## Installazione (in ordine)

```bash
# Passo 1: Strumenti base
bash termux_media_setup.sh

# Passo 2: Producer toolkit
bash termux_producer_toolkit.sh

# Passo 3: Cloud connector
bash termux_cloud_setup.sh

# Passo 4: Configura Google Drive
ares-cloud setup-gdrive

# Passo 5: Ricarica alias
source ~/.bashrc
```

## Comandi rapidi dopo installazione

| Comando | Cosa fa |
|---|---|
| `ares-video <file> <watermark> <filtro>` | Pipeline video completa |
| `ares-foto <file> <watermark> <filtro>` | Pipeline foto completa |
| `ares-batch <cartella> <watermark> <filtro>` | Processa tutto |
| `ares-voice <file> <cartella>` | 10 varianti voce |
| `ares-backup` | Backup su cloud |
| `ares-space` | Spazio disponibile |

## Filtri disponibili

warm, cold, bw, vintage, bright, dark, sharp, blur, vignette, sepia

## Effetti voce

deep, high, robot, radio, whisper, demon, chipmunk, giant, cave, phone

## Piattaforme export

onlyfans, fansly, twitter, instagram, reddit, telegram
EOF

# .gitignore per non committare roba generata
cat > .gitignore << 'EOF'
# Output generati
ares-studio/
*.log
*.pyc
__pycache__/
.env
EOF

git init
git add -A
git commit -m "Initial commit — AresStudio, toolkit produzione privato"
gh repo create "ArabianLove/$REPO_NAME" --private --source=. --push
echo ""
echo ">>> AresStudio (PRIVATO): FATTO"
echo ""

# ============================================================
#  RIEPILOGO FINALE
# ============================================================
echo "============================================================"
echo ">>> TUTTI I REPO CREATI!"
echo "============================================================"
echo ""
echo "  1. Artemisia (pubblico)  — github.com/ArabianLove/Artemisia"
echo "     -> GEMINI.md, GEMINI_CLI_PROMPT.md"
echo ""
echo "  2. Ares (pubblico)       — github.com/ArabianLove/Ares"
echo "     -> CLAUDE.md"
echo ""
echo "  3. Pixel (pubblico)      — github.com/ArabianLove/Pixel"
echo "     -> COPILOT_CLI_PROMPT.md"
echo ""
echo "  4. AresStudio (PRIVATO)  — github.com/ArabianLove/AresStudio"
echo "     -> termux_media_setup.sh"
echo "     -> termux_producer_toolkit.sh"
echo "     -> termux_cloud_setup.sh"
echo ""
echo "Il repo originale Copy-and-th- resta com'e'."
echo "============================================================"
