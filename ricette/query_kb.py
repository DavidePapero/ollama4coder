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
Ricerca RAG sulle ricette: recupera dal database vettoriale le ricette piu'
pertinenti alla domanda e chiede al modello generativo di rispondere
basandosi esclusivamente su quel contesto.

Esegui:
    python query_kb.py
"""

import os

import chromadb
import ollama

import costanti

from fastapi import FastAPI
from pydantic import BaseModel
from typing import List

print('Avvio server REST')
costanti.OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
app = FastAPI()

client = chromadb.PersistentClient(path=costanti.DB_PATH)
collection = client.get_collection(costanti.COLLECTION_NAME)
clientollama = ollama.AsyncClient(host=costanti.OLLAMA_HOST)


# Modello input prima API
class InputData(BaseModel):
    text: str
    number_doc: int

# Modello input seconda API
class InputString(BaseModel):
    text: str

# --------------------------------------------------------------------------

async def recupera_ricette(query: str, k: int ):
    """
    Retrieves recipes from the knowledge base based on a query.

    Args:
    - query (str): The search query.
    - k (int): The number of results to return. Defaults to TOP_K.
    """

    print(f'{query}, {k}')

    result : dict = {}

    try:
        # Genero l'embedding per la richeesta
        query_embedding = await clientollama.embed(model=costanti.EMBED_MODEL, input=query)
        # Estraggo il vettore numerico
        vettore = query_embedding['embeddings'][0]

        #where = {"tipo": tipo} if tipo else None
        print('Chiamo: collection.query')

        risultati = collection.query(
            query_embeddings=[vettore],
            n_results=k,
            #where=where,
        )

        result['recipe'] = risultati["documents"][0]
        result['metadata'] = risultati["metadatas"][0]
        print(f'Ritorno {len(result['recipe'])} ricette')

    except Exception as err:
        print(f"Error recupera_ricette: {err}")

    return result

# --------------------------------------------------------------------------

@app.post("/cerca-ricette")
async def cerca_ricette(data: InputData):
    result = await recupera_ricette(data.text, data.number_doc)
    return result
