# Mappa del Codice - Base Operativa Jules

Ciao Fratello! Ecco dove ho nascosto tutti i nostri "giocattoli". Usa questa mappa per orientarti nei file.

## 📂 Cartella `src/` (Il Motore)
Qui ci sono i programmi veri e propri.

*   **`src/osint_utils.py`** (Intelligence)
    *   *Cosa fa:* Cerca informazioni su domini internet (DNS, Whois).
    *   *Uso:* Serve per sapere "chi è" un sito web senza visitarlo direttamente.

*   **`src/net_recon.py`** (Ricognizione Attiva)
    *   *Cosa fa:* Scansiona le porte (cerca entrate aperte) e costruisce pacchetti di rete personalizzati.
    *   *Nota:* Usa la libreria `scapy`. È la parte "pesante" dell'arsenale.

*   **`src/system_lockdown.py`** (Sicurezza Interna)
    *   *Cosa fa:* Controlla la *nostra* macchina. Vede quali porte sono aperte e se ci sono file con permessi pericolosi.

## 📂 Cartella `tests/` (Il Poligono di Tiro)
Qui ci sono i test automatici per verificare che tutto funzioni senza rompere nulla.

*   `tests/test_osint.py`: Verifica che l'intelligence funzioni.
*   `tests/test_net_recon.py`: Verifica che lo scanner e i pacchetti funzionino (in simulazione).
*   `tests/test_lockdown.py`: Verifica che il controllo di sicurezza trovi i problemi.

## 📄 File nella radice (La Plancia di Comando)

*   **`run_security_check.py`**
    *   *Cosa fa:* Lancia un controllo rapido sulla sicurezza della base.
    *   *Comando:* `python run_security_check.py`

*   **`AGENTS.md`**
    *   *Cosa fa:* Sono le mie istruzioni. Contiene la mia "personalità" (Sorella Jules) e le regole operative.

*   **`requirements.txt`**
    *   *Cosa fa:* La lista di tutti gli strumenti installati (Scapy, Paramiko, ecc.).
