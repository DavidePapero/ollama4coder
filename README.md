[![License](https://img.shields.io/github/license/italia/bootstrap-italia.svg)](https://github.com/DavidePapero/AutomateMySlqBackup/LICENSE)
[![ciccio](https://img.shields.io/badge/Status-project_in_beta-blue)](https://github.com/DavidePapero/AutomateMySlqBackup/new/main)

*Leggi questo in un'altra lingua: [Italian](README.IT.md).*

## Analyze your code

This project is a wrapper on Ollama to facilitate code analysis.
In this first version it is designed to manage Python code.
Later *maybe* I'll add more languages.

## Prerequisites

Ollama, updated Python and the Ollama python library must be installed on the machine it runs on

## First analysis

Once Ollama is installed you need to download the templates.
Once this is done, you can analyze a file or a directory containing files by passing the path.

```python
import ollama4coder

analyzer = ollama4coder.OllamaForCoder()
model_response = analyzer.process_analysis(model_name, path_file_python)
print(model_response)
```

## Related articles::

[Primo articolo su questa libreria](https://www.linkedin.com/pulse/ ai-per-poveracci-come-usare-i-modelli-linguistici-locale-infantino-iybne)

[First article on this library](https://www.linkedin.com/pulse/budget-friendly-ai-how-run-large-language-models-free-infantino-nidoe)