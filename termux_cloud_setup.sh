#!/bin/bash
# ============================================================
#  ARES CLOUD CONNECTOR — Collega Termux al cloud storage
#  Supporta: Google Drive, Dropbox, OneDrive, S3, MEGA, pCloud
#  Tutto automatizzato. Un comando e sei connesso.
# ============================================================

echo ">>> ARES CLOUD CONNECTOR"
echo ""

# ============================================================
#  INSTALLAZIONE RCLONE (se non presente)
# ============================================================
if ! command -v rclone &> /dev/null; then
    echo ">>> Installo rclone..."
    pkg update -y
    pkg install -y rclone
else
    echo ">>> rclone gia' installato: $(rclone version | head -1)"
fi

# Crea directory di appoggio
STUDIO="$HOME/ares-studio"
mkdir -p "$STUDIO"

# ============================================================
#  SCRIPT PYTHON — CLOUD MANAGER
# ============================================================

cat > "$STUDIO/ares_cloud.py" << 'CLOUD_SCRIPT'
#!/usr/bin/env python3
"""
ARES CLOUD MANAGER
Gestione cloud storage da Termux.
Supporta: Google Drive, Dropbox, OneDrive, S3, MEGA, pCloud
"""

import os
import sys
import subprocess
import json
from datetime import datetime

STUDIO = os.path.expanduser("~/ares-studio")
CLOUD_CONFIG = os.path.join(STUDIO, "cloud_config.json")


def log(msg):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    line = f"[{timestamp}] {msg}"
    print(line)
    log_file = os.path.join(STUDIO, "logs", "cloud.log")
    os.makedirs(os.path.dirname(log_file), exist_ok=True)
    with open(log_file, "a") as f:
        f.write(line + "\n")


def run(cmd):
    log(f"CMD: {cmd}")
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    if result.returncode != 0:
        log(f"ERRORE: {result.stderr[:500]}")
    return result


# ============================================================
#  CONFIGURAZIONE CLOUD
# ============================================================

def cloud_setup_gdrive(remote_name="gdrive"):
    """
    Configura Google Drive.
    rclone usa OAuth — ti da' un link, tu lo apri nel browser,
    autorizzi, e incolli il codice.
    """
    print(f"""
=== CONFIGURAZIONE GOOGLE DRIVE ===

Segui questi passi:

1. Esegui questo comando:
   rclone config

2. Quando chiede "n/s/q/r/c/d/q": scrivi  n  (new remote)
3. Nome: {remote_name}
4. Storage type: cerca "Google Drive" (di solito numero 18 o 19)
5. client_id: lascia vuoto (premi Invio)
6. client_secret: lascia vuoto (premi Invio)
7. scope: scegli 1 (full access)
8. root_folder_id: lascia vuoto
9. service_account_file: lascia vuoto
10. Edit advanced config: No
11. Use auto config: No (sei su Termux)
12. Ti da' un LINK — copialo e aprilo nel browser del telefono
13. Autorizza con il tuo account Google
14. Copia il codice che ti da' e incollalo in Termux
15. Configure as team drive: No
16. Conferma: Yes

Fatto! Hai 15GB gratis su Google Drive.
""")
    os.system("rclone config")


def cloud_setup_dropbox(remote_name="dropbox"):
    """Configura Dropbox."""
    print(f"""
=== CONFIGURAZIONE DROPBOX ===

1. Esegui: rclone config
2. New remote: {remote_name}
3. Storage: cerca "Dropbox"
4. client_id/secret: lascia vuoto
5. Edit advanced: No
6. Use auto config: No
7. Segui il link per autorizzare
8. Incolla il token

Dropbox free: 2GB (poco ma utile per backup importanti)
""")
    os.system("rclone config")


def cloud_setup_mega(remote_name="mega"):
    """Configura MEGA."""
    print(f"""
=== CONFIGURAZIONE MEGA ===

1. Esegui: rclone config
2. New remote: {remote_name}
3. Storage: cerca "MEGA"
4. Inserisci email e password del tuo account MEGA
5. Conferma

MEGA free: 20GB — ottimo per backup!
""")
    os.system("rclone config")


# ============================================================
#  OPERAZIONI CLOUD
# ============================================================

def cloud_list_remotes():
    """Mostra tutti i cloud configurati."""
    result = run("rclone listremotes")
    remotes = result.stdout.strip().split("\n") if result.stdout.strip() else []
    if remotes and remotes[0]:
        print("\n=== CLOUD CONFIGURATI ===")
        for r in remotes:
            print(f"  {r}")
            # Mostra spazio usato
            info = run(f"rclone about {r} 2>/dev/null")
            if info.stdout:
                for line in info.stdout.strip().split("\n"):
                    print(f"    {line}")
    else:
        print("\nNessun cloud configurato. Usa:")
        print("  python ares_cloud.py setup-gdrive")
        print("  python ares_cloud.py setup-dropbox")
        print("  python ares_cloud.py setup-mega")
    return remotes


