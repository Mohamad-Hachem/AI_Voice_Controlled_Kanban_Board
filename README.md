# Voice-Controlled AI Kanban Board

![Python](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)
![Gradio](https://img.shields.io/badge/Gradio-6.0-F97316?logo=gradio&logoColor=white)
![OpenAI](https://img.shields.io/badge/OpenAI-GPT--4o-412991?logo=openai&logoColor=white)
![Web Speech API](https://img.shields.io/badge/Web_Speech_API-Browser--Native-22C55E?logo=googlechrome&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-16A34A)

> A fully interactive drag-and-drop Kanban board with **AI voice control** — speak a command, watch the board respond. Built as a custom [Gradio 6](https://www.gradio.app/) component with OpenAI `gpt-4o` intent parsing and the Web Speech API.

---

## What Is This?

This project is a **production-quality Kanban board** built entirely in Python on top of Gradio 6's `gr.HTML` component model. It ships in two flavours:

| File | What it does |
|---|---|
| `kanban.py` | Core board — drag-and-drop, inline editing, priority labels, search, column collapse |
| `kanban_voice.py` | Voice-controlled variant — speak to add, move, delete, or reprioritise cards |
| `kanban_board_with_live_sync.py` | Live-sync variant — board state persists to JSON, auto-refreshes every 2 s |
| `python_gradio_client_for_live_kanban_sync.py` | Python API client for the live-sync board |

---

## Screenshots

### The Board — Ready State
The board loads with four workflow columns, a real-time progress bar, and the voice command bar at the bottom.

![Board ready state](application_screenshots/Screenshot%202026-03-26%20191329.png)

---

### Cards Distributed Across Columns
Cards with priority labels (red = high, yellow = medium, green = low) spread across To Do, In Progress, Review, and Done. Stats pills update live.

![Cards across columns](application_screenshots/Screenshot%202026-03-26%20191401.png)

---

### Speaking a Voice Command
The mic button (bottom-right) is clicked. The Web Speech API transcribes speech into the command bar in real time — no typing required.

![Voice command typed](application_screenshots/Screenshot%202026-03-26%20191437.png)

---

### Board Updated After Voice Command
After speaking *"add a card call it hello world"*, OpenAI parses the intent and the board adds the new card instantly. The AI Status bar confirms the action taken.

![Card added by voice](application_screenshots/Screenshot%202026-03-26%20192010.png)

---

## Feature List

### Board (all versions)
- **Drag-and-drop** cards between columns
- **Inline editing** — double-click any card text to rename it
- **Priority cycling** — click the colour dot (🔴🟡🟢) to cycle through high / medium / low
- **Delete cards** — one-click `✕` button per card
- **Column collapse** — hide/show columns to focus
- **Live search / filter** — type in the search box to highlight matching cards
- **Progress bar** — animated bar driven by the percentage of cards in the Done column
- **Stats pills** — total task count and done % always visible in the header

### Voice Control (`kanban_voice.py`)
- **One-click mic** — fixed purple button, bottom-right corner
- **Zero-latency transcription** — Web Speech API runs entirely in the browser (Chrome/Edge)
- **Natural language commands** — fuzzy intent parsing handles casual phrasing
- **OpenAI `gpt-4o` intent parser** — returns structured JSON; never hallucinates column IDs
- **Fuzzy card matching** — "move the login thing to done" correctly finds "Fix login bug"
- **Auto-execute** — no manual button press needed; the board updates the moment you stop speaking
- **AI Status bar** — shows exactly what was heard and what action was taken

### Live Sync (`kanban_board_with_live_sync.py`)
- Board state persisted to `board_state.json`
- `gr.Timer(2)` auto-refresh — board stays current across browser sessions
- Explicit REST-style API endpoints: `/add_card`, `/move_card`, `/clear_board`, `/set_board`, `/set_title`
- Python client (`python_gradio_client_for_live_kanban_sync.py`) for programmatic control

---

## Voice Commands You Can Say

| Say this | What happens |
|---|---|
| *"Add a card called Fix login bug to To Do"* | New card appears in To Do |
| *"Move Fix login bug to In Progress"* | Card slides to In Progress |
| *"Move Fix login bug to Done"* | Card moves to Done, progress bar updates |
| *"Delete Fix login bug"* | Card is removed |
| *"Set Fix login bug to high priority"* | Card gets red priority bar |
| *"Add Deploy to production to Done with high priority"* | High-priority card added to Done |
| *"What's in Review?"* | OpenAI returns unknown action; status bar clarifies |

---

## Architecture

### Gradio 6 Component Model

```
┌─────────────────────────────────────────────────────────┐
│                      Browser (Svelte)                    │
│                                                          │
│   KanbanBoard (gr.HTML subclass)                        │
│   ┌──────────────────────────────────────────────────┐  │
│   │  HTML_TEMPLATE  ←── board_title, value (dict)    │  │
│   │  CSS_TEMPLATE   ←── injected into shadow DOM     │  │
│   │  JS_ON_LOAD     ←── runs once, wires all events  │  │
│   │                                                   │  │
│   │  User drags card → JS mutates props.value dict   │  │
│   │                   → trigger('change') fires       │  │
│   │                   → Gradio sends dict to Python   │  │
│   └──────────────────────────────────────────────────┘  │
│                                                          │
│   Python returns gr.HTML(value=new_dict)                 │
│   → Svelte diffs and re-renders only changed cards       │
└─────────────────────────────────────────────────────────┘
```

### Voice Control Pipeline

```
┌─────────┐     ┌──────────────────┐     ┌─────────────────────┐
│  User   │────▶│  Web Speech API  │────▶│  Voice Command      │
│ speaks  │     │  (browser-side)  │     │  Textbox (Gradio)   │
└─────────┘     └──────────────────┘     └──────────┬──────────┘
                                                     │
                                          JS sets native Svelte
                                          value, clicks Execute btn
                                                     │
                                                     ▼
                                         ┌───────────────────────┐
                                         │   handle_voice()      │
                                         │   Python handler      │
                                         └──────────┬────────────┘
                                                    │
                               ┌────────────────────┼────────────────────┐
                               │                    │                    │
                               ▼                    ▼                    ▼
                    ┌──────────────────┐  ┌──────────────────┐  ┌──────────────┐
                    │ parse_voice_     │  │  Board state     │  │  Column      │
                    │ command()        │  │  (current dict)  │  │  + card list │
                    │                  │  └──────────────────┘  └──────────────┘
                    │  OpenAI gpt-4o   │◀──────── both passed as context ────────
                    │  JSON response   │
                    └──────────┬───────┘
                               │
                    ┌──────────▼───────┐
                    │ action_          │
                    │ dispatcher()     │
                    │                  │
                    │  add  / move /   │
                    │  delete/priority │
                    └──────────┬───────┘
                               │
                    ┌──────────▼───────┐
                    │ gr.HTML(         │
                    │   value=         │
                    │   new_board_dict │
                    │ )                │
                    └──────────┬───────┘
                               │
                    ┌──────────▼───────┐
                    │ Gradio re-renders│
                    │ board in browser │
                    └──────────────────┘
```

### Board Data Schema

```python
{
    "columns": [
        {
            "id": "todo",              # used to route voice commands
            "title": "📋 To Do",
            "color": "#6366f1",        # column accent colour
            "collapsed": False,
            "cards": [
                {
                    "id": "a1b2c3d4",  # 8-char UUID fragment
                    "text": "Fix login bug",
                    "priority": "high",  # high | medium | low
                    "tags": []
                }
            ]
        },
        {"id": "progress", ...},
        {"id": "review",   ...},
        {"id": "done",     ...}        # % complete is cards here / total cards
    ]
}
```

### OpenAI Intent Parsing — Action Schemas

```
Input:  transcript (string) + board_state (dict with all columns and cards)

Output (one of):
  {"action": "add",      "text": "...",  "column": "<id>", "priority": "low|medium|high"}
  {"action": "move",     "card": "...",  "to": "<column id>"}
  {"action": "delete",   "card": "..."}
  {"action": "priority", "card": "...",  "priority": "low|medium|high"}
  {"action": "unknown",  "message": "..."}
```

`response_format={"type": "json_object"}` guarantees valid JSON — no markdown wrapping, no prose.

---

## Tech Stack

| Layer | Technology |
|---|---|
| UI framework | [Gradio 6](https://www.gradio.app/) (`gr.HTML` custom component) |
| Frontend logic | Vanilla JavaScript (ES6) inside `JS_ON_LOAD` string |
| Speech-to-text | [Web Speech API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Speech_API) (free, browser-native) |
| AI intent parsing | [OpenAI](https://platform.openai.com/) `gpt-4o` with `response_format=json_object` |
| Python | 3.10+ |
| Dependencies | `gradio>=6.0`, `openai`, `python-dotenv` |

---

## Getting Started

### 1. Clone the repo

```bash
git clone https://github.com/Mohamad-Hachem/drag-and-drop-kanban-board.git
cd drag-and-drop-kanban-board
```

### 2. Create and activate a virtual environment

```bash
python -m venv .venv

# Windows (bash / Git Bash)
source .venv/Scripts/activate

# macOS / Linux
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install "gradio>=6.0" openai python-dotenv
```

### 4. Add your OpenAI API key

Create a `.env` file in the project root:

```
OPENAI_API_KEY=sk-proj-...
```

> The key is loaded automatically by `python-dotenv` at startup. Never commit `.env` to git.

### 5. Run the app

**Board only (no voice):**
```bash
python kanban.py
```

**Voice-controlled board:**
```bash
python kanban_voice.py
```

**Live-sync board + Python client (two terminals):**
```bash
# Terminal 1
python kanban_board_with_live_sync.py

# Terminal 2
python python_gradio_client_for_live_kanban_sync.py
```

Open the printed URL in **Chrome or Edge** (voice recognition requires these browsers).

---

## How the Voice Feature Works — Step by Step

1. **Click the mic button** (purple, bottom-right corner). It turns red to show it is listening.
2. **Speak your command** naturally — e.g. *"add a card called Deploy to production to Done with high priority"*.
3. **Web Speech API** transcribes your speech in real time and writes the text to the command bar.
4. The **JavaScript layer** uses the native Svelte value setter to update the textbox, then programmatically clicks the Execute button — no manual interaction needed.
5. **`handle_voice()`** fires in Python. It calls **`parse_voice_command()`** which sends the transcript plus the full current board state to **OpenAI gpt-4o**.
6. OpenAI returns a structured JSON action (e.g. `{"action": "add", "text": "Deploy to production", "column": "done", "priority": "high"}`).
7. **`action_dispatcher()`** deep-copies the board state, applies the mutation, and returns the updated dict.
8. Gradio receives `gr.HTML(value=new_dict)`, Svelte diffs the DOM, and the card appears instantly.
9. The **AI Status bar** confirms: *Heard: "add a card called Deploy…" → Added "Deploy to production" to Done*.

---

## Project Structure

```
drag-and-drop-kanban-board/
├── kanban_voice.py                      # Voice-controlled board
├── kanban_board_with_live_sync.py       # Live-sync board with REST API
├── python_gradio_client_for_live_kanban_sync.py   # Python API client
├── application_screenshots/             # Screenshots used in this README
├── .env                                 # Your API key (not committed)
├── .gitignore
└── .venv/                               # Virtual environment (not committed)
```

---

## Why This Project Is Interesting

### For an AI portfolio

- **Multimodal input** — combines audio, NLP, and a live UI. Three AI layers in one demo.
- **Real AI orchestration** — not just an API call. The system does intent classification, entity extraction (card name, target column), fuzzy reference resolution, and conditional action dispatch. This is a minimal agent loop.
- **Tangible, demo-able** — screen-record yourself saying *"move the login bug to done"* and watching a card animate across the board. That is far more memorable than a static chatbot.
- **Custom Gradio 6 component** — shows understanding of the `gr.HTML` template/prop/trigger model, not just `gr.Chatbot` wrappers.
- **Clean separation of concerns** — voice layer is ~120 lines added on top of the existing board, zero rewrites.

### Technical depth

- Uses the **native Svelte value setter** to update Gradio 6 internal state from external JS — a non-obvious integration technique.
- **Fuzzy card matching** in Python handles "the login thing" → "Fix login bug" using word-overlap scoring.
- **`response_format={"type": "json_object"}`** in the OpenAI call guarantees parse-safe output with zero post-processing.
- The Gradio 6 component pattern (`props.value` + `trigger('change')`) means the entire board is a single reactive Python dict — no database, no websocket, no custom server.

---

## Troubleshooting

| Symptom | Fix |
|---|---|
| Mic button is grey | Switch to Chrome or Edge. Firefox does not support the Web Speech API. |
| Status bar says "Error: ..." | Check your `.env` file contains a valid `OPENAI_API_KEY`. |
| Status bar says "Could not find card" | The fuzzy match failed. Try saying the card name more precisely. |
| Board does not update after typing | Make sure you press Enter or click the Execute button. |
| Board does not update after speaking | Open DevTools (F12) → Console and check for JS errors. |

---

## License

MIT — use it, fork it, build on it.

---

*Built with [Gradio](https://www.gradio.app/) and [OpenAI](https://platform.openai.com/).*
