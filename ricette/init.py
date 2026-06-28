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

import os
import signal
import time
import datetime
import sys

print (os.path.basename(__file__))

import costanti

import uvicorn

import build_kb

CONTINUA : bool = True
def Loop():
    global CONTINUA

    # ho creato il database?
    if os.path.isdir(costanti.DB_PATH) is False:
        print(f'{datetime.datetime.now().isoformat(sep = ' ', timespec = 'seconds')} - Inizializzo il sistema')
        build_kb.build()
        print(f'{datetime.datetime.now().isoformat(sep = ' ', timespec = 'seconds')} - Finita inizializzazione')

    uvicorn.run("query_kb:app", host="0.0.0.0", port=5000)

def signal_handler(signalvalue, frame):
    global CONTINUA

    if CONTINUA:
        CONTINUA = False
        print(f'Esco')
    else:
        print ('Autokill')
        sys.exit(0)

if __name__ == "__main__":
    signal.signal(signal.SIGINT,  signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    costanti.OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')

    Loop()
