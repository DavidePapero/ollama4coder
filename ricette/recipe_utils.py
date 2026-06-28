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
Conversione di una ricetta (dict caricato da JSON) in un testo Markdown leggibile,
da usare sia per l'indicizzazione che come contesto passato al modello.
"""

def recipe_to_markdown(ricetta: dict) -> str:
    nome = ricetta.get("Nome", "")
    tipo = ricetta.get("Tipo_Piatto", "")
    ingrediente_principale = ricetta.get("Ing_Principale", "")
    persone = ricetta.get("persone", "")
    note = ricetta.get("Note", "")
    ingredienti = ricetta.get("Ingredienti", [])
    preparazione = ricetta.get("Preparazione", "")

    if nome is None or len(nome) == 0:
        return ''
    if ingredienti is None or len(ingredienti) == 0:
        return ''

    righe = [f"# {nome}", "",]

    if tipo is not None and len(tipo) > 0:
        righe.extend( [f"**Tipo:** {tipo}", "",] )

    if ingrediente_principale is not None and len(ingrediente_principale) > 0:
        righe.extend( [f"**Ingrediente principale:** {ingrediente_principale}", "",] )

    if persone is not None and len(persone) > 0:
        righe.extend( [f"**Persone:** {persone}", "",] )

    if note is not None and len(note) > 0:
        righe.extend( [f"**Note:** {note}", "",] )

    righe.append("## Ingredienti")
    righe.append("")
    for ing in ingredienti:
            righe.append(f"- {ing}")
    righe.append("")

    righe += ["## Preparazione", "", preparazione]

    return "\n".join(righe)


if __name__ == "__main__":
    # Piccolo test manuale
    esempio =      {
        "Nome": "Gnocchi Con Fontina (2)",
        "Tipo_Piatto": "Primo",
        "Ing_Principale": "Formaggio Fontina",
        "Persone": "4",
        "Note": None,
        "Ingredienti": [
            "400 G Gnocchi Di Patate",
            "120 G Formaggio Fontina A Fettine",
            "5 Cucchiai Panna",
            "Formaggio Parmigiano Grattugiato",
            "Burro",
            "Sale"
        ],
        "Preparazione": "Ungere di burro una teglia e accendere il forno al massimo. Lessare gli gnocchi in abbondante acqua salata e ritirarli con la schiumarola man mano che vengono a galla. Metterli nella teglia. Cospargerli con il parmigiano, poi unire la panna e coprire con la fontina tagliata a fettine. Passare in forno finché la fontina è fusa e servire gli gnocchi ben caldi."
    }

    d = recipe_to_markdown(esempio)
    with open(r'C:\local_git\github\ollama4coder\ricette\access\test_ricetta.md', 'w', encoding='UTF-8') as f:
        f.write(d)
