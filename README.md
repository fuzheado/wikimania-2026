# Wikimania 2026 — Schedule Explorer

A fast, filterable browser for the [Wikimania 2026](https://wikimania.wikimedia.org/wiki/2026:Wikimania) conference schedule in Paris (July 21–25).

**Live:** [fuzheado.github.io/wikimania-2026](https://fuzheado.github.io/wikimania-2026/)

## Features

- **Full-text search** across session titles, abstracts, speakers, and track names
- **Filters** by day, track, language, and session type
- **Expandable cards** with full session abstracts
- **Speaker click-to-filter** — click any speaker name to see all their sessions
- **Direct links** to original session pages on eventyay

## How it works

Two static files served via GitHub Pages:

| File | Size | Purpose |
|---|---|---|
| `index.html` | ~15 KB | UI, CSS, and client-side JavaScript |
| `wikimania2026_data.js` | ~730 KB | Pre-fetched session data from the Wikimania eventyay API |

The data file sets `window.WIKIMANIA_DATA` with all sessions and filter metadata. The HTML reads it and renders everything client-side — no build step, no dependencies, no server.

## Local development

```bash
# Serve locally with Python
python3 -m http.server 8080

# Or open directly in your browser
open index.html
```

No build tools or `npm install` needed.
