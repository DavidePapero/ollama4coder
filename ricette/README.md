## Test con LLM Locali

Quello che trovate in questa cartella è tutto ciò che è necessario per avere un motore di ricerca multilingue su oltre 28000 ricette di cucina italiana.
Questo progetto serve per illustrare un post su Linkedin in cui parlo dei RAG.
Sono post divulgativi che non hanno intenzione di essere scientifici.

## Prerequisiti

Bisogna avere una macchina in cui sia installato docker e docker compose, abbia accesso ad internet, e almeno 5 GB di spazio libero su disco.

## Avvio

Una volta scaricato tutta la cartella da qualche parte, da una console dentro la vostra cartella, dovete dare il comando:

```bash
sudo docker compose up --build -d
```
quello che succederà al primo avvio è che il "sistema" scaricherà dei modelli LLM open sul computer, e poi indicizzerà le ricette. Attenzione in questa fase il sistema non deve essere interrotto. Sul mio computer ci ha messo circa 7 ore per finire il lavoro.

Una volta effettuato, se siete sul computer con il docker engine, se dal browser andate all'indirizzo http://localhost:8000 potrete fare ricerche sulle ricette italiane in qualsiasi lingua. Il sistema è lento però, ci vuole pazienza.

## Articoli collegati:

[Primo articolo su questa libreria](https://www.linkedin.com/pulse/ai-per-poveracci-come-usare-i-modelli-linguistici-locale-infantino-iybne)

[Secondo articolo su questa libreria](https://www.linkedin.com/posts/davideinfantino_la-lingua-degli-llm-activity-7471882016066830336-LVhJ)
