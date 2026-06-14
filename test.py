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
import ollama


domanda : str = r"""
## Formula:

Let \( x \) be the mass of a brick.
We have the following equation:

$x \text{kg} = 1\,\text{kg} + \frac{1}{2}x \text{kg}$

## Request:

Can you solve this equation?

## Conditions:

Show the reasoning needed for the resolution.
"""

def Generate(enable_thinking_request: bool = True):
    #esiste la directory dei risultati? se no la creo
    if os.path.exists('res') is False:
        os.mkdir('res')

    # modelli disponibili
    models : list[str] = [modello.model for modello in ollama.list().models]
    for i, model_name in enumerate(models):
        print(f"Model: {model_name} ({i+1}/{len(models)})")
        respo_show = ollama.show(model_name)

        #il modello può fare thinking?
        enable_thinking : bool = False
        if enable_thinking_request:
            enable_thinking : bool = 'thinking' in respo_show.get('capabilities', [])

        response = None
        try:
            # analisi
            response = ollama.generate(model=model_name, prompt=domanda, think = enable_thinking)
            # salvataggio risposta
            response_text : str = response.get('response', '')
            second_duration = response.get('total_duration', '0') // 1_000_000_000
            fn = os.path.join('res', f'{model_name.replace(":", "_")}-{second_duration}.md')
            with open(fn, 'w', encoding='utf-8') as f:
                f.write(response_text)
            # era abilitato il thinking? salvo anche quello
            if enable_thinking:
                thinking : str = str(response.get('thinking', '') )
                fn = os.path.join('res', f'{model_name.replace(":", "_")}-thinking.md')
                with open(fn, 'w', encoding='utf-8') as f:
                    f.write(thinking)
        except Exception as e:
            print(f"Error for model {model_name}: {e}")
            continue

if __name__ == "__main__":
    Generate(False)

