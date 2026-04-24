# Campaign Assistant — TODO

Tracks everything that needs to be built for the campaign assistant to reach a working state. Items are grouped by area and roughly ordered by implementation dependency.

---

## Project Bootstrap

- [x] Create `requirements.txt` — Streamlit, anthropic, httpx (for Ollama), python-dotenv, pydantic
- [x] Create `.env.example` with all supported variables and inline comments
- [x] Create `app/__init__.py` and all module `__init__.py` files
- [x] Set up `.gitignore` — exclude `.env`, `*.db`, `.venv/`, `__pycache__/`

---

## Configuration (`app/config.py`)

- [x] Load `.env` with `python-dotenv`
- [x] Validate required variables based on selected `LLM_PROVIDER` (fail fast with a clear message if missing)
- [x] Expose a typed `Settings` dataclass/Pydantic model used across the app
- [x] Support `CAMPAIGN_FOLDER` as a single path (v1) — multiple campaigns can be a v2 feature

---

## LLM Clients (`app/llm/`)

- [ ] Define abstract `BaseLLMClient` in `base.py` with a `complete(system: str, user: str) -> str` interface
- [ ] Implement `AnthropicClient` in `anthropic_client.py`
  - [ ] Use the `anthropic` Python SDK
  - [ ] Respect `ANTHROPIC_MODEL` config
  - [ ] Handle API errors gracefully (rate limits, auth failures) with user-facing messages
- [ ] Implement `OllamaClient` in `ollama_client.py`
  - [ ] Call Ollama's REST API (`/api/chat`) via `httpx`
  - [ ] Respect `OLLAMA_BASE_URL` and `OLLAMA_MODEL` config
  - [ ] Handle connection errors when Ollama is not running
- [ ] Factory function in `base.py` or `config.py` that returns the correct client based on `LLM_PROVIDER`

---

## Campaign Loader (`app/campaign/`)

- [ ] `loader.py` — scan `CAMPAIGN_FOLDER` for known file types:
  - [ ] Collect `README.md`, `characters.md`, `creatures.md`, and any `.txt` file at the root level
  - [ ] Read each file and store as a named string (keyed by filename)
  - [ ] Skip `assets/`, `maps/`, `Tokens/` subfolders
  - [ ] Cache loaded content in session state to avoid re-reading on every query
- [ ] `context.py` — build LLM-ready context blocks:
  - [ ] For in-session queries: include all campaign files (truncate if over a token budget)
  - [ ] For recap generation: include campaign files + last N session debrief answers
  - [ ] Simple truncation strategy for v1; smarter retrieval (embeddings/vector search) is a v2 stretch goal

---

## Session Database (`app/session/`)

- [ ] `database.py`
  - [ ] Create SQLite DB at `DATABASE_PATH` on first run
  - [ ] Schema:
    - `sessions` table: `id`, `campaign_name`, `session_number`, `session_date`, `created_at`
    - `debrief_answers` table: `id`, `session_id`, `question_key`, `answer_text`
    - `recaps` table: `id`, `session_id`, `recap_text`, `generated_at`
  - [ ] Helper functions: `create_session()`, `save_debrief_answers()`, `get_recent_sessions(n)`, `save_recap()`
- [ ] `questions.py`
  - [ ] Define the standard post-session question list (question key + display text)
  - [ ] Allow the list to be extended or overridden via a `questions.json` file in the campaign folder

---

## Prompt Templates (`prompts/`)

- [ ] `query.txt` — system prompt for in-session queries
  - [ ] Instructs the LLM to answer from campaign content only, cite its source (which file), and keep answers concise
  - [ ] Includes a placeholder for injected campaign context
- [ ] `recap.txt` — system prompt for pre-session recap generation
  - [ ] Instructs the LLM to produce a structured DM briefing: last session summary, outstanding threads, expected encounters, DM prep reminders
  - [ ] Includes placeholders for campaign context and session history

---

## Streamlit UI (`app/ui/` and `app/main.py`)

- [ ] `main.py` — top-level Streamlit app
  - [ ] Sidebar: campaign name, current session number, LLM provider indicator
  - [ ] Three tabs: **Query**, **Debrief**, **Recap**
  - [ ] Load config and campaign content on startup; show errors inline if config is missing

- [ ] `ui/query.py` — in-session query tab
  - [ ] Text input for the DM's question
  - [ ] Submit button (also triggers on Enter)
  - [ ] Display LLM response in a styled card
  - [ ] Keep a short query history in session state for the current session

- [ ] `ui/debrief.py` — post-session debrief tab
  - [ ] Render each question from `questions.py` as a text area
  - [ ] Session number auto-increments from the last saved session; allow manual override
  - [ ] Save button writes all answers to the database
  - [ ] Confirmation message and summary after save

- [ ] `ui/recap.py` — pre-session recap tab
  - [ ] "Generate Recap" button
  - [ ] Show a spinner while the LLM call is in progress
  - [ ] Display the generated recap in a readable format
  - [ ] "Save Recap" button to persist the generated text to the database
  - [ ] Show previously saved recaps for reference

---

## Testing

- [ ] Unit tests for `loader.py` — mock filesystem, check file discovery and skipping logic
- [ ] Unit tests for `database.py` — in-memory SQLite, test schema creation and CRUD helpers
- [ ] Unit tests for `context.py` — check truncation and context assembly
- [ ] Integration test for each LLM client — mock HTTP responses, verify prompt formatting
- [ ] Manual end-to-end test checklist (documented in `tests/e2e_checklist.md`)

---

## Documentation

- [ ] Add usage screenshots to `README.md` once the UI exists
- [ ] Document the `questions.json` override format in `README.md`
- [ ] Add a `CONTRIBUTING.md` if the project is opened up

---

## Stretch Goals (v2)

- [ ] Support multiple campaign folders — selector in the sidebar
- [ ] Vector embeddings for smarter campaign context retrieval (avoid token limit issues on large campaigns)
- [ ] Player-facing view — a read-only mode showing only what players should know
- [ ] Export recap as a PDF or shareable markdown file
- [ ] Automatic session number detection from the database
- [ ] Support additional LLM providers (OpenAI, Google Gemini)
- [ ] Whisper integration for voice-to-text debrief input
