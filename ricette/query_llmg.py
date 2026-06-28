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
import traceback

import ollama

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn

import httpx
import asyncio

import costanti
from pydantic import BaseModel

app = FastAPI()

class RequestRecipe(BaseModel):
    text: str

def GenerateQueryLLM(system_prompt : str, user_prompt : str) -> list[dict[str,str]]:
    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]

@app.post("/ricette")
async def ricette(data: RequestRecipe):
    if len(costanti.OLLAMA_HOST) == 0:
        costanti.OLLAMA_HOST = os.getenv('OLLAMA_HOST', 'http://localhost:11434')
        print(f'Server Ollama: {costanti.OLLAMA_HOST}')
    print(str(data))

    system_prompt : str = "sei un assistente specializzato nel capire la lingua usata in un testo scritto."
    user_prompt : str  = ('In che lingua è il messaggio che ti passerò. Rispondi in maniera coincisa con solo la lingua. '
            'Se non lo puoi capire con con sicurezza rispondi con la parola: indeterminato. '
            f'Questo è il messaggio: {data.text}')

    query = GenerateQueryLLM(system_prompt, user_prompt)

    # prima determino la lingua della richiesta
    print(f'{user_prompt}')
    try:
        clientollama = ollama.AsyncClient(host=costanti.OLLAMA_HOST)
        response = await clientollama.chat(model=costanti.GENERATE_MODEL, messages=query)
        lingua : str = response.get('message', {}).get('content', 'indeterminato').lower()
        print(f'Ottenuto: {lingua}')
        if 'indeterminato' in lingua or 'italiano' in lingua:
            lingua = 'italiano'

        payload = {
            "text": data.text,
            "number_doc": 5
        }

        url = os.getenv('KB_SERVER_URL', 'http://localhost:7000/cerca-ricette')
        print(f'Cerco il contesto: {url}')
        contesto = ''
        async with httpx.AsyncClient() as clientkb:
            response : httpx.Response = await clientkb.post(url, json=payload)
            response.raise_for_status()
            print(response)

            # Il server ritorna una tupla di due liste di stringhe
            print('response.json() ... ')
            risultato = response.json()
            print('response.json() -> ok')
            if len(risultato) == 0:
                print('Nessuno risultato -')
                return ''
            if len(risultato['recipe']) == 0:
                print('Nessuno risultato +')
                return ''

            for i, ricetta in enumerate(risultato['recipe']):
                contesto += f'<documento id="{i}">\n```markdown\n'
                contesto += ricetta
                contesto += '\n```\n</documento>\n\n\n'

        # devo tradurre la domanda?
        domanda_in_italiano : str = data.text
        if lingua != 'italiano':
            print(f'Traduco da {lingua} in italiano il testo in ingresso')
            system_prompt = (
                    "Sei un assistente traduttore. Limitati a fare quanto richiesto"
                )
            user_prompt = ("Traduci in italiano il testo che ti passerò. "
                        "Non aggiungere tue considerazioni, limitati a tradurre il testo. "
                        f"Questo è il testo da tradurre: {data.text}"
                )

            query = GenerateQueryLLM(system_prompt, user_prompt)
            response = await clientollama.chat(model=costanti.GENERATE_MODEL, messages=query)
            domanda_in_italiano : str = response.get('message', {}).get('content', '')
            if len(domanda_in_italiano) < 2:
                domanda_in_italiano = data.text
            print(f'Traduzione: {domanda_in_italiano}')

        system_prompt = (
            "Sei un assistente di cucina. Rispondi alla domanda dell'utente "
            "usando esclusivamente le informazioni contenute nelle ricette fornite "
            "come contesto. Se il contesto non contiene una risposta adeguata, "
            "dillo chiaramente invece di inventare informazioni."
        )
        user_prompt = f"## Ricette disponibili\n\n{contesto}## Domanda\n{domanda_in_italiano}"

        print('Faccio lavorare LLM generativo sul contesto')
        query = GenerateQueryLLM(system_prompt, user_prompt)
        response = await clientollama.chat(model=costanti.GENERATE_MODEL, messages=query)
        ricette_trovate : str = response.get('message', {}).get('content', '')
        print('Ok')

        # devo tradurre le ricette nella lingua dell'utente?
        if lingua != 'italiano':
            print(f'traduco le ricette in {lingua}')
            system_prompt = (
                    "Sei un assistente traduttore. Limitati a fare quanto richiesto"
                )
            user_prompt = (f"Traduci il testo che ti passerò in {lingua}. "
                        "Non aggiungere tue considerazioni, limitati a tradurre il testo. "
                        f"Questo è il testo da tradurre: {ricette_trovate}"
                )

            query = GenerateQueryLLM(system_prompt, user_prompt)
            response = await clientollama.chat(model=costanti.GENERATE_MODEL, messages=query)
            ricette_trovate = response.get('message', {}).get('content', '')
            print('Testo')

        return ricette_trovate
    except Exception as err:
        print(err)
        traceback.print_exc()
    return ''

if __name__ == "__main__":
    modulo : str = f'{os.path.basename(__file__)[:-3]}:app'
    uvicorn.run(modulo, host="0.0.0.0", port=7000, reload=True)
