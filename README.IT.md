[![License](https://img.shields.io/github/license/italia/bootstrap-italia.svg)](https://github.com/DavidePapero/AutomateMySlqBackup/LICENSE)
[![ciccio](https://img.shields.io/badge/Status-project_in_beta-blue)](https://github.com/DavidePapero/AutomateMySlqBackup/new/main)

*Read this in other languages: [English](README.md).*

## Analizza il tuo codice

Questo progetto è un wrapper su Ollama per facilitare l'analisi di codice. 
In questa prima versione è pensato per gestire il codice python. 
Successivamente *forse* aggiungerò altri linguaggi.

## Prerequisiti

Nella macchina in cui gira è necessario sia installato il Ollama, Python aggiornato e la libreria di python Ollama

## Prima analisi

Una volta installato Ollama bisogna scaricare i modelli. 
Fatto questo si può analizzare un file o una directory contenente file passandone il path.

```python
import ollama4coder

analyzer = ollama4coder.OllamaForCoder()
model_response = analyzer.process_analysis(model_name, path_file_python)
print(model_response)
```

## Articoli collegati:


[Primo articolo su questa libreria](https://www.linkedin.com/pulse/ ai-per-poveracci-come-usare-i-modelli-linguistici-locale-infantino-iybne)
