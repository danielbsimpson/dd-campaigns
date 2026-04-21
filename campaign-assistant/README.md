# Campaign Assistant

A web-based D&D campaign assistant for Dungeon Masters. Point it at any campaign folder, and it will help you wrap up sessions, brief you before the next one, and answer questions during play — all powered by an LLM of your choice.

---

## Features

| Feature | Description |
|---|---|
| **Campaign Ingestion** | Reads and indexes your campaign folder — characters, creatures, lore, and full campaign text |
| **Post-Session Debrief** | Guided end-of-session questionnaire capturing key events, decisions, deaths, and discoveries |
| **Pre-Session Recap** | Generates a focused DM briefing before each session, drawing on past notes and campaign content |
| **In-Session Query** | Fast, freeform query interface — ask about stat blocks, NPC motivations, lore, or anything in your campaign |

---

## Architecture

| Layer | Technology |
|---|---|
| **UI** | [Streamlit](https://streamlit.io/) — Python-native browser-based web app |
| **LLM** | [Anthropic Claude](https://www.anthropic.com/) or local models via [Ollama](https://ollama.com/) — configurable per environment |
| **Storage** | SQLite — session notes, debrief answers, and summaries stored locally |
| **Campaign Data** | Plain filesystem reads — works with any campaign folder following the structure below |

### Project Structure

```
campaign-assistant/
├── app/
│   ├── main.py                  # Streamlit app entry point and page routing
│   ├── config.py                # Loads and validates .env configuration
│   ├── llm/
│   │   ├── base.py              # Abstract LLM client interface
│   │   ├── anthropic_client.py  # Anthropic Claude implementation
│   │   └── ollama_client.py     # Ollama (local) implementation
│   ├── campaign/
│   │   ├── loader.py            # Reads and indexes campaign folder files
│   │   └── context.py           # Assembles relevant campaign content for LLM prompts
│   ├── session/
│   │   ├── database.py          # SQLite schema, read/write helpers
│   │   └── questions.py         # Post-session question definitions and flow
│   └── ui/
│       ├── query.py             # In-session query tab
│       ├── debrief.py           # Post-session debrief tab
│       └── recap.py             # Pre-session recap tab
├── prompts/
│   ├── recap.txt                # System prompt template for pre-session recap
│   └── query.txt                # System prompt template for in-session queries
├── requirements.txt
├── .env.example
├── README.md
└── TODO.md
```

---

## Setup

### Prerequisites

- Python 3.11+
- One of:
  - An [Anthropic API key](https://console.anthropic.com/) for cloud-based inference
  - [Ollama](https://ollama.com/) installed and running locally for fully offline use

### Installation

1. Navigate to this directory:
   ```bash
   cd campaign-assistant
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   # Windows
   .venv\Scripts\activate
   # macOS / Linux
   source .venv/bin/activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Copy the example environment file and configure it:
   ```bash
   cp .env.example .env
   ```

### Configuration

Edit `.env` with your values:

| Variable | Description | Default |
|---|---|---|
| `LLM_PROVIDER` | `anthropic` or `ollama` | `anthropic` |
| `ANTHROPIC_API_KEY` | Your Anthropic API key | — |
| `ANTHROPIC_MODEL` | Claude model identifier | `claude-opus-4-5` |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Ollama model name (e.g. `llama3`, `mistral`) | `llama3` |
| `CAMPAIGN_FOLDER` | Absolute path to your campaign folder | — |
| `DATABASE_PATH` | Path for the SQLite session database | `./sessions.db` |

### Running

```bash
streamlit run app/main.py
```

The app opens in your browser at `http://localhost:8501`.

---

## Campaign Folder Structure

The assistant works with any campaign folder. It looks for the following files (all optional):

```
My Campaign/
├── README.md          # Campaign overview and summary
├── characters.md      # NPC roster and character details
├── creatures.md       # Creature stat blocks and descriptions
└── My Campaign.txt    # Full campaign narrative / booklet
```

Subfolders (e.g. `assets/`, `maps/`) are ignored. Any markdown or plain text file at the root level is read and indexed.

---

## Session Workflow

### After Each Session — Debrief Tab

1. Open the **Debrief** tab
2. Answer the prompted questions. Examples:
   - What did the party accomplish this session?
   - Were there any character deaths or major injuries?
   - What key decisions did the players make?
   - Which NPCs did they interact with?
   - What plot hooks were revealed or followed up on?
   - Where did the session end (location, situation)?
3. Save — answers are written to the SQLite database with a session timestamp

### Before Each Session — Recap Tab

1. Open the **Recap** tab
2. Select the campaign to recap (if multiple are configured)
3. The assistant retrieves recent session notes and the most relevant campaign content
4. It generates a DM briefing covering:
   - Where the party left off
   - Outstanding plot threads and decisions
   - NPCs and creatures likely to appear next session
   - Any player-facing hooks to have ready

### During a Session — Query Tab

1. Open the **Query** tab
2. Type any question about your campaign. Examples:
   - *"What are the Hrimfang's stat blocks?"*
   - *"Remind me of Bjorn Ironside's motivation and what he knows."*
   - *"What traps did I plan for the ice cave?"*
   - *"What are the weaknesses of a Rakshasa?"*
3. The assistant searches indexed campaign content and returns a focused answer

---

## LLM Providers

### Anthropic Claude (cloud)

Set `LLM_PROVIDER=anthropic` and provide your `ANTHROPIC_API_KEY`. Recommended for best response quality.

### Ollama (local / offline)

Set `LLM_PROVIDER=ollama`. Requires [Ollama](https://ollama.com/) running locally with your chosen model pulled:

```bash
ollama pull llama3
```

Good models for this use case: `llama3`, `mistral`, `gemma3`.

---

## Data & Privacy

- All session notes are stored in a local SQLite database — nothing is sent anywhere except to your configured LLM provider.
- When using Ollama, the entire pipeline is local and offline.
- Campaign files are never modified by the assistant.
