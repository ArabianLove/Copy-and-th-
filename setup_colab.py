"""
Setup per Google Colab (server gratuito).

Esegui questo notebook su Google Colab per avere Ollama gratis nel cloud.
Poi collegati dal telefono all'URL che ti da.

Istruzioni:
1. Vai su https://colab.research.google.com
2. Crea un nuovo notebook
3. Copia questo codice in una cella e eseguilo
"""


def setup_colab():
    """Esegui in una cella di Google Colab."""
    import subprocess
    import os

    # Installa Ollama
    print("[1/4] Installazione Ollama...")
    subprocess.run(
        "curl -fsSL https://ollama.com/install.sh | sh",
        shell=True,
        check=True,
    )

    # Avvia Ollama in background
    print("[2/4] Avvio Ollama...")
    subprocess.Popen(
        ["ollama", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )

    import time
    time.sleep(3)

    # Scarica il modello
    print("[3/4] Download modello dolphin-mistral (~4.4GB)...")
    print("       Ci vogliono ~2-3 minuti su Colab.")
    subprocess.run(["ollama", "pull", "dolphin-mistral"], check=True)

    # Esponi con ngrok (tunnel gratuito)
    print("[4/4] Creazione tunnel pubblico...")
    subprocess.run(
        "pip install pyngrok -q",
        shell=True,
        check=True,
    )

    from pyngrok import ngrok

    # Crea tunnel verso Ollama
    tunnel = ngrok.connect(11434)
    public_url = tunnel.public_url

    print("\n" + "=" * 50)
    print("FATTO! Ollama e' raggiungibile da:")
    print(f"\n  {public_url}\n")
    print("Sul telefono, modifica config.json:")
    print(f'  "ollama_url": "{public_url}"')
    print("=" * 50)
    print("\nLascia questo notebook APERTO finche' usi l'agente.")
    print("Il tunnel si chiude quando chiudi Colab.")

    return public_url


if __name__ == "__main__":
    print("Questo script va eseguito su Google Colab!")
    print("Vai su: https://colab.research.google.com")
    print("Crea un notebook e incolla il codice.")
