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
"""
Server web minimale con FastAPI e uvicorn.
Pagina: "Cerca la tua ricetta italiana"
"""

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.responses import FileResponse
import uvicorn

app = FastAPI()

HTML_PAGE = """<!DOCTYPE html>
<html lang="it">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>Cerca la tua ricetta italiana</title>

  <!-- Marked.js per il rendering Markdown -->
  <!-- script src="https://cdn.jsdelivr.net/npm/marked/marked.min.js"></script -->
  <script src="https://cdn.jsdelivr.net/npm/markdown-it/dist/markdown-it.min.js"></script>

  <style>
    /* ── Reset & base ────────────────────────────────────────── */
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root {
      --bg:        #f8f8f8;
      --white:     #ffffff;
      --text:      #222222;
      --muted:     #666666;
      --accent:    #c0392b;   /* rosso italiano */
      --border:    #d0d0d0;
      --radius:    24px;
      --shadow:    0 1px 6px rgba(0,0,0,.12), 0 2px 20px rgba(0,0,0,.06);
    }

    body {
      background: var(--bg);
      color: var(--text);
      font-family: Arial, sans-serif;
      font-size: 15px;
      line-height: 1.6;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
    }

    /* ── Logo / intestazione ─────────────────────────────────── */
    header {
      margin-top: 80px;
      text-align: center;
      user-select: none;
    }

    .logo-text {
      font-size: 52px;
      font-weight: 700;
      letter-spacing: -1px;
      line-height: 1;
    }

    /* Colori tricolore sul titolo */
    .logo-text .g  { color: #009246; }
    .logo-text .o  { color: #009246; }
    .logo-text .o2 { color: var(--text); }
    .logo-text .g2 { color: var(--accent); }
    .logo-text .l  { color: var(--accent); }
    .logo-text .e  { color: #009246; }

    .logo-sub {
      font-size: 13px;
      color: var(--muted);
      margin-top: 6px;
      letter-spacing: .4px;
    }

    /* ── Casella di ricerca ──────────────────────────────────── */
    .search-wrapper {
      margin-top: 32px;
      display: flex;
      flex-direction: column;
      align-items: center;
      gap: 16px;
      width: 100%;
      max-width: 580px;
      padding: 0 16px;
    }

    .search-box {
      width: 100%;
      display: flex;
      align-items: center;
      background: var(--white);
      border: 1px solid var(--border);
      border-radius: var(--radius);
      box-shadow: var(--shadow);
      padding: 12px 20px;
      gap: 10px;
      transition: box-shadow .15s;
    }

    .search-box:focus-within {
      box-shadow: 0 1px 6px rgba(0,0,0,.20), 0 4px 24px rgba(0,0,0,.10);
      border-color: transparent;
      outline: 2px solid var(--accent);
      outline-offset: 1px;
    }

    .search-icon {
      color: var(--muted);
      flex-shrink: 0;
    }

    #query {
      flex: 1;
      border: none;
      outline: none;
      font-size: 16px;
      background: transparent;
      color: var(--text);
    }

    #query::placeholder { color: #aaa; }

    #query:disabled,
    #cerca:disabled {
      opacity: .5;
      cursor: not-allowed;
    }

    /* ── Pulsante cerca ──────────────────────────────────────── */
    #cerca {
      background: #f2f2f2;
      border: 1px solid var(--border);
      border-radius: 4px;
      padding: 9px 18px;
      font-size: 14px;
      color: var(--text);
      cursor: pointer;
      transition: background .15s, box-shadow .15s;
    }

    #cerca:hover:not(:disabled) {
      background: var(--white);
      box-shadow: 0 1px 3px rgba(0,0,0,.2);
      border-color: #c6c6c6;
    }

    /* ── Messaggio di attesa ─────────────────────────────────── */
    #attesa {
      display: none;
      font-size: 14px;
      color: var(--muted);
      font-style: italic;
      animation: pulse 1.4s ease-in-out infinite;
    }

    @keyframes pulse {
      0%, 100% { opacity: 1; }
      50%       { opacity: .45; }
    }

    /* ── Area risultato Markdown ─────────────────────────────── */
    #risultato {
      margin-top: 28px;
      width: 100%;
      max-width: 680px;
      padding: 0 16px 60px;
    }

    #risultato-inner {
      background: var(--white);
      border: 1px solid var(--border);
      border-radius: 12px;
      box-shadow: var(--shadow);
      padding: 28px 32px;
      display: none;
    }

    /* Stile del Markdown renderizzato */
    #risultato-inner h1,
    #risultato-inner h2,
    #risultato-inner h3 {
      color: var(--accent);
      margin: 1em 0 .4em;
      font-weight: 700;
    }

    #risultato-inner h1 { font-size: 1.5em; }
    #risultato-inner h2 { font-size: 1.25em; }
    #risultato-inner h3 { font-size: 1.05em; }

    #risultato-inner p   { margin: .5em 0; }
    #risultato-inner ul,
    #risultato-inner ol  { padding-left: 1.4em; margin: .5em 0; }
    #risultato-inner li  { margin: .2em 0; }
    #risultato-inner strong { color: #111; }

    #risultato-inner hr {
      border: none;
      border-top: 1px solid var(--border);
      margin: 1.2em 0;
    }

    #risultato-inner code {
      background: #f2f2f2;
      border-radius: 3px;
      padding: 1px 5px;
      font-size: .9em;
    }

    /* ── Footer ──────────────────────────────────────────────── */
    footer {
      margin-top: auto;
      border-top: 1px solid var(--border);
      width: 100%;
      padding: 12px 24px;
      background: #f2f2f2;
      font-size: 13px;
      color: var(--muted);
      text-align: center;
    }
  </style>
</head>
<body>

  <!-- Intestazione stile Google storico -->
  <header>
    <div class="logo-text">
      <span class="g">C</span><span class="o">e</span><span class="o2">r</span><span
            class="g2">c</span><span class="l">a</span>
    </div>
    <p class="logo-sub">la tua ricetta italiana</p>
  </header>

  <!-- Casella di ricerca -->
  <div class="search-wrapper">
    <div class="search-box">
      <!-- icona lente -->
      <svg class="search-icon" width="18" height="18" viewBox="0 0 24 24"
           fill="none" stroke="currentColor" stroke-width="2"
           stroke-linecap="round" stroke-linejoin="round">
        <circle cx="11" cy="11" r="8"/>
        <line x1="21" y1="21" x2="16.65" y2="16.65"/>
      </svg>
      <input id="query" type="text"
             placeholder="Es: risotto alla milanese, pasta al pomodoro…"
             autocomplete="off" />
    </div>

    <button id="cerca" onclick="eseguiRicerca()">Cerca</button>
    <span id="attesa">Attendere con pazienza&hellip;</span>
  </div>

  <!-- Area risultato -->
  <div id="risultato">
    <div id="risultato-inner"></div>
  </div>

  <footer>Powered by FastAPI &amp; uvicorn &nbsp;·&nbsp; Ricette 100% italiane</footer>

  <script>
    async function eseguiRicerca() {
      const queryEl  = document.getElementById('query');
      const cercaBtn = document.getElementById('cerca');
      const attesaEl = document.getElementById('attesa');
      const innerEl  = document.getElementById('risultato-inner');
      const text     = queryEl.value.trim();

      if (!text) {
        queryEl.focus();
        return;
      }

      // Disabilita controlli e mostra messaggio
      queryEl.disabled = true;
      cercaBtn.disabled = true;
      attesaEl.style.display = 'block';
      innerEl.style.display  = 'none';
      innerEl.innerHTML = '';

      try {
        // ── Chiamata REST al server remoto ──────────────────────────
        // Sostituisci l'URL con quello del tuo server remoto reale.
        const url = `/api/cerca?text=${encodeURIComponent(text)}`;
        const resp = await fetch(url);

        if (!resp.ok) throw new Error(`Errore HTTP ${resp.status}`);

        const markdown = await resp.text();
        // console.log("risposta dal server: ", markdown);

        // Renderizza il Markdown
        const md = window.markdownit();
        const a = md.render(markdown);
        const b = a.replaceAll("&quot;", "").replaceAll("###", " ")
        const c = b.replaceAll("\\\\n", "<br>");
        //console.log(JSON.stringify(c));
        innerEl.innerHTML = c;
        innerEl.style.display = 'block';

      } catch (err) {
        innerEl.innerHTML =
          `<p style="color:var(--accent)">
             ⚠️ Si è verificato un errore: <strong>${err.message}</strong>
           </p>`;
        innerEl.style.display = 'block';

      } finally {
        // Riabilita controlli
        attesaEl.style.display = 'none';
        queryEl.disabled  = false;
        cercaBtn.disabled = false;
        queryEl.focus();
      }
    }

    // Cerca anche premendo Invio
    document.getElementById('query').addEventListener('keydown', e => {
      if (e.key === 'Enter') eseguiRicerca();
    });
  </script>
</body>
</html>
"""


