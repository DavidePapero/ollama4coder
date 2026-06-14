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

def update_all_models():
    models : list[str] = [modello.model for modello in ollama.list().models]
    for model_name in models:
        print(model_name)
        try:
            ollama.pull(model_name)
        except Exception as e:
            print(f"Error updating model {model_name}: {e}")

if __name__ == "__main__":
    update_all_models()