def cloud_upload(local_path, remote, remote_path="ares-studio"):
    """Upload file o cartella al cloud."""
    if os.path.isdir(local_path):
        cmd = f'rclone copy "{local_path}" {remote}{remote_path}/ --progress'
    else:
        cmd = f'rclone copy "{local_path}" {remote}{remote_path}/ --progress'
    print(f"\n>>> Upload: {local_path} -> {remote}{remote_path}/")
    os.system(cmd)  # os.system per vedere il progresso in tempo reale
    log(f"Upload completato: {local_path} -> {remote}{remote_path}/")


def cloud_download(remote, remote_path, local_path):
    """Download dal cloud."""
    cmd = f'rclone copy {remote}{remote_path} "{local_path}" --progress'
    print(f"\n>>> Download: {remote}{remote_path} -> {local_path}")
    os.system(cmd)
    log(f"Download completato: {remote}{remote_path} -> {local_path}")


def cloud_sync_exports(remote, remote_path="ares-studio/export"):
    """Sincronizza TUTTI gli export al cloud."""
    export_dir = os.path.join(STUDIO, "export")
    if not os.path.exists(export_dir):
        log("Cartella export non trovata")
        return

    cmd = f'rclone copy "{export_dir}" {remote}{remote_path}/ --progress'
    print(f"\n>>> Sincronizzo export -> {remote}{remote_path}/")
    os.system(cmd)
    log(f"Export sincronizzati con {remote}")


def cloud_sync_full(remote, remote_path="ares-studio"):
    """Sincronizza TUTTO lo studio al cloud."""
    cmd = f'rclone copy "{STUDIO}" {remote}{remote_path}/ --progress --exclude "logs/**"'
    print(f"\n>>> Sincronizzo studio completo -> {remote}{remote_path}/")
    os.system(cmd)
    log(f"Studio sincronizzato con {remote}")


def cloud_ls(remote, remote_path=""):
    """Lista file nel cloud."""
    cmd = f'rclone ls {remote}{remote_path}'
    result = run(cmd)
    if result.stdout:
        print(f"\n=== FILE IN {remote}{remote_path} ===")
        print(result.stdout)
    else:
        print(f"Nessun file in {remote}{remote_path}")


def cloud_free_space(remote):
    """Mostra spazio disponibile nel cloud."""
    cmd = f'rclone about {remote}'
    result = run(cmd)
    if result.stdout:
        print(f"\n=== SPAZIO {remote} ===")
        print(result.stdout)


def cloud_delete(remote, remote_path):
    """Cancella un file dal cloud."""
    cmd = f'rclone delete {remote}{remote_path}'
    run(cmd)
    log(f"Cancellato dal cloud: {remote}{remote_path}")


def cloud_auto_backup():
    """
    Backup automatico: cerca il primo cloud configurato
    e ci carica tutti gli export.
    """
    result = run("rclone listremotes")
    remotes = result.stdout.strip().split("\n") if result.stdout.strip() else []
    if not remotes or not remotes[0]:
        print("Nessun cloud configurato! Configura prima con:")
        print("  python ares_cloud.py setup-gdrive")
        return

    remote = remotes[0]  # Usa il primo cloud configurato
    print(f">>> Backup automatico su {remote}")
    cloud_sync_exports(remote)
    print(f"\n>>> Backup completato su {remote}")


# ============================================================
#  CALCOLO SPAZIO LOCALE
# ============================================================

def local_space_check():
    """Mostra quanto spazio usi e quanto ne resta."""
    print("\n=== SPAZIO SUL TELEFONO ===")

    # Spazio studio
    if os.path.exists(STUDIO):
        result = run(f'du -sh "{STUDIO}"')
        if result.stdout:
            print(f"  Studio: {result.stdout.strip().split()[0]}")

        # Dettaglio per cartella
        for folder in ["raw", "edited", "watermarked", "export",
                        "thumbnails", "audio", "voice"]:
            folder_path = os.path.join(STUDIO, folder)
            if os.path.exists(folder_path):
                r = run(f'du -sh "{folder_path}"')
                if r.stdout:
                    size = r.stdout.strip().split()[0]
                    print(f"    {folder}/: {size}")

    # Spazio totale disponibile
    result = run("df -h $HOME | tail -1")
    if result.stdout:
        parts = result.stdout.strip().split()
        if len(parts) >= 4:
            print(f"\n  Disco totale: {parts[1]}")
            print(f"  Usato: {parts[2]}")
            print(f"  Disponibile: {parts[3]}")
            print(f"  Uso: {parts[4]}")


# ============================================================
#  CLI
# ============================================================