@app.get("/favicon.ico", include_in_schema=False)
async def favicon():
    return FileResponse("favicon.ico")

@app.get("/", response_class=HTMLResponse)
async def homepage():
    """Restituisce la pagina HTML principale."""
    return HTML_PAGE


@app.get("/api/cerca")
async def cerca_ricetta(text: str):
    """
    Endpoint REST che inoltra la query al server remoto e restituisce
    la risposta in formato Markdown (testo semplice).

    ── PERSONALIZZA QUI ────────────────────────────────────────────────
    Sostituisci l'URL e la logica seguente con la chiamata al tuo
    server remoto reale (es. un'API AI, un backend dedicato, ecc.).
    ─────────────────────────────────────────────────────────────────────
    """
    import httpx

    print(f"L'untente chiede: {text}")
    REMOTE_URL = os.getenv('SERVER_BACK_END', 'http://localhost:5000/ricette')
    payload = payload = {'text' : text}

    try:
        async with httpx.AsyncClient(timeout=None) as client:
            print(f'Interrogo: {REMOTE_URL}')
            response : httpx.Response = await client.post(REMOTE_URL, json=payload)
            print(response)
            response.raise_for_status()
            return response.text  # il server remoto risponde in Markdown

    except Exception as err:
        print(err)
        traceback.print_exc()


# ── Avvio diretto ────────────────────────────────────────────────────────
if __name__ == "__main__":
    modulo : str = f'{os.path.basename(__file__)[:-3]}:app'
    uvicorn.run(modulo, host="0.0.0.0", port=8000, reload=True)
