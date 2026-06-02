"""Copyright 2026 Infantino Davide

Redistribution and use in source and binary forms, with or without modification, are permitted provided that the following conditions are met:

1. Redistributions of source code must retain the above copyright notice, this list of conditions and the following disclaimer.

2. Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following disclaimer in the documentation and/or other materials provided with the distribution.

3. Neither the name of the copyright holder nor the names of its contributors may be used to endorse or promote products derived from this software without specific prior written permission.

THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS “AS IS” AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
"""
import datetime
import math
import os
import ast
import tokenize
import ollama

class HumanDiffTime:
    @staticmethod
    def from_seconds(total_seconds: int) -> str:
        """Trasforma secondi totali in una stringa HH:MM:SS."""

        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    @staticmethod
    def from_date(start_dt: datetime.datetime, end_dt: datetime.datetime) -> str:
        """Calcola la differenza tra due datetime e restituisce una stringa formattata HH:MM:SS."""
        total_seconds = int((end_dt - start_dt).total_seconds())
        return HumanDiffTime.from_seconds(total_seconds)

class OllamaForCoder:
    """Wrapper personalizzato per interagire con l'API locale di Ollama, 
    gestendo errori, parametri di campionamento e lettura del codice sorgente."""

    def __init__(self):
        # Parametri di default ottimizzati per l'analisi di codice (coding)
        self.default_options: dict = {}
        # Abilita il calcolo dinamico del contesto in base alla lunghezza del prompt
        self.force_context : bool = True
        # Rimuove eventuali commenti o linee vuote per ridurre la dimensione del prompt
        self.clean_codebase : bool = False
        # Abilita un'analisi più approfondita e dettagliata del codice, a scapito di tempi di risposta più lunghi
        self.think : bool = False
        # Definizione delle direttive di comportamento (System Prompt) 
        self.system_prompt  : str = 'You are an experienced programmer assistant. Provide only clean, commented code and briefly explain the logic. Be concise and specific in your analysis.'
        # Definizione delle direttive operative (User Request)
        self.request_prompt  : str = (
                "### Instructions\n"
                "When it makes sense, indicate the name of the file and the line of code where you found an issue or a suggestion. If you suggest code changes, provide the modified code snippet with line numbers and file names for clarity.\n"
                "1. Analyze the provided codebase and identify potential issues, bugs, or areas for improvement.\n"
                "2. Provide a concise summary of your findings, highlighting the most critical points.\n"
                "3. If possible, suggest specific code changes or best practices to address the identified issues.\n"
                "4. Focus on code quality, maintainability, and adherence to Python best practices.\n"
                "5. Provide clear explanations and actionable feedback that can be easily understood by developers.\n"
                "6. Add, edit, improve comments in the code if necessary."
        )
        self.set_default_options()
        # Stima di 3 caratteri per token, con blocchi di 1024 token
        self.context_divisor : float = 3.0
        # Posiziona le istruzioni operative dopo il codice sorgente per una migliore contestualizzazione (True) o prima (False)
        self.request_at_bottom : bool = True
        # In modalità summary, la risposta include solo i punti chiave e i metadati essenziali, mentre in modalità dettagliata viene restituita l'intera risposta generata dal modello senza ulteriori formattazioni.
        self.summary_mode : bool = True

    def set_request_at_bottom(self, enable: bool = True) -> None:
        """Determina se posizionare le istruzioni operative dopo il codice sorgente (True) o prima (False) per una migliore contestualizzazione."""
        self.request_at_bottom = enable

    def set_summary_mode(self, enable: bool = True) -> None:
        """Abilita o disabilita la modalità summary per restituire solo i punti chiave e i metadati essenziali."""
        self.summary_mode = enable

    def set_context_divisor(self, divisor: float) -> None:
        """Aggiorna il divisore usato per stimare la dimensione del contesto in base alla lunghezza del prompt."""
        self.context_divisor = divisor

    def set_system_prompt(self, prompt: str) -> None:
        """Aggiorna il prompt di sistema che definisce il comportamento generale dell'LLM."""
        self.system_prompt = prompt

    def set_request_prompt(self, prompt: str) -> None:
        """Aggiorna il prompt utente che specifica le istruzioni operative per l'LLM."""
        self.request_prompt = prompt

    def set_think(self, enable: bool = True) -> None:
        """Abilita o disabilita la modalità 'think' per un'analisi più approfondita."""
        self.think = enable

    def set_default_options(self, temperature: float = 0.2, top_p: float = 0.9, repeat_penalty: float = 1.1) -> None:
        """Aggiorna i parametri di campionamento di default per le chiamate successive.
        
            "temperature": 0.2,       # Molto bassa: riduce la creatività per risposte precise e logiche
            "top_p": 0.9,             # Esclude i token con probabilità complessiva inferiore al 10%
            "repeat_penalty": 1.1     # Penalizza la ripetizione frequente delle stesse parole o loop
        """
        self.default_options = {
            "temperature": temperature,
            "top_p": top_p,
            "repeat_penalty": repeat_penalty
        }

    def set_clean_codebase(self, enable: bool = True) -> None:
        """Enables or disables code cleaning (removing docstrings and comment)."""
        self.clean_codebase = enable

    def clean_code(self, code: str) -> str:
        """Parses and unparses code using AST to normalize formatting."""
        if not self.clean_codebase:
            return code
        tree = ast.parse(code)
        return ast.unparse(tree)

    def set_force_context(self, enable: bool = True) -> None:
        """Enables or disables forced context window calculation."""
        self.force_context = enable

    def set_options(self, **kwargs) -> None:
        """Permette di aggiornare dinamicamente i parametri di campionamento per le chiamate successive. Nessun controllo sui parametri, si assume che l'utente fornisca valori validi.

        Esempio di utilizzo:
        wrapper.set_options(temperature=0.5, top_p=0.95)
        """
        for key, value in kwargs.items():
            self.default_options[key] = value

    def list_models(self) -> ollama.ListResponse:
        """Richiede ad Ollama l'oggetto completo contenente tutti i modelli installati."""
        try:
            return ollama.list()
        except Exception as err:
            print(f"Errore durante il list dei modelli: {err}")
            return ollama.ListResponse(models=[])

    def list_names(self) -> list[str]:
        """Estrae ed elenca solo i nomi testuali dei modelli disponibili sul sistema."""
        try:
            # Cicla sulla lista di oggetti modello per recuperare la stringa identificativa .model
            return [modello.model for modello in self.list_models().models]
        except Exception as err:
            print(f"Errore nel recupero dei nomi dei modelli: {err}")
        return []

    def update_models(self) -> None:
        """Scorre tutti i modelli locali scaricati ed esegue il pull per aggiornarli all'ultima versione."""
        for model in self.list_names():
            self.pull_model(model)

    def pull_model(self, model_name: str) -> None:
        """
        Scarica o aggiorna un modello specifico mostrando l'avanzamento sul terminale.
        
        Parametri:
        - modello: Nome del modello da scaricare (es. 'codegemma:7b').
        """
        try:
            old_digest = ''
            # Abilita stream=True per ricevere aggiornamenti progressivi del download
            response = ollama.pull(model_name, stream=True)
            for chunk in response:
                digest = chunk.get('digest', '')
                # Se il digest cambia, notifica l'inizio del download del nuovo livello (layer)
                if digest and digest != old_digest:
                    print(f"\nPulling {model_name} - digest: {digest}", flush=True)
                    old_digest = digest

                # Sovrascrive la stessa riga sul terminale con lo stato corrente (\r)
                status = chunk.get('status', '')
                print(f"{status}", end='\r', flush=True)
            print(f"\nPull of {model_name} completed.")
        except Exception as err:
            print(f"Error pulling model {model_name}: {err}")

    def clean_python_code(self, source_code: str) -> str:
        """Rimuove docstring e commenti da un file Python, restituendo il codice pulito."""

        class DocstringRemover(ast.NodeTransformer):
            def _remove_docstring(self, node):
                """
                Rimuove la docstring se è la prima istruzione del corpo.
                Funziona per moduli, classi, funzioni e metodi.
                """
                if (
                    node.body
                    and isinstance(node.body[0], ast.Expr)
                    and isinstance(node.body[0].value, ast.Constant)
                    and isinstance(node.body[0].value.value, str)
                ):
                    node.body.pop(0)
                return node
            def visit_Module(self, node):
                self.generic_visit(node)
                return self._remove_docstring(node)
            def visit_ClassDef(self, node):
                self.generic_visit(node)
                return self._remove_docstring(node)
            def visit_FunctionDef(self, node):
                self.generic_visit(node)
                return self._remove_docstring(node)
            def visit_AsyncFunctionDef(self, node):
                self.generic_visit(node)
                return self._remove_docstring(node)

        # remove_comments_and_docstrings(source_code):
        tree = ast.parse(source_code)
        transformer = DocstringRemover()
        tree = transformer.visit(tree)
        ast.fix_missing_locations(tree)
        # Disponibile da Python 3.9 in poi.
        return ast.unparse(tree)

    def build_user_prompt(self, input_path: str, save_to_file: None | str = None) -> str:
        """
        Legge file Python singoli o intere directory e li unisce in un'unica 
        stringa formattata in Markdown per l'LLM.
        
        Parametri:
        - input_path: Percorso di un file .py o di una cartella.
        - save_to_file: Se True, salva il testo unito nel file locale 'codebase.txt'.
        """
        codebase_chunks = []
        # Maschera Markdown per delimitare chiaramente i file e preservare la sintassi Python
        mask = "### `{fname}`\n```python\n{code}\n```\n\n"
        
        # Caso 1: L'input fornito è un file singolo valido
        if os.path.isfile(input_path):
            files_to_read = [input_path]
        # Caso 2: L'input fornito è una directory (filtra solo i file .py effettivi)
        elif os.path.isdir(input_path):
            files_to_read = [
                os.path.join(input_path, f) 
                for f in os.listdir(input_path) 
                if f.endswith(".py") and os.path.isfile(os.path.join(input_path, f))
            ]
        else:
            print("Il path fornito non è né un file né una directory valida.")
            return ''

        # Lettura sequenziale dei file individuati
        for fpath in files_to_read:
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    s_code : str =f.read()
                    if self.clean_codebase:
                        s_code = self.clean_python_code(s_code)
                    codebase_chunks.append(mask.format(fname=os.path.basename(fpath), code = s_code))
            except Exception as err:
                print(f"Problemi con il file {fpath}: {err}")

        codebase : str = "".join(codebase_chunks)

        # Salvataggio opzionale del prompt aggregato su disco
        if isinstance(save_to_file, str):
            try:
                with open(save_to_file, "w", encoding="utf-8") as f:
                    f.write(codebase)
            except Exception as err:
                print(f"Impossibile salvare codebase.txt: {err}")
                
        return codebase

    def calculate_size_context(self, prompt: str) -> int:
        """
        Stima la dimensione minima della finestra di contesto (num_ctx) 
        necessaria per elaborare il prompt, arrotondandola a blocchi di 1024.
        """
        # Estimates required context window size rounded up to the next 1024 chunk.
        return math.ceil(len(prompt) / self.context_divisor / 1024) * 1024

    def process_analysis(self, model_name: str, codebase_path: str) -> str:
        """
        Invia la richiesta di analisi ad Ollama, traccia i tempi, calcola i metadati 
        e restituisce il report finale comprensivo della risposta dell'IA.

        Parametri:
        - model_name: Nome dell'LLM locale da interpellare.
        - codebase_path: Path del codice sorgente da analizzare.
        - request_at_bottom: Posiziona le istruzioni dopo il codice (True) o prima (False).
        - summary_mode: Se True, include solo i punti chiave nella risposta, altrimenti fornisce un'analisi dettagliata.
        """
        try:
            # Genera la stringa con il codice sorgente formattato
            source_codebase : str = self.build_user_prompt(codebase_path)
            if len(source_codebase) == 0:
                return ''

            # Registra il timestamp di inizio operazione
            start_dt : datetime.datetime= datetime.datetime.now()

            # Assembla l'ordine di lettura del prompt finale
            user_prompt  = (
                f"{source_codebase}\n\n{self.request_prompt}" 
                if self.request_at_bottom 
                else f"{self.request_prompt}\n\n{source_codebase}"
            )

            # Copia le opzioni base per evitare modifiche collaterali all'istanza della classe
            ollama_options = self.default_options.copy()
            context_size : int = -1
            if self.force_context:
                context_size  = self.calculate_size_context(user_prompt)
                ollama_options["num_ctx"] = context_size

            # Struttura dei messaggi per la chat di Ollama
            ollama_messages = [
                {"role": "system", "content": self.system_prompt},
                {"role": "user", "content": user_prompt},
            ]

            # Esecuzione sincrona della chiamata ad Ollama
            response = ollama.chat(model=model_name, messages=ollama_messages, think=self.think, options=ollama_options or None)
            end_dt : datetime.datetime = datetime.datetime.now()

            # Estrazione dei contatori dei token e del testo generato (gestisce i valori mancanti)
            token_in = response.get('prompt_eval_count', 'N/D')
            token_out = response.get('eval_count', 'N/D')
            response_text : str = response.get('message', {}).get('content', '')
            model_name = response.get('model', model_name)
            load_duration = response.get('load_duration', 'N/D')
            if isinstance(load_duration, int):
                load_duration = HumanDiffTime.from_seconds(load_duration // 1_000_000_000)  # Converte da nanosecondi a secondi
            prompt_eval_duration = response.get('prompt_eval_duration', 'N/D')
            if isinstance(prompt_eval_duration, int):
                prompt_eval_duration = HumanDiffTime.from_seconds(prompt_eval_duration // 1_000_000_000)
            eval_duration = response.get('eval_duration', 'N/D')
            if isinstance(eval_duration, int):
                eval_duration = HumanDiffTime.from_seconds(eval_duration // 1_000_000_000) 
            total_duration = response.get('total_duration', 'N/D')
            if isinstance(total_duration, int):
                total_duration = HumanDiffTime.from_seconds(total_duration // 1_000_000_000) 
            thinking  = response.get('thinking', 'N/D')

            if self.summary_mode:
                # Formatta visivamente l'elenco dei parametri di configurazione applicati
                options_str  = "".join([f"  {k}: {v}\n" for k, v in ollama_options.items()])

                # Costruisce l'intestazione informativa da allegare alla risposta del modello
                summary : str = (
                    f"Richiesta inviata alle: {start_dt.isoformat(sep=' ', timespec='seconds')}\n"
                    f"Response ricevuta alle: {end_dt.isoformat(sep=' ', timespec='seconds')}\n"
                    f"Codebase: {codebase_path}\n"
                    f"Tempo trascorso: {HumanDiffTime.from_date(start_dt, end_dt)}\n"
                    f"Modello usato: {model_name}\n"
                    f"Dimensione contesto imposta: {context_size if self.force_context else 'Default'}\n"
                    f"Dimensione prompt: {len(user_prompt)} caratteri\n"
                    f"Token in input: {token_in}\n"
                    f"Token in output: {token_out}\n"
                    f"Tempo caricamento modello: {load_duration}\n"
                    f"Tempo analisi input: {prompt_eval_duration}\n"
                    f"Tempo generazione output: {eval_duration}\n"
                    f"Tempo totale: {total_duration}\n"
                    f"Thinking: {thinking}\n"
                    f"Opzioni Ollama:\n{options_str}"
                    f"\n---\n\n"
                    f"{response_text}"
                )
                return summary
            # Restituisce la forma grezza generata dal modello senza ulteriori formattazioni o aggiunte informative
            return str(response)

        except Exception as err:
            print(f"Errore durante l'elaborazione del modello: {err}")
            return ''

if __name__ == "__main__":
    # Inizializzazione della classe Wrapper
    analyzer = OllamaForCoder()

    # Aggiorna tutti i modelli locali scaricati all'ultima versione disponibile
    analyzer.update_models()

    # Pack current file for testing
    #_ = analyzer.build_user_prompt(__file__, save_to_file='codebase.txt')

    # Disabilita la pulizia del codice per confrontare i risultati
    analyzer.set_clean_codebase(False)
    analyzer.set_think(False)
    analyzer.set_force_context(True)
    analyzer.set_context_divisor(2.2)

    #print(f"Inizio analisi con {start_dt.isoformat(sep=' ', timespec='seconds')}")
    available_models = analyzer.list_names()
    start_dt : datetime.datetime = datetime.datetime.now()
    final_feedback : list[str] = []

    # Ciclo di analisi
    for i, model in enumerate(available_models):
        #if model != "mistral-large:latest":
        #    continue
        sub_start_dt = datetime.datetime.now()
        print(f"{sub_start_dt.isoformat(sep=' ', timespec='seconds')} - Analyzing with model: {model} ({i + 1}/{len(available_models)})")
        fn = __file__
        model_response = analyzer.process_analysis(model, fn)
        try:
            fnr : str = f"response_{model.replace(':', '_')}.txt"
            with open(fnr, "w", encoding="utf-8") as file_output:
                file_output.write(model_response)
            print(f"Analisi completata. Risposta salvata in '{fnr}'.")
        except Exception as e:
            print(f"Errore nel salvataggio del file di risposta: {e}")
        sub_end_dt = datetime.datetime.now()
        msg = f"Tempo totale per {model}: {HumanDiffTime.from_date(sub_start_dt, sub_end_dt)}"
        final_feedback.append(msg)
    end_dt : datetime.datetime = datetime.datetime.now()

    msg = f"Tempo totale per l'analisi di tutti {len(available_models)} modelli: {HumanDiffTime.from_date(start_dt, end_dt)}"
    final_feedback.append(msg)
    print(msg)

    # report minimale complessivo
    try:
        with open(f"response_time.txt", "w", encoding="utf-8") as file_output:
            file_output.write('\n'.join(final_feedback))
    except Exception as e:
        print(f"Errore nel salvataggio del file di risposta finale: {e}")
