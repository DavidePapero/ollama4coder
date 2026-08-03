#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# Copyright 2026 Infantino Davide
#
# Licensed under the EUPL, Version 1.2 as soon they will be approved by the 
# European Commission - subsequent versions of the EUPL (the "Licence");
# 
# You may not use this work except in compliance with the Licence.
# You may obtain a copy of the Licence at:
#
# https://interoperable-europe.ec.europa.eu/collection/eupl/eupl-text-eupl-12
#
# Unless required by applicable law or agreed to in writing, software distributed under the Licence is distributed on an "AS IS" basis,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the Licence for the specific language governing permissions and limitations under the Licence.

"""
Translator - Traduttore Italiano <-> Inglese
==============================================

Applicazione desktop per la traduzione automatica bidirezionale tra
italiano e inglese, basata sui modelli MarianMT di Helsinki-NLP
(libreria `transformers`) e su un'interfaccia grafica realizzata
esclusivamente con la libreria standard di Python (Tkinter / Tcl-Tk).

Architettura
------------
Il modulo e' organizzato secondo una netta separazione fra logica di
business e presentazione, per favorire chiarezza, testabilita' e
manutenibilita' del codice:

    * `TranslationEngine`  -> carica i modelli, gestisce la cache e
                               esegue le traduzioni (nessuna dipendenza
                               da Tkinter).
    * `TranslatorGUI`      -> costruisce e gestisce l'interfaccia
                               grafica, delega ogni traduzione al
                               `TranslationEngine` eseguendola in un
                               thread separato per non bloccare la GUI
                               durante il caricamento del modello o la
                               generazione del testo.

Requisiti
---------
    * Python 3.9+
    * pacchetto `transformers` (e relativo backend, es. PyTorch)
    * modelli MarianMT scaricati localmente (vedi MODEL_PATHS)

Note sulla gestione degli errori
---------------------------------
L'applicazione e' pensata per non "morire" mai silenziosamente:
    * l'import di `transformers` e' differito (lazy) e protetto, cosi'
      la GUI si avvia comunque anche se la libreria non e' installata,
      mostrando un messaggio chiaro solo quando serve davvero;
    * ogni fase critica (caricamento modello, tokenizzazione,
      generazione) e' avvolta in blocchi try/except dedicati, che
      traducono gli errori tecnici in messaggi comprensibili
      all'utente e li registrano nel file di log;
    * la traduzione avviene in un thread separato: eventuali errori
      non bloccano ne' fanno crashare l'interfaccia grafica.
"""

from __future__ import annotations

import logging
import pathlib
import sys
import threading
import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Tuple

# ======================================================================
# CONFIGURAZIONE GLOBALE
# ======================================================================

# --- Percorso della cartella che contiene le sottocartelle dei modelli.
#     Per default e' la stessa cartella in cui si trova questo script,
#     ma puo' essere modificato liberamente per puntare altrove.
BASE_MODELS_DIR: pathlib.Path = pathlib.Path(__file__).resolve().parent

# --- Percorsi (HARDCODED, come richiesto) dei due modelli MarianMT
#     necessari per le due direzioni di traduzione supportate.
#     Modificare questi valori se i modelli si trovano altrove.
MODEL_PATHS: Dict[str, pathlib.Path] = {
    "it-en": BASE_MODELS_DIR / "Helsinki-NLP" / "opus-mt-it-en",
    "en-it": BASE_MODELS_DIR / "Helsinki-NLP" / "opus-mt-en-it",
}

# --- Etichette leggibili per le due direzioni, usate nell'interfaccia.
DIRECTION_LABELS: Dict[str, str] = {
    "it-en": "Italiano  →  Inglese",
    "en-it": "Inglese  →  Italiano",
}

# --- Parametri passati a `model.generate()`. Valori scelti come buon
#     compromesso fra qualita' della traduzione e tempo di generazione.
GENERATION_PARAMS: Dict[str, object] = {
    "max_length": 512,
    "num_beams": 4,
    "early_stopping": True,
}