def print_help():
    print("""
ARES CLOUD MANAGER

SETUP (da fare una volta):
  python ares_cloud.py setup-gdrive     Configura Google Drive (15GB gratis)
  python ares_cloud.py setup-dropbox    Configura Dropbox (2GB gratis)
  python ares_cloud.py setup-mega       Configura MEGA (20GB gratis)

OPERAZIONI:
  python ares_cloud.py list             Mostra cloud configurati
  python ares_cloud.py upload <file_o_cartella> <remote:> [percorso]
  python ares_cloud.py download <remote:> <percorso> <destinazione_locale>
  python ares_cloud.py sync-exports <remote:>   Carica tutti gli export
  python ares_cloud.py sync-full <remote:>       Carica TUTTO lo studio
  python ares_cloud.py backup           Backup auto sul primo cloud
  python ares_cloud.py ls <remote:> [percorso]   Lista file nel cloud
  python ares_cloud.py space <remote:>  Spazio disponibile nel cloud
  python ares_cloud.py local-space      Spazio sul telefono
  python ares_cloud.py delete <remote:> <percorso>  Cancella dal cloud

ESEMPI:
  python ares_cloud.py setup-gdrive
  python ares_cloud.py upload ~/ares-studio/export/ gdrive:
  python ares_cloud.py sync-exports gdrive:
  python ares_cloud.py backup
  python ares_cloud.py local-space
""")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print_help()
        sys.exit(0)

    cmd = sys.argv[1]

    # Setup
    if cmd == "setup-gdrive":
        name = sys.argv[2] if len(sys.argv) > 2 else "gdrive"
        cloud_setup_gdrive(name)
    elif cmd == "setup-dropbox":
        name = sys.argv[2] if len(sys.argv) > 2 else "dropbox"
        cloud_setup_dropbox(name)
    elif cmd == "setup-mega":
        name = sys.argv[2] if len(sys.argv) > 2 else "mega"
        cloud_setup_mega(name)

    # Operazioni
    elif cmd == "list":
        cloud_list_remotes()
    elif cmd == "upload" and len(sys.argv) >= 4:
        remote_path = sys.argv[4] if len(sys.argv) > 4 else "ares-studio"
        cloud_upload(sys.argv[2], sys.argv[3], remote_path)
    elif cmd == "download" and len(sys.argv) >= 5:
        cloud_download(sys.argv[2], sys.argv[3], sys.argv[4])
    elif cmd == "sync-exports" and len(sys.argv) >= 3:
        cloud_sync_exports(sys.argv[2])
    elif cmd == "sync-full" and len(sys.argv) >= 3:
        cloud_sync_full(sys.argv[2])
    elif cmd == "backup":
        cloud_auto_backup()
    elif cmd == "ls" and len(sys.argv) >= 3:
        path = sys.argv[3] if len(sys.argv) > 3 else ""
        cloud_ls(sys.argv[2], path)
    elif cmd == "space" and len(sys.argv) >= 3:
        cloud_free_space(sys.argv[2])
    elif cmd == "local-space":
        local_space_check()
    elif cmd == "delete" and len(sys.argv) >= 4:
        cloud_delete(sys.argv[2], sys.argv[3])
    else:
        print_help()
CLOUD_SCRIPT

chmod +x "$STUDIO/ares_cloud.py"

# ============================================================
#  ALIAS CLOUD
# ============================================================

cat >> ~/.bashrc << 'CLOUD_ALIASES'

# === ARES CLOUD ALIASES ===
alias ares-cloud='python $HOME/ares-studio/ares_cloud.py'
alias ares-backup='python $HOME/ares-studio/ares_cloud.py backup'
alias ares-upload='python $HOME/ares-studio/ares_cloud.py upload'
alias ares-sync='python $HOME/ares-studio/ares_cloud.py sync-exports'
alias ares-space='python $HOME/ares-studio/ares_cloud.py local-space'
# === FINE ARES CLOUD ALIASES ===
CLOUD_ALIASES

echo ""
echo "============================================================"
echo ">>> ARES CLOUD CONNECTOR — INSTALLATO!"
echo "============================================================"
echo ""
echo "SETUP RAPIDO (fai UNA volta):"
echo ""
echo "  1. Google Drive (15GB gratis):"
echo "     ares-cloud setup-gdrive"
echo ""
echo "  2. MEGA (20GB gratis):"
echo "     ares-cloud setup-mega"
echo ""
echo "  3. Dropbox (2GB gratis):"
echo "     ares-cloud setup-dropbox"
echo ""
echo "DOPO IL SETUP:"
echo ""
echo "  Backup veloce (un comando):"
echo "     ares-backup"
echo ""
echo "  Upload specifico:"
echo "     ares-upload ~/ares-studio/export/ gdrive:"
echo ""
echo "  Controlla spazio telefono:"
echo "     ares-space"
echo ""
echo "============================================================"
