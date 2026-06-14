*Read this in other languages: [English](README.md).*

## Test con LLM Locali

Questo progetto serve per avere allegati su dei post su Linkedin.
Sono post divulgativi che non hanno intenzione di essere scientifici.

## Prerequisiti

Ollama, updated Python and the Ollama python library must be installed on the machine it runs on.

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

[Primo articolo su questa libreria](https://www.linkedin.com/pulse/ai-per-poveracci-come-usare-i-modelli-linguistici-locale-infantino-iybne)
[Secondo articolo su questa libreria](https://www.linkedin.com/pulse/ai-per-poveracci-come-usare-i-modelli-linguistici-locale-infantino-iybne)