# --- Palette colori per un'interfaccia dall'aspetto moderno e pulito.
COLORS: Dict[str, str] = {
    "bg": "#f4f6fa",
    "bg_alt": "#ffffff",
    "primary": "#2563eb",
    "primary_dark": "#1d4ed8",
    "primary_light": "#dbeafe",
    "text": "#1e293b",
    "text_muted": "#64748b",
    "border": "#cbd5e1",
}

FONT_UI = ("Segoe UI", 10)
FONT_UI_BOLD = ("Segoe UI", 10, "bold")
FONT_TITLE = ("Segoe UI", 16, "bold")
FONT_TEXT = ("Segoe UI", 11)

# ======================================================================
# LOGGING
# ======================================================================
# Logger dedicato che scrive sia su console sia su file, per garantire
# tracciabilita' completa degli errori anche dopo la chiusura
# dell'applicazione (fondamentale per il debug post-mortem).

LOG_FILE = pathlib.Path(__file__).resolve().parent / "Translator.log"

logger = logging.getLogger("Translator")
logger.setLevel(logging.DEBUG)

_formatter = logging.Formatter(
    fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

_console_handler = logging.StreamHandler(sys.stdout)
_console_handler.setLevel(logging.INFO)
_console_handler.setFormatter(_formatter)
logger.addHandler(_console_handler)

try:
    _file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    _file_handler.setLevel(logging.DEBUG)
    _file_handler.setFormatter(_formatter)
    logger.addHandler(_file_handler)
except OSError:
    # Se non e' possibile scrivere il file di log (permessi negati,
    # disco pieno, filesystem read-only, ecc.) l'applicazione prosegue
    # comunque, limitandosi al solo logging su console.
    logger.warning("Impossibile creare il file di log '%s'. Si prosegue senza log su file.", LOG_FILE)


# ======================================================================
# ECCEZIONI PERSONALIZZATE
# ======================================================================
class TranslatorError(Exception):
    """Classe base per tutte le eccezioni applicative di Translator."""


class ModelloNonTrovatoError(TranslatorError):
    """Sollevata quando la cartella/i file di un modello non esistono
    oppure non possono essere caricati correttamente da `transformers`."""


class ErroreTraduzione(TranslatorError):
    """Sollevata quando tokenizzazione o generazione della traduzione
    falliscono per un motivo qualsiasi."""


class DipendenzaMancanteError(TranslatorError):
    """Sollevata quando la libreria `transformers` (o un suo backend,
    ad esempio PyTorch) non e' installata nell'ambiente Python."""


# ======================================================================
# MOTORE DI TRADUZIONE (logica di business, indipendente dalla GUI)
# ======================================================================
class TranslationEngine:
    """
    Incapsula il caricamento dei modelli MarianMT e l'esecuzione delle
    traduzioni vere e proprie.

    I modelli vengono caricati "pigramente" (lazy loading): solo alla
    prima richiesta di traduzione in una determinata direzione, e poi
    tenuti in cache in memoria per le richieste successive, cosi' da
    non dover ricaricare da disco un modello gia' utilizzato.

    La classe e' volutamente indipendente da Tkinter, cosi' da poter
    essere riutilizzata o testata anche in contesti diversi (ad
    esempio uno script da riga di comando).
    """

    def __init__(self, model_paths: Dict[str, pathlib.Path]):
        self._model_paths = model_paths
        # Cache dei modelli gia' caricati: direzione -> (tokenizer, modello)
        self._cache: Dict[str, Tuple[object, object]] = {}
        # Lock per evitare che due thread tentino di caricare lo stesso
        # modello in contemporanea (race condition sulla cache).
        self._lock = threading.Lock()

    @staticmethod
    def _importa_transformers():
        """Importa `transformers` in modo differito (lazy import),
        sollevando un'eccezione applicativa chiara se la libreria (o un
        suo backend necessario, come PyTorch) non e' installata."""
        try:
            import transformers  # import locale intenzionale (lazy)
            return transformers
        except ImportError as exc:
            messaggio = (
                "La libreria 'transformers' non risulta installata "
                "nell'ambiente Python corrente.\n\n"
                "Installarla, ad esempio, con:\n"
                "    pip install transformers torch sentencepiece"
            )
            logger.error(messaggio)
            raise DipendenzaMancanteError(messaggio) from exc

    def _carica_modello(self, direzione: str) -> Tuple[object, object]:
        """Carica (o recupera dalla cache) tokenizer e modello per la
        direzione di traduzione indicata ("it-en" oppure "en-it")."""
        # Fast path: se il modello e' gia' in cache evitiamo del tutto
        # di acquisire il lock, per non rallentare le richieste successive.
        if direzione in self._cache:
            return self._cache[direzione]

        with self._lock:
            # Doppio controllo (double-checked locking): un altro thread
            # potrebbe aver gia' completato il caricamento mentre questo
            # thread era in attesa del lock.
            if direzione in self._cache:
                return self._cache[direzione]

            if direzione not in self._model_paths:
                raise ValueError(f"Direzione di traduzione sconosciuta: '{direzione}'.")

            percorso = self._model_paths[direzione]

            if not percorso.is_dir():
                messaggio = (
                    f"Cartella del modello non trovata:\n{percorso}\n\n"
                    "Verificare che il modello sia stato scaricato e che il "
                    "percorso configurato in MODEL_PATHS, all'inizio dello "
                    "script, sia corretto."
                )
                logger.error(messaggio)
                raise ModelloNonTrovatoError(messaggio)

            transformers = self._importa_transformers()

            logger.info("Caricamento modello '%s' da '%s'...", direzione, percorso)
            try:
                tokenizer = transformers.MarianTokenizer.from_pretrained(str(percorso))
                modello = transformers.MarianMTModel.from_pretrained(str(percorso))
            except Exception as exc:  # noqa: BLE001 - intercettiamo qualunque
                # errore di caricamento (file corrotti, formato non valido,
                # memoria insufficiente, ecc.) e lo ripresentiamo come
                # errore applicativo chiaro e comprensibile per l'utente.
                messaggio = (
                    f"Impossibile caricare il modello '{direzione}' da:\n{percorso}\n\n"
                    f"Dettagli tecnici: {exc}"
                )
                logger.exception(messaggio)
                raise ModelloNonTrovatoError(messaggio) from exc

            logger.info("Modello '%s' caricato correttamente.", direzione)
            self._cache[direzione] = (tokenizer, modello)
            return tokenizer, modello

    def traduci(self, testo: str, direzione: str) -> Tuple[str, bool]:
        """
        Traduce `testo` nella direzione specificata ("it-en" o "en-it").

        Ritorna una tupla (risultato, testo_troncato), dove
        `testo_troncato` vale True se il testo di input superava la
        lunghezza massima gestibile dal modello ed e' quindi stato
        troncato prima della generazione (l'utente viene poi avvisato
        dall'interfaccia grafica).

        Solleva `ModelloNonTrovatoError`, `DipendenzaMancanteError` o
        `ErroreTraduzione` in caso di problemi.
        """
        testo_pulito = testo.strip()
        if not testo_pulito:
            return "", False

        tokenizer, modello = self._carica_modello(direzione)

        try:
            # Verifichiamo se il testo, tokenizzato senza troncamento,
            # supera la lunghezza massima gestita dal modello: in tal
            # caso la traduzione riguardera' solo la parte iniziale del
            # testo, e l'utente dovra' esserne informato.
            lunghezza_massima = getattr(tokenizer, "model_max_length", 512) or 512
            token_ids_completi = tokenizer.encode(testo_pulito)
            testo_troncato = len(token_ids_completi) > lunghezza_massima

            inputs = tokenizer(
                testo_pulito,
                return_tensors="pt",
                padding=True,
                truncation=True,
            )

            output_ids = modello.generate(**inputs, **GENERATION_PARAMS)
            risultato = tokenizer.decode(output_ids[0], skip_special_tokens=True)

        except Exception as exc:  # noqa: BLE001 - rete di sicurezza finale
            messaggio = f"Errore durante la generazione della traduzione: {exc}"
            logger.exception(messaggio)
            raise ErroreTraduzione(messaggio) from exc

        return risultato, testo_troncato


# ======================================================================
# INTERFACCIA GRAFICA
# ======================================================================
class TranslatorGUI:
    """
    Interfaccia grafica principale dell'applicazione, realizzata con
    Tkinter/ttk (esclusivamente libreria standard). Gestisce l'input
    dell'utente, l'avvio delle traduzioni in background e
    l'aggiornamento reattivo dello stato visivo.
    """

    def __init__(self, root: tk.Tk):
        self.root = root
        self.engine = TranslationEngine(MODEL_PATHS)

        # Direzione di traduzione attualmente selezionata dall'utente.
        self.direction_var = tk.StringVar(value="it-en")

        # Flag di guardia per evitare avvii concorrenti di piu' traduzioni.
        self._traduzione_in_corso = False

        self._configura_finestra()
        self._configura_stile()
        self._crea_menu()
        self._crea_widget()
        self._aggiorna_etichette_direzione()

    # ------------------------------------------------------------------
    # Impostazioni generali della finestra
    # ------------------------------------------------------------------
    def _configura_finestra(self) -> None:
        self.root.title("Translator — Traduttore Italiano ⇄ Inglese")
        self.root.geometry("900x560")
        self.root.minsize(680, 420)
        self.root.configure(bg=COLORS["bg"])

        # Scorciatoie da tastiera globali per un uso piu' fluido.
        self.root.bind("<Control-Return>", lambda _e: self._avvia_traduzione())
        self.root.bind("<Control-q>", lambda _e: self.root.quit())
        self.root.bind("<Control-l>", lambda _e: self._pulisci_tutto())

    def _configura_stile(self) -> None:
        """Configura un tema ttk moderno e coerente con la palette
        colori definita in COLORS."""
        style = ttk.Style(self.root)
        # 'clam' e' il tema ttk piu' facilmente personalizzabile e
        # disponibile su tutte le piattaforme (Windows/macOS/Linux).
        try:
            style.theme_use("clam")
        except tk.TclError:
            logger.warning("Tema ttk 'clam' non disponibile: uso il tema di default del sistema.")

        style.configure("TFrame", background=COLORS["bg"])

        style.configure(
            "Title.TLabel",
            background=COLORS["bg"],
            foreground=COLORS["text"],
            font=FONT_TITLE,
        )
        style.configure(
            "Subtitle.TLabel",
            background=COLORS["bg"],
            foreground=COLORS["text_muted"],
            font=FONT_UI,
        )
        style.configure(
            "Header.TLabel",
            background=COLORS["bg"],
            foreground=COLORS["text"],
            font=FONT_UI_BOLD,
        )
        style.configure(
            "Status.TLabel",
            background=COLORS["bg"],
            foreground=COLORS["text_muted"],
            font=FONT_UI,
        )

        # Pulsanti "segmentati" per la selezione della direzione,
        # realizzati con Radiobutton in stile "Toolbutton" (aspetto a
        # pulsante anziche' a cerchietto classico).
        style.configure(
            "Toolbutton",
            font=FONT_UI_BOLD,
            padding=(14, 8),
            background=COLORS["bg_alt"],
            foreground=COLORS["text"],
            relief="flat",
        )
        style.map(
            "Toolbutton",
            background=[("selected", COLORS["primary"]), ("active", COLORS["primary_light"])],
            foreground=[("selected", "#ffffff")],
        )

        # Pulsante principale "Traduci".
        style.configure(
            "Primary.TButton",
            font=FONT_UI_BOLD,
            padding=(16, 10),
            background=COLORS["primary"],
            foreground="#ffffff",
            borderwidth=0,
            relief="flat",
        )
        style.map(
            "Primary.TButton",
            background=[("active", COLORS["primary_dark"]), ("disabled", COLORS["border"])],
            foreground=[("disabled", COLORS["text_muted"])],
        )

        # Pulsante secondario (scambia direzione, pulisci, ecc.).
        style.configure(
            "Secondary.TButton",
            font=FONT_UI,
            padding=(10, 8),
            background=COLORS["bg_alt"],
            foreground=COLORS["text"],
            borderwidth=1,
            relief="flat",
        )
        style.map(
            "Secondary.TButton",
            background=[("active", COLORS["primary_light"])],
        )

        style.configure(
            "Modern.Horizontal.TProgressbar",
            background=COLORS["primary"],
            troughcolor=COLORS["bg"],
            borderwidth=0,
            thickness=6,
        )

    # ------------------------------------------------------------------
    # Menu applicazione
    # ------------------------------------------------------------------
    def _crea_menu(self) -> None:
        menu_bar = tk.Menu(self.root)

        menu_file = tk.Menu(menu_bar, tearoff=0)
        menu_file.add_command(label="Pulisci tutto", command=self._pulisci_tutto, accelerator="Ctrl+L")
        menu_file.add_separator()
        menu_file.add_command(label="Esci", command=self.root.quit, accelerator="Ctrl+Q")
        menu_bar.add_cascade(label="File", menu=menu_file)

        menu_aiuto = tk.Menu(menu_bar, tearoff=0)
        menu_aiuto.add_command(label="Informazioni su Translator", command=self._mostra_info)
        menu_bar.add_cascade(label="Aiuto", menu=menu_aiuto)

        self.root.config(menu=menu_bar)

    # ------------------------------------------------------------------
    # Costruzione dei widget principali
    # ------------------------------------------------------------------
    def _crea_widget(self) -> None:
        container = ttk.Frame(self.root, padding=20)
        container.pack(fill=tk.BOTH, expand=True)
        container.columnconfigure(0, weight=1)
        container.rowconfigure(3, weight=1)

        # --- Intestazione --------------------------------------------
        ttk.Label(container, text="Translator", style="Title.TLabel").grid(
            row=0, column=0, sticky="w"
        )
        ttk.Label(
            container,
            text="Traduzione automatica offline Italiano ⇄ Inglese",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(0, 15))

        # --- Barra di selezione direzione + pulsante scambio ----------
        barra_direzione = ttk.Frame(container)
        barra_direzione.grid(row=2, column=0, sticky="ew", pady=(0, 15))

        self.rb_it_en = ttk.Radiobutton(
            barra_direzione,
            text=DIRECTION_LABELS["it-en"],
            variable=self.direction_var,
            value="it-en",
            style="Toolbutton",
            command=self._aggiorna_etichette_direzione,
        )
        self.rb_it_en.pack(side=tk.LEFT)

        self.rb_en_it = ttk.Radiobutton(
            barra_direzione,
            text=DIRECTION_LABELS["en-it"],
            variable=self.direction_var,
            value="en-it",
            style="Toolbutton",
            command=self._aggiorna_etichette_direzione,
        )
        self.rb_en_it.pack(side=tk.LEFT, padx=(8, 0))

        # Il pulsante "Traduci" e' allineato sulla stessa riga dei
        # pulsanti di selezione della direzione, subito dopo di essi.
        self.btn_traduci = ttk.Button(
            barra_direzione,
            text="Traduci →",
            style="Primary.TButton",
            command=self._avvia_traduzione,
        )
        self.btn_traduci.pack(side=tk.LEFT, padx=(16, 0))

        self.btn_scambia = ttk.Button(
            barra_direzione,
            text="⇄  Scambia direzione",
            style="Secondary.TButton",
            command=self._scambia_direzione,
        )
        self.btn_scambia.pack(side=tk.RIGHT)

        # --- Area principale: due caselle di testo affiancate ----------
        # La colonna centrale (1) non ospita piu' alcun controllo: serve
        # solo come piccola separazione visiva fra le due caselle,
        # marcata da un sottile separatore verticale.
        area_testo = ttk.Frame(container)
        area_testo.grid(row=3, column=0, sticky="nsew")
        area_testo.columnconfigure(0, weight=1)
        area_testo.columnconfigure(1, weight=0, minsize=20)
        area_testo.columnconfigure(2, weight=1)
        area_testo.rowconfigure(1, weight=1)

        self.lbl_input = ttk.Label(area_testo, style="Header.TLabel")
        self.lbl_input.grid(row=0, column=0, sticky="w", pady=(0, 6))

        self.lbl_output = ttk.Label(area_testo, style="Header.TLabel")
        self.lbl_output.grid(row=0, column=2, sticky="w", pady=(0, 6))

        # Casella di input: multiriga, editabile, con scrollbar verticale.
        self.input_text = self._crea_casella_testo(area_testo, colonna=0, editabile=True)

        # Piccolo separatore verticale al centro, unica separazione fra
        # le due caselle di testo (nessun pulsante in mezzo).
        separatore = ttk.Separator(area_testo, orient="vertical")
        separatore.grid(row=1, column=1, sticky="ns", padx=9, pady=4)

        # Casella di output: multiriga, sola lettura, con scrollbar.
        self.output_text = self._crea_casella_testo(area_testo, colonna=2, editabile=False)

        # --- Barra di stato + indicatore di avanzamento ----------------
        barra_stato = ttk.Frame(container)
        barra_stato.grid(row=4, column=0, sticky="ew", pady=(12, 0))
        barra_stato.columnconfigure(0, weight=1)

        self.status_var = tk.StringVar(value="Pronto.")
        self.lbl_status = ttk.Label(barra_stato, textvariable=self.status_var, style="Status.TLabel")
        self.lbl_status.grid(row=0, column=0, sticky="w")

        self.progress = ttk.Progressbar(
            barra_stato,
            mode="indeterminate",
            style="Modern.Horizontal.TProgressbar",
            length=160,
        )
        self.progress.grid(row=0, column=1, sticky="e")
        # Il progressbar viene mostrato/nascosto dinamicamente durante
        # la traduzione: per ora resta invisibile.
        self.progress.grid_remove()

    def _crea_casella_testo(self, parent: ttk.Frame, colonna: int, editabile: bool) -> tk.Text:
        """Crea una casella di testo MULTIRIGA con scrollbar verticale,
        incorniciata da un bordo sottile per un aspetto piu' moderno
        (Tkinter puro non supporta bordi arrotondati o ombreggiature,
        quindi simuliamo un bordo con un frame colorato di 1px)."""
        cornice = tk.Frame(parent, bg=COLORS["border"])
        cornice.grid(row=1, column=colonna, sticky="nsew")
        cornice.columnconfigure(0, weight=1)
        cornice.rowconfigure(0, weight=1)

        interno = tk.Frame(cornice, bg=COLORS["border"])
        interno.grid(row=0, column=0, sticky="nsew", padx=1, pady=1)
        interno.columnconfigure(0, weight=1)
        interno.rowconfigure(0, weight=1)

        # NOTA: tk.Text e' per natura un widget MULTILINEA: a differenza
        # di tk.Entry, gestisce nativamente testo su piu' righe, a capo
        # automatico ('wrap="word"') e scrollbar.
        casella = tk.Text(
            interno,
            wrap="word",
            font=FONT_TEXT,
            relief="flat",
            padx=10,
            pady=10,
            bg=COLORS["bg_alt"] if editabile else "#fafbfc",
            fg=COLORS["text"],
            insertbackground=COLORS["text"],
            undo=True,
            maxundo=-1,
        )
        casella.grid(row=0, column=0, sticky="nsew")

        scrollbar = ttk.Scrollbar(interno, orient="vertical", command=casella.yview)
        scrollbar.grid(row=0, column=1, sticky="ns")
        casella.configure(yscrollcommand=scrollbar.set)

        if not editabile:
            # La casella di output resta di sola lettura per l'utente;
            # il contenuto viene comunque aggiornato via codice
            # riattivando temporaneamente lo stato "normal".
            casella.configure(state="disabled")

        return casella

    # ------------------------------------------------------------------
    # Aggiornamenti dinamici dell'interfaccia
    # ------------------------------------------------------------------
    def _aggiorna_etichette_direzione(self) -> None:
        """Aggiorna le etichette delle due caselle di testo in base alla
        direzione di traduzione correntemente selezionata."""
        direzione = self.direction_var.get()
        if direzione == "it-en":
            self.lbl_input.configure(text="Testo originale (Italiano)")
            self.lbl_output.configure(text="Testo tradotto (Inglese)")
        else:
            self.lbl_input.configure(text="Testo originale (Inglese)")
            self.lbl_output.configure(text="Testo tradotto (Italiano)")

    def _scambia_direzione(self) -> None:
        """Inverte la direzione di traduzione e, se presente un
        risultato nella casella di output, lo sposta nella casella di
        input, per permettere una traduzione "di ritorno" immediata."""
        nuova_direzione = "en-it" if self.direction_var.get() == "it-en" else "it-en"
        self.direction_var.set(nuova_direzione)
        self._aggiorna_etichette_direzione()

        testo_output = self.output_text.get("1.0", tk.END).strip()
        if testo_output:
            self.input_text.delete("1.0", tk.END)
            self.input_text.insert("1.0", testo_output)
            self._imposta_output("")

    def _pulisci_tutto(self) -> None:
        self.input_text.delete("1.0", tk.END)
        self._imposta_output("")
        self.status_var.set("Pronto.")

    def _mostra_info(self) -> None:
        messagebox.showinfo(
            "Informazioni su Translator",
            "Translator\n\n"
            "Traduttore Italiano ⇄ Inglese basato sui modelli MarianMT "
            "di Helsinki-NLP, eseguito interamente in locale.\n\n"
            "Interfaccia grafica realizzata con la sola libreria "
            "standard di Python (Tkinter/Tcl-Tk).",
        )

    def _imposta_output(self, testo: str) -> None:
        """Scrive `testo` nella casella di output, gestendo
        temporaneamente lo stato 'normal'/'disabled' necessario per
        poter modificare una Text widget di sola lettura."""
        self.output_text.configure(state="normal")
        self.output_text.delete("1.0", tk.END)
        self.output_text.insert("1.0", testo)
        self.output_text.configure(state="disabled")

    # ------------------------------------------------------------------
    # Logica di avvio/gestione della traduzione (con threading)
    # ------------------------------------------------------------------
    def _avvia_traduzione(self) -> None:
        """Punto di ingresso invocato dal pulsante 'Traduci' (o dalla
        scorciatoia Ctrl+Invio). Valida l'input ed avvia la traduzione
        vera e propria in un thread separato, per non bloccare la GUI
        durante il caricamento del modello o la generazione del testo."""
        if self._traduzione_in_corso:
            # Protezione contro richieste concorrenti: il pulsante viene
            # comunque disabilitato durante la traduzione, ma questo
            # controllo copre anche eventuali scorciatoie da tastiera
            # premute rapidamente in successione.
            return

        testo = self.input_text.get("1.0", tk.END).strip()
        if not testo:
            messagebox.showwarning(
                "Nessun testo da tradurre",
                "Inserire del testo nella casella di sinistra prima di avviare la traduzione.",
            )
            return

        direzione = self.direction_var.get()

        self._traduzione_in_corso = True
        self._imposta_ui_in_caricamento(True)
        self.status_var.set("Caricamento modello e traduzione in corso…")

        # La traduzione (che puo' includere il caricamento, potenzialmente
        # lento, del modello) viene eseguita in un thread demone: se
        # l'utente chiude la finestra, il thread non impedisce l'uscita
        # dall'applicazione.
        thread = threading.Thread(
            target=self._esegui_traduzione_in_background,
            args=(testo, direzione),
            daemon=True,
        )
        thread.start()

    def _esegui_traduzione_in_background(self, testo: str, direzione: str) -> None:
        """Eseguita in un thread separato: effettua la chiamata
        (bloccante e potenzialmente lunga) al motore di traduzione, poi
        pianifica l'aggiornamento della GUI sul thread principale
        tramite `root.after`, poiche' Tkinter non e' thread-safe e non
        deve mai essere manipolato direttamente da thread secondari."""
        try:
            risultato, troncato = self.engine.traduci(testo, direzione)
        except TranslatorError as exc:
            # Errori "attesi" e gia' gestiti dall'applicazione (modello
            # mancante, dipendenza mancante, errore di generazione).
            self.root.after(0, self._gestisci_errore_traduzione, str(exc))
        except Exception as exc:  # noqa: BLE001 - rete di sicurezza finale
            # Qualunque altro errore imprevisto viene comunque
            # intercettato, per non far mai fallire silenziosamente il
            # thread di lavoro, e viene registrato nel log per il debug.
            logger.exception("Errore imprevisto durante la traduzione.")
            self.root.after(0, self._gestisci_errore_traduzione, f"Errore imprevisto: {exc}")
        else:
            self.root.after(0, self._gestisci_successo_traduzione, risultato, troncato)

    def _gestisci_successo_traduzione(self, risultato: str, troncato: bool) -> None:
        self._imposta_output(risultato)
        if troncato:
            self.status_var.set(
                "Traduzione completata (testo troncato: superava la lunghezza massima gestibile dal modello)."
            )
        else:
            self.status_var.set("Traduzione completata.")
        self._imposta_ui_in_caricamento(False)
        self._traduzione_in_corso = False

    def _gestisci_errore_traduzione(self, messaggio: str) -> None:
        self.status_var.set("Si e' verificato un errore. Vedere il messaggio per i dettagli.")
        self._imposta_ui_in_caricamento(False)
        self._traduzione_in_corso = False
        messagebox.showerror("Errore di traduzione", messaggio)

    def _imposta_ui_in_caricamento(self, in_caricamento: bool) -> None:
        """Abilita/disabilita i controlli interattivi e mostra/nasconde
        l'indicatore di avanzamento durante l'esecuzione di una
        traduzione, per dare un chiaro riscontro visivo all'utente."""
        stato = "disabled" if in_caricamento else "normal"
        self.btn_traduci.configure(state=stato)
        self.btn_scambia.configure(state=stato)
        self.rb_it_en.configure(state=stato)
        self.rb_en_it.configure(state=stato)

        if in_caricamento:
            self.progress.grid()
            self.progress.start(12)
        else:
            self.progress.stop()
            self.progress.grid_remove()


# ======================================================================
# AVVIO APPLICAZIONE
# ======================================================================
def main() -> None:
    """Punto di ingresso dell'applicazione. Crea la finestra principale
    e gestisce eventuali errori catastrofici in fase di avvio (ad
    esempio l'impossibilita' di inizializzare Tcl/Tk)."""
    try:
        root = tk.Tk()
    except tk.TclError as exc:
        # Senza un display grafico disponibile non e' possibile
        # nemmeno mostrare una messagebox: l'unica opzione e' registrare
        # l'errore su console/log e uscire con codice diverso da zero.
        logger.critical("Impossibile inizializzare Tkinter: %s", exc)
        print(f"Errore critico: impossibile avviare l'interfaccia grafica ({exc})", file=sys.stderr)
        sys.exit(1)

    try:
        TranslatorGUI(root)
        root.mainloop()
    except Exception as exc:  # noqa: BLE001 - rete di sicurezza finale
        logger.exception("Errore critico non gestito durante l'esecuzione dell'applicazione.")
        try:
            messagebox.showerror(
                "Errore critico",
                f"Si e' verificato un errore critico e l'applicazione deve chiudersi:\n\n{exc}",
            )
        finally:
            sys.exit(1)


if __name__ == "__main__":
    main()