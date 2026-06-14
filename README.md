*Leggi questo in un'altra lingua: [Italian](README.IT.md).*

## Analyze your code

This project is used to have attachments on posts on Linkedin.
They are informative posts that have no intention of being scientific.

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

[First article on this library](https://www.linkedin.com/pulse/budget-friendly-ai-how-run-large-language-models-free-infantino-nidoe)

[Second article on this library](https://www.linkedin.com/posts/davideinfantino_speaking-the-language-of-ai-activity-7471894617056202752-74kD)
