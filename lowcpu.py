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


import psutil
import time
import platform

def Work() -> None:
    """Funzione che monitora i processi di Ollama e ne abbassa la priorità se è troppo alta."""
    ollama_exe = ['ollama.exe', 'llama-server.exe']
    if platform.system() == 'Linux':
        # su Linux i processi non hanno estensione .exe, quindi rimuovo l'estensione
        ollama_exe = ['ollama', 'llama-server']
    while True:
        # aspetto
        time.sleep(2)
        try:
            for proc in psutil.process_iter(['name',]):
                if proc.info['name'].lower() in ollama_exe:
                    if int(proc.nice()) > int(psutil.NORMAL_PRIORITY_CLASS):
                        print( f"I lower the priority of the {proc.info['name']} process (nice: {proc.nice()})")
                        proc.nice(psutil.NORMAL_PRIORITY_CLASS)
        except psutil.NoSuchProcess:
            # il processo è terminato, ignoro e continuo
            pass
        except psutil.AccessDenied:
            # non ho i permessi per modificare la priorità, mi blocco e aspetto che l'utente mi dia i permessi
            print("Access denied. Need elevated privileges.")
            break
        except Exception as e:
            print(f"Errore: {e}")
            break

if __name__ == '__main__':
    print(f"Running on {platform.system()} {platform.release()}")
    print("Starting Ollama Low CPU Priority Manager...")
    print("Press Ctrl+C to stop.")
    Work()