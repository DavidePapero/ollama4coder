# Guida Completa: 
## Configurazione Ambiente Python e Download di Modelli Hugging Face in Directory Locali

Questa guida spiega passo per passo come impostare un ambiente virtuale isolato in Python, installare gli strumenti ufficiali di **Hugging Face** (`huggingface_hub` e `transformers`) e scaricare modelli di intelligenza artificiale direttamente all'interno di una cartella specifica sul tuo filesystem locale.

---

## Indice

1. [Prerequisiti di Sistema](#1-prerequisiti-di-sistema)
2. [Creazione e Attivazione dell'Ambiente Virtuale](#2-creazione-e-attivazione-dellambiente-virtuale)
   - [Metodo Standard (venv)](#metodo-standard-venv)
   - [Metodo Alternativo (Conda)](#metodo-alternativo-conda)
3. [Installazione delle Librerie Hugging Face](#3-installazione-delle-librerie-hugging-face)
4. [Autenticazione per Modelli Protetti (Gated Models)](#4-autenticazione-per-modelli-protetti-gated-models)
5. [Download di un Modello in un Path Specifico](#5-download-di-un-modello-in-un-path-specifico)
   - [Metodo 1: Interfaccia a Riga di Comando (CLI)](#metodo-1-interfaccia-a-riga-di-comando-cli)
   - [Metodo 2: Script Python con `snapshot_download`](#metodo-2-script-python-con-snapshot_download)
   - [Metodo 3: Download di Singoli File (`hf_hub_download`)](#metodo-3-download-di-singoli-file-hf_hub_download)
   - [Metodo 4: Uso Diretto con `transformers`](#metodo-4-uso-diretto-con-transformers)
6. [Gestione della Cache e dei Symlink](#6-gestione-della-cache-e-dei-symlink)
7. [Ottimizzazione della Velocità di Download (`hf_transfer`)](#7-ottimizzazione-della-velocità-di-download-hf_transfer)
8. [Risoluzione dei Problemi Comuni (Troubleshooting)](#8-risoluzione-dei-problemi-comuni-troubleshooting)

---

## 1. Prerequisiti di Sistema

Prima di iniziare, assicurati di avere installato:
- **Python 3.8 o superiore** (consigliato Python 3.10 / 3.11).
- **pip** aggiornato all'ultima versione disponibile.
- **Git** (opzionale ma utile se intendi usare strumenti legati ai repository Git LFS).

Verifica la tua versione di Python da terminale:
```bash
python --version
# oppure su Linux/macOS:
python3 --version
```

---

## 2. Creazione e Attivazione dell'Ambiente Virtuale

L'uso di un ambiente virtuale è essenziale per isolare le dipendenze del progetto ed evitare conflitti tra versioni di librerie diverse (ad esempio, versioni specifiche di `torch` o `transformers`).

### Metodo Standard (`venv`)

1. **Crea l'ambiente virtuale** (in questo esempio lo chiamiamo `.venv`):
   ```bash
   python -m venv .venv
   ```

2. **Attiva l'ambiente virtuale**:
   - **Linux / macOS**:
     ```bash
     source .venv/bin/activate
     ```
   - **Windows (Command Prompt - CMD)**:
     ```cmd
     .venv\Scripts Activate.bat
     ```
     
   - **Windows (PowerShell)**:
     ```powershell
     .venv\Scripts\Activate.ps1
     ```

   > *Nota per Windows PowerShell*: Se ricevi un errore sui criteri di esecuzione, esegui una volta il comando:  
   > `Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser`

3. **Aggiorna `pip` all'interno dell'ambiente attivato**:
   ```bash
   pip install --upgrade pip
   ```

---

### Metodo Alternativo (`Conda`)

Se preferisci utilizzare Miniconda o Anaconda:
```bash
# Creazione dell'ambiente specificando la versione di Python
conda create -n hf-env python=3.11 -y

# Attivazione dell'ambiente
conda activate hf-env
```

---

## 3. Installazione delle Librerie Hugging Face

Per scaricare e gestire i modelli, installeremo:
- `huggingface_hub`: la libreria core per interagire con l'Hub (incluso lo strumento di download e la CLI).
- `transformers`: la libreria principale per caricare ed eseguire modelli LLM e architetture supportate.
- `torch` (PyTorch): il backend di deep learning tipicamente richiesto per l'inferenza.

Esegui il comando:
```bash
pip install huggingface_hub transformers torch
```

Per sfruttare la nuova riga di comando con funzionalità complete (compresi gli helper per il trasferimento di file di grandi dimensioni), puoi installare `huggingface_hub` con il supporto CLI extra:
```bash
pip install "huggingface_hub[cli]"
```

---

## 4. Autenticazione per Modelli Protetti (Gated Models)

Molti modelli popolari (come **Meta-Llama-3**, **Mistral**, **Gemma**, ecc.) sono coperti da licenza specifica e richiedono un **Access Token** del tuo account Hugging Face per essere scaricati.

1. Registrati o accedi su [huggingface.co](https://huggingface.co/).
2. Accetta le condizioni sulla pagina del modello che intendi scaricare.
3. Genera un token da: **Settings** > **Access Tokens** > **New token** (con permessi di tipo *Read*).
4. Effettua il login da terminale nell'ambiente virtuale attivato:
   ```bash
   huggingface-cli login
   ```
   Incolla il token quando richiesto (non verrà mostrato a schermo per sicurezza).

In alternativa, puoi impostare il token tramite variabile d'ambiente:
```bash
# Linux / macOS
export HF_TOKEN="hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"

# Windows (PowerShell)
$env:HF_TOKEN="hf_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"
```

---

## 5. Download di un Modello in un Path Specifico

Per impostazione predefinita, Hugging Face salva i file in una cache globale (`~/.cache/huggingface/hub`). Quando specifichi una cartella di destinazione personalizzata tramite il parametro `local_dir`, i file del modello verranno archiviati direttamente in quella specifica directory.

---

### Metodo 1: Interfaccia a Riga di Comando (CLI)

Il metodo più immediato ed efficiente da terminale è utilizzare il comando `huggingface-cli download` con l'argomento `--local-dir`.

#### Esempio: scaricare un intero repository
```bash
huggingface-cli download Qwen/Qwen2.5-0.5B-Instruct --local-dir ./modelli/qwen2.5-0.5b
```

#### Esempio: scaricare solo determinati file (es. file GGUF o escludere file non desiderati)
Se desideri scaricare solo uno specifico formato di pesi (ad esempio i pesi in formato `.safetensors` o file `.gguf` per modelli quantizzati):

```bash
# Scarica solo i file safetensors e le configurazioni
huggingface-cli download Qwen/Qwen2.5-0.5B-Instruct   --include "*.safetensors" "*.json" "*.txt" "*.model"   --local-dir ./modelli/qwen2.5-0.5b
```

---

### Metodo 2: Script Python con `snapshot_download`

Se vuoi gestire il download in modo programmatico all'interno di uno script Python o di una pipeline automatizzata, utilizza la funzione `snapshot_download` dal modulo `huggingface_hub`.

Crea un file chiamato `download_model.py`:

```python
import os
from huggingface_hub import snapshot_download

# Identificativo del modello sull'Hub
REPO_ID = "Qwen/Qwen2.5-0.5B-Instruct"

# Path locale assoluto o relativo in cui salvare il modello
LOCAL_PATH = os.path.abspath("./modelli/qwen2.5-0.5b")

print(f"Avvio del download di '{REPO_ID}' in: -> {LOCAL_PATH}")

# Avvio del download
path_scaricato = snapshot_download(
    repo_id=REPO_ID,
    local_dir=LOCAL_PATH,
    # Opzionale: per scaricare i file direttamente nel path senza mantenere symlink alla cache centralizzata
    local_dir_use_symlinks=False,
    # Opzionale: lista dei file/estensioni da includere
    # allow_patterns=["*.safetensors", "*.json", "*.txt", "*.model"],
    # Opzionale: se il modello richiede autenticazione, passa un token o usa quello di default
    # token=True
)

print(f"Download completato con successo in: {path_scaricato}")
```

Esegui lo script:
```bash
python download_model.py
```

---

### Metodo 3: Download di Singoli File (`hf_hub_download`)

Se hai bisogno di scaricare un singolo file specifico da un repository (molto comune per i modelli in formato **GGUF** usati con `llama.cpp` o `ollama`):

```python
from huggingface_hub import hf_hub_download

repo_id = "TheBloke/Llama-2-7B-Chat-GGUF"
filename = "llama-2-7b-chat.Q4_K_M.gguf"
local_dir = "./modelli/gguf"

file_path = hf_hub_download(
    repo_id=repo_id,
    filename=filename,
    local_dir=local_dir,
    local_dir_use_symlinks=False
)

print(f"File salvato in: {file_path}")
```

---

### Metodo 4: Uso Diretto con `transformers`

Puoi scaricare e contemporaneamente caricare il modello nel tuo script specificando una directory di cache o scaricando prima nella directory locale per poi passarla a `.from_pretrained()`:

```python
from transformers import AutoTokenizer, AutoModelForCausalLM

LOCAL_DIR = "./modelli/qwen2.5-0.5b"

# 1. Caricamento del Tokenizer e del Modello dal path locale specificato
# (se il path locale contiene già i file scaricati tramite CLI o snapshot_download, 
# verrà evitato qualsiasi download di rete)
tokenizer = AutoTokenizer.from_pretrained(LOCAL_DIR)
model = AutoModelForCausalLM.from_pretrained(LOCAL_DIR)

print("Modello e tokenizer caricati correttamente dalla cartella locale!")
```

---

## 6. Gestione della Cache e dei Symlink

Quando usi il parametro `local_dir`, il comportamento predefinito di `huggingface_hub` dipende dalle opzioni di symlink:

1. **Comportamento Predefinito**:  
   I file vengono prima scaricati nella cache globale (`~/.cache/huggingface/hub`) per il deduplicamento e successivamente collegati tramite **symlink** (collegamento simbolico) nel percorso `local_dir`.
2. **Download Indipendente senza Symlink (`local_dir_use_symlinks=False`)**:  
   Se desideri che la tua cartella `local_dir` sia del tutto indipendente, portabile (ad esempio per essere archiviata su chiavetta USB o disco esterno) o se il tuo file system non supporta i symlink in modo nativo, aggiungi `--local-dir-use-symlinks False` dalla CLI oppure il parametro `local_dir_use_symlinks=False` in Python:

   ```bash
   huggingface-cli download Qwen/Qwen2.5-0.5B-Instruct      --local-dir ./modelli/qwen2.5-0.5b      --local-dir-use-symlinks False
   ```

---

## 7. Ottimizzazione della Velocità di Download (`hf_transfer`)

Per modelli di grandi dimensioni (decine di Gigabyte), puoi accelerare drasticamente la velocità di download abilitando la libreria ad alte prestazioni **`hf-transfer`**, basata su Rust.

1. **Installa `hf-transfer`**:
   ```bash
   pip install hf-transfer
   ```

2. **Abilita il trasferimento veloce prima dell'esecuzione**:
   - Da terminale:
     ```bash
     # Linux / macOS
     export HF_HUB_ENABLE_HF_TRANSFER=1
     huggingface-cli download ...
     
     # Windows (PowerShell)
     $env:HF_HUB_ENABLE_HF_TRANSFER="1"
     huggingface-cli download ...
     ```
   - All'interno dello script Python:
     ```python
     import os
     os.environ["HF_HUB_ENABLE_HF_TRANSFER"] = "1"
     from huggingface_hub import snapshot_download
     # ...
     ```

---

## 8. Risoluzione dei Problemi Comuni (Troubleshooting)

| Problema | Causa Probabile | Soluzione |
| :--- | :--- | :--- |
| **`401 Client Error: Unauthorized`** o **`403 Forbidden`** | Il modello richiede autenticazione o non hai accettato i termini di licenza sulla pagina del modello. | Esegui `huggingface-cli login`, inserisci il token con permessi di lettura ed accetta le condizioni sulla pagina web di HF. |
| **`OSError: [WinError 1314] A required privilege is not held by the client`** (Windows) | Windows richiede permessi di amministratore per creare link simbolici. | Attiva la modalità sviluppatore su Windows, oppure usa `--local-dir-use-symlinks False` per evitare l'uso di symlink. |
| **Spazio su disco esaurito nella partizione root (`/` o `C:\`)** | I file vengono prima scaricati nella cache in `~/.cache` prima di essere linkati. | Imposta la variabile d'ambiente `HF_HOME="/nuovo/path/cache"` verso un disco ad alta capacità, oppure usa `local_dir_use_symlinks=False`. |
| **Download lento o interrotto** | Connessione instabile con file molto grandi. | Installa e attiva `hf-transfer` come descritto nella sezione 7; il download di Hugging Face supporta nativamente il ripristino (resume) se rilanci il comando. |

---

## Riepilogo Rapido (Quickstart)

```bash
# 1. Crea e attiva l'ambiente
python -m venv .venv
source .venv/bin/activate  # su Windows: .venv\Scripts ctivate.bat

# 2. Installa le librerie necessarie
pip install huggingface_hub[cli] transformers torch

# 3. Scarica un modello nella cartella './modelli/my_model'
huggingface-cli download Qwen/Qwen2.5-0.5B-Instruct --local-dir
```