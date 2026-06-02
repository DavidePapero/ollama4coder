[![License](https://img.shields.io/github/license/italia/bootstrap-italia.svg)](https://github.com/DavidePapero/AutomateMySlqBackup/LICENSE)
[![ciccio](https://img.shields.io/badge/Status-project_in_beta-blue)](https://github.com/DavidePapero/AutomateMySlqBackup/new/main)

*Read this in other languages: [English](README.md).*

## Analizza il tuo codice

Questo progetto è un wrapper su Ollama per facilitare l'analisi di codice. In questa prima è pensato per il codice python. Successivamente forse aggiungerò altri linguaggi.

## Prerequisiti

Nella macchina in cui gira è necessario sia installato il Ollama, Python aggiornato e la libreria di python Ollama

## Prima analisi

Una volta installato Ollama bisogna scaricare i modelli. Poi si può analizzare con un modello passandone il nome

```python
import ollama4coder

analyzer = ollama4coder.OllamaForCoder()
model_response = analyzer.process_analysis(model_name, path_file_python)
print(model_response)
```

you compile the docker image and install the relevant container.
Attention you need to configure the volume. In my case the backup files are placed on the host machine in a specific folder. This path must be aligned with the path that appears in the config.json to the "backup_file" and "backup_path" entries
