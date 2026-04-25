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
- [ ] **Phase 1:** restrict `LLM_PROVIDER` literal to `"ollama"` | `"lmstudio"` only; cloud provider values are rejected with a clear "not yet supported" message pointing to the roadmap
- [ ] **Phase 2:** expand `LLM_PROVIDER` literal to include cloud providers as each client is implemented

---

## LLM Clients (`app/llm/`)

> **Phasing note:** Build and validate everything locally first. Cloud providers and credential storage are defined here for completeness but are not implemented until Phase 2 — after local inference is working end-to-end. Stub files for cloud clients are created early so the registry compiles, but their `complete()` methods raise `NotImplementedError` until Phase 2.

### Phase 1 — Core Interface & Local Providers

- [ ] Define abstract `BaseLLMClient` in `base.py` with a `complete(system: str, user: str) -> str` interface
- [ ] `ProviderRegistry` — a dict mapping provider keys to (client class, required credential fields, optional fields); register only local providers initially; cloud provider entries added in Phase 2
- [ ] Factory function `get_llm_client(provider: str, config: dict) -> BaseLLMClient` — constructs the correct client; in Phase 1 only `"ollama"` and `"lmstudio"` are valid
- [ ] `ollama_client.py` — Ollama (primary local backend, **default**)
  - [ ] Call Ollama's REST API (`/api/chat`) via `httpx`
  - [ ] Respect `OLLAMA_BASE_URL` (default `http://localhost:11434`) and `OLLAMA_MODEL` from config
  - [ ] Default recommended model: `llama3.1:8b` — fits comfortably in 8 GB VRAM (RTX 4060) at Q4 quantisation (~4.5 GB)
  - [ ] Other well-tested options for 8 GB VRAM: `mistral:7b-instruct`, `phi3:medium` (~7 GB Q4), `qwen2.5:7b`
  - [ ] On startup, query `/api/tags` to list locally available models and populate a dropdown in settings
  - [ ] Detect whether Ollama is using GPU: parse `/api/show` response for `nvidia` in `details` — show GPU/CPU badge in settings UI
  - [ ] Handle connection errors when Ollama is not running with a clear "Start Ollama first" message
  - [ ] Document GPU setup: requires CUDA toolkit + Ollama ≥ 0.1.29; RTX 4060 requires CUDA 12.x driver
- [ ] `lmstudio_client.py` — LM Studio (OpenAI-compatible local server, secondary local option)
  - [ ] Call LM Studio's `/v1/chat/completions` endpoint via `httpx`
  - [ ] Default base URL: `http://localhost:1234`
  - [ ] Query `/v1/models` to list loaded model and populate the model field automatically
  - [ ] GPU acceleration is automatic via LM Studio's built-in CUDA/Metal support; no extra config required
- [ ] Create empty stub files for cloud clients: `anthropic_client.py`, `openai_client.py`, `gemini_client.py`, `groq_client.py`, `mistral_client.py` — each contains the class inheriting `BaseLLMClient` with `complete()` raising `NotImplementedError("Cloud provider not yet configured")`; stubs allow the registry to be fully defined without any cloud SDK dependencies being imported at runtime

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

### Memory Taxonomy

The assistant works with five distinct memory layers. Each layer has different persistence, retrieval priority, and update patterns:

| Layer | Source | Mutability | Retrieved for |
|---|---|---|---|
| **Campaign Lore** | Campaign files (README, .txt) | Static (file-driven) | All queries |
| **Entity State** | DM debrief + manual edits | Dynamic | Queries about NPCs/locations/factions |
| **Character Roster** | DM-maintained player character records | Semi-static | Recap + party-related queries |
| **Session Episodes** | Post-session debrief answers | Append-only | Recap + recent-history queries |
| **Narrative Threads** | DM-curated hooks, quests, foreshadowing | Dynamic | Recap + plot queries |

### `database.py`

- [ ] Create SQLite DB at `DATABASE_PATH` on first run with `PRAGMA journal_mode=WAL` for concurrent reads
- [ ] Schema — **Sessions & Debrief** (existing, unchanged):
  - `sessions`: `id`, `campaign_name`, `session_number`, `session_date`, `created_at`
  - `debrief_answers`: `id`, `session_id`, `question_key`, `answer_text`
  - `recaps`: `id`, `session_id`, `recap_text`, `generated_at`
- [ ] Schema — **Entity State** (new):
  - `npcs`: `id`, `campaign_name`, `name`, `role`, `disposition`, `last_seen_session`, `notes`, `updated_at`
    - `disposition` is a short freetext field: "friendly", "hostile", "unknown", "dead", etc.
  - `locations`: `id`, `campaign_name`, `name`, `visited` (bool), `first_seen_session`, `state_notes`, `updated_at`
    - `state_notes` captures dynamic changes ("the temple is now ruined", "guards doubled after session 3")
  - `factions`: `id`, `campaign_name`, `name`, `standing` (int −3 to +3), `notes`, `updated_at`
- [ ] Schema — **Character Roster** (new):
  - `player_characters`: `id`, `campaign_name`, `player_name`, `character_name`, `class`, `level`, `backstory_notes`, `active` (bool), `updated_at`
  - `pc_inventory`: `id`, `pc_id`, `item_name`, `description`, `acquired_session`, `notable` (bool)
    - Only notable items (quest items, unique magic, character-defining gear) are tracked — not every piece of equipment
- [ ] Schema — **Narrative Threads** (new):
  - `threads`: `id`, `campaign_name`, `title`, `type` (`quest`/`mystery`/`foreshadowing`/`consequence`), `status` (`active`/`resolved`/`abandoned`), `description`, `introduced_session`, `resolved_session`, `updated_at`
  - `thread_sessions`: `thread_id`, `session_id` — many-to-many join tracking which sessions touched a thread
- [ ] Schema — **LLM Credentials** (new, shared with `llm/credentials.py`):
  - `llm_credentials`: `id`, `provider`, `key_name`, `encrypted_value`, `updated_at`
- [ ] Helper functions — existing:
  - `create_session()`, `save_debrief_answers()`, `get_recent_sessions(n)`, `save_recap()`
- [ ] Helper functions — Entity State:
  - `upsert_npc(campaign, name, **fields)`, `get_npcs(campaign, disposition=None) -> list`
  - `upsert_location(campaign, name, **fields)`, `get_visited_locations(campaign) -> list`
  - `upsert_faction(campaign, name, **fields)`, `get_factions(campaign) -> list`
- [ ] Helper functions — Character Roster:
  - `upsert_pc(campaign, character_name, **fields)`, `get_active_pcs(campaign) -> list`
  - `add_notable_item(pc_id, item_name, description, session_id)`
- [ ] Helper functions — Narrative Threads:
  - `create_thread(campaign, title, type, description, session_id)`, `resolve_thread(thread_id, session_id)`
  - `get_active_threads(campaign) -> list`, `get_threads_for_session(session_id) -> list`
- [ ] Schema migrations: use a `schema_version` table + version-gated `ALTER TABLE` statements so existing databases upgrade cleanly on first launch

### `memory.py` (new — retrieval orchestrator)

Centralises *what* gets included in each LLM context request and *why*. Keeps `context.py` from becoming a monolith.

- [ ] `build_query_context(campaign_name, query_text, token_budget) -> str`
  - Always include: **Campaign Lore** (README + .txt files, truncated if large)
  - Always include: **Active Narrative Threads** (titles + one-line descriptions)
  - Always include: **Active PC roster** (name, class, level)
  - Conditionally include based on query keyword heuristics:
    - Query mentions an NPC name → include that NPC's full entity state record
    - Query mentions a location → include that location's state notes
    - Query mentions a faction → include faction standing + notes
    - Query seems session-history related → include last 2 session debrief summaries
  - Remaining budget: fill with the most recent session debrief answers (newest first)
- [ ] `build_recap_context(campaign_name, n_recent_sessions, token_budget) -> str`
  - Always include: **Campaign Lore** (abbreviated — README only)
  - Always include: **Active PC roster** (full records)
  - Always include: **All active Narrative Threads** (full descriptions)
  - Always include: **Last N session debrief answers** (full text, N from config default 3)
  - Always include: **NPC disposition summary** (name + disposition for all non-dead NPCs)
  - Always include: **Faction standings** (all factions, one line each)
  - Fill remaining budget with: resolved threads from the last 3 sessions
- [ ] `build_debrief_context(session_id) -> str`
  - Returns a lightweight context block used when auto-populating thread linkage suggestions in the debrief UI
  - Includes: active threads + NPC list (names only) + location list (names only)
- [ ] Token budget enforcement: simple character-count proxy (1 token ≈ 4 chars) for v1; swap to `tiktoken` or provider-native counting in v2
- [ ] Each `build_*` function returns a structured string with clearly labelled sections (e.g. `## Campaign Lore`, `## Active Quests`) so prompt templates can reference them predictably

### `questions.py`

- [ ] Define the standard post-session question list (question key + display text) covering:
  - What happened this session (brief summary)
  - Which NPCs were meaningfully interacted with
  - Which locations were visited or had their state change
  - Which narrative threads advanced, were resolved, or were newly introduced
  - What player decisions or consequences should be remembered
  - Any notable items acquired or lost
  - DM prep notes for next session
- [ ] Allow the list to be extended or overridden via a `questions.json` file in the campaign folder
- [ ] After saving debrief answers, run a lightweight post-save pass: prompt the DM to review/update entity state and threads based on the answers they just entered (surfaced in the debrief UI, not an automatic write)

---

## Prompt Templates (`prompts/`)

- [ ] `query.txt` — system prompt for in-session queries
  - [ ] Instructs the LLM to answer from campaign content only, cite its source (which file), and keep answers concise
  - [ ] Includes a placeholder for injected campaign context
- [ ] `recap.txt` — system prompt for pre-session recap generation
  - [ ] Instructs the LLM to produce a structured DM briefing: last session summary, outstanding threads, expected encounters, DM prep reminders
  - [ ] Includes placeholders for campaign context and session history

---

## Voice Input (`app/voice/`)

Allows the DM to speak answers into the microphone at the end of a session rather than typing. The primary use case is the post-session debrief — the DM talks through what happened while it's still fresh, and the assistant transcribes each answer into its text field. Secondary use case is the in-session query tab.

### `transcriber.py` — speech-to-text backend

- [ ] Define abstract `BaseTranscriber` with a single method `transcribe(audio_bytes: bytes) -> str`
- [ ] `FasterWhisperTranscriber` — local GPU transcription (default)
  - [ ] Use the `faster-whisper` library (CTranslate2-based, significantly faster than OpenAI's `whisper` package on CUDA)
  - [ ] Default model: `medium` — best accuracy/speed balance on an RTX 4060 (~2 GB VRAM, real-time factor < 0.3×)
  - [ ] Also support `small` (faster, lower VRAM) and `large-v3` (highest accuracy, ~4 GB VRAM — leaves headroom alongside an 8B LLM if they don't run simultaneously)
  - [ ] Load the model once at startup and hold it in session state; unload when voice is disabled to reclaim VRAM
  - [ ] Force `device="cuda"`, `compute_type="float16"` when a CUDA device is detected; fall back to `device="cpu"`, `compute_type="int8"` silently
  - [ ] Expose `language` param (default `"en"`); can be overridden in settings for multilingual campaigns
- [ ] `WhisperAPITranscriber` — cloud fallback
  - [ ] Call OpenAI's `/v1/audio/transcriptions` endpoint via `httpx`
  - [ ] Reuse the OpenAI API key from `credentials.py` if already saved; otherwise prompt in settings
  - [ ] Use `whisper-1` model (the only available option on the API)
- [ ] `TranscriberRegistry` — maps backend keys (`"local"`, `"openai_api"`) to their classes, mirroring `ProviderRegistry` in the LLM module
- [ ] Factory: `get_transcriber(backend: str) -> BaseTranscriber` — used by the UI

### `recorder.py` — in-browser mic capture

- [ ] Use `audio_recorder_streamlit` (lightweight Streamlit component, no WebRTC server required) to capture mic audio as WAV bytes
- [ ] Return raw `bytes`; all format handling stays in `transcriber.py`
- [ ] Expose a `record_button(label: str, key: str) -> bytes | None` helper used by the UI — returns `None` if the user hasn't recorded anything yet
- [ ] Handle browser permission denial gracefully — show an inline warning rather than an unhandled component error

### Settings integration

- [ ] Add a **Voice** section to `ui/settings.py`:
  - [ ] Enable/disable toggle — when off, all mic buttons are hidden across the app; Whisper model is unloaded if it was in memory
  - [ ] Backend selector: `Local (faster-whisper)` | `OpenAI Whisper API`
  - [ ] Model size selector (local only): `small` / `medium` (default) / `large-v3` — show estimated VRAM usage next to each option
  - [ ] Language field (default `en`) — free text, accepts any Whisper-supported language code
  - [ ] "Test Mic" button: records a short clip and displays the transcription so the DM can verify the setup before a session
  - [ ] VRAM budget warning: if the selected Whisper model + the selected LLM model together exceed ~7 GB, show an amber warning suggesting the DM use a smaller Whisper model or run them sequentially

---

## Streamlit UI (`app/ui/` and `app/main.py`)

- [ ] `main.py` — top-level Streamlit app
  - [ ] Sidebar: campaign name, current session number, active LLM provider + model name, GPU/CPU badge for local providers
  - [ ] Four tabs: **Query**, **Debrief**, **Recap**, **Settings**
  - [ ] Load config and campaign content on startup; show errors inline if config is missing
  - [ ] On first launch (no credentials saved), redirect automatically to the Settings tab with a setup banner

- [ ] `ui/settings.py` — provider & configuration management
  - [ ] **Phase 1 — Local providers only:**
    - [ ] Provider selector showing `Ollama` (default) and `LM Studio`
    - [ ] Ollama section: base URL field, model dropdown populated live from `/api/tags`, "Refresh" button, GPU/CPU badge
    - [ ] LM Studio section: base URL field, model field auto-populated from `/v1/models`
    - [ ] "Test Connection" button — calls `BaseLLMClient.complete()` with a short ping prompt and shows success/failure inline
    - [ ] GPU detection badge — green "GPU (CUDA)" or amber "CPU only"
    - [ ] "Recommended models for 8 GB VRAM" hint with `ollama pull llama3.1:8b` pre-filled
    - [ ] Campaign folder path field with a folder-exists validation indicator
    - [ ] Settings persisted to a local `settings.json` (no encryption needed for Phase 1 — no secrets stored)
  - [ ] **Phase 2 — Cloud providers** *(see the dedicated Phase 2 section later in this file)*:
    - [ ] Expand provider selector to include cloud options (Anthropic, OpenAI, Gemini, Groq, Mistral)
    - [ ] Dynamic credential form per cloud provider driven by `ProviderRegistry`
    - [ ] API key fields wired to `credentials.py` (encrypted storage); existing values shown redacted (•••• last 4 chars)
    - [ ] "Test Connection" updated to handle cloud auth errors distinctly from network errors

- [ ] `ui/query.py` — in-session query tab
  - [ ] Text input for the DM's question
  - [ ] Mic button beside the text input (visible only when voice is enabled in settings) — recording populates the text field and auto-submits
  - [ ] Submit button (also triggers on Enter)
  - [ ] Display LLM response in a styled card with a collapsible "Context used" expander showing which memory layers were included
  - [ ] Keep a short query history in session state for the current session

- [ ] `ui/debrief.py` — post-session debrief tab
  - [ ] Render each question from `questions.py` as a text area
  - [ ] When voice is enabled: show a mic button beneath each question — clicking records until the user stops, then transcribes and populates the text area (text remains fully editable after transcription)
  - [ ] "Record All" mode: cycles through each unanswered question sequentially — reads the question text aloud via `st.info`, records, transcribes, advances automatically; DM can interrupt and edit at any point
  - [ ] Visual transcription state per question: idle → recording (red pulse) → transcribing (spinner) → done (green tick)
  - [ ] Session number auto-increments from the last saved session; allow manual override
  - [ ] Save button writes all answers to the database
  - [ ] After save: show a "Review & Update" panel surfacing:
    - NPCs mentioned in answers → prompt DM to confirm/update disposition
    - Locations mentioned → prompt DM to mark as visited and add state notes
    - Thread suggestions: highlight answers that seem to advance or resolve an active thread; let DM confirm linkage
    - New thread prompt: "Did this session introduce a new quest or plot hook?" with quick-add form
  - [ ] Confirmation message and summary after full save + review pass

- [ ] `ui/recap.py` — pre-session recap tab
  - [ ] "Generate Recap" button
  - [ ] Show a spinner while the LLM call is in progress
  - [ ] Display the generated recap in a readable format with sections matching the prompt template
  - [ ] "Save Recap" button to persist the generated text to the database
  - [ ] Show previously saved recaps for reference

- [ ] `ui/world.py` — world state browser (new)
  - [ ] Three sub-tabs: **NPCs**, **Locations**, **Threads**
  - [ ] NPCs: filterable table (by disposition, last-seen session); inline edit for disposition and notes
  - [ ] Locations: list of visited/unvisited locations; inline edit for state notes
  - [ ] Threads: Kanban-style columns for Active / Resolved / Abandoned; click a thread to expand full description and session history; quick-add and resolve buttons
  - [ ] All edits save immediately via the database helpers; no separate Save button needed

---

## Phase 2 — Cloud Providers & Credential Storage

> Implement only after the full local workflow (query, debrief, recap, world state) is working end-to-end and validated.

### Cloud LLM Providers (`app/llm/`)

- [ ] Update `config.py` to accept cloud providers in the `LLM_PROVIDER` literal once a cloud client is implemented
- [ ] `anthropic_client.py` — Anthropic (Claude)
  - [ ] Use the `anthropic` Python SDK
  - [ ] Support model selection: `claude-opus-4-5`, `claude-sonnet-4-5`, `claude-haiku-3-5`
  - [ ] Handle API errors gracefully (rate limits, auth failures) with user-facing messages
- [ ] `openai_client.py` — OpenAI
  - [ ] Use the `openai` Python SDK
  - [ ] Support model selection: `gpt-4o`, `gpt-4o-mini`, `gpt-4-turbo`
  - [ ] Handle quota and auth errors
- [ ] `gemini_client.py` — Google Gemini
  - [ ] Use `google-generativeai` SDK
  - [ ] Support model selection: `gemini-2.0-flash`, `gemini-1.5-pro`, `gemini-1.5-flash`
  - [ ] Handle safety filter blocks — surface them as user-facing warnings, not crashes
- [ ] `groq_client.py` — Groq (fast cloud inference, free tier)
  - [ ] Use `groq` Python SDK
  - [ ] Support model selection: `llama-3.3-70b-versatile`, `llama-3.1-8b-instant`, `mixtral-8x7b-32768`
- [ ] `mistral_client.py` — Mistral AI
  - [ ] Use `mistralai` Python SDK
  - [ ] Support model selection: `mistral-large-latest`, `mistral-small-latest`, `open-mixtral-8x7b`

### Credential & Settings Storage (`app/llm/credentials.py`)

- [ ] Persist provider credentials to the SQLite DB in an `llm_credentials` table (provider, key_name, encrypted_value)
- [ ] Encrypt values at rest using `cryptography` (Fernet) with a machine-local key stored in the user's home dir (`~/.campaign_assistant_key`) — prevents casual credential exposure if the DB file is shared
- [ ] `save_credential(provider, key_name, value)`, `load_credential(provider, key_name) -> str | None`, `delete_credential(provider, key_name)`
- [ ] Never log or print credential values; redact in error messages
- [ ] Update settings UI to show cloud provider credential forms wired to `credentials.py`; existing values shown redacted (•••• last 4 chars)
- [ ] Uncomment cloud SDK dependencies in `requirements.txt` and `cryptography>=42.0.0`

---

## Testing

### Unit & Integration Tests

- [ ] Unit tests for `loader.py` — mock filesystem, check file discovery and skipping logic
- [ ] Unit tests for `database.py` — in-memory SQLite, test schema creation and CRUD helpers for all five memory layers
- [ ] Unit tests for `context.py` / `memory.py` — check truncation, context assembly, and conditional inclusion logic per query type
- [ ] Unit tests for `credentials.py` — verify encrypt/decrypt round-trip; verify nothing is logged in plaintext
- [ ] Integration test for each LLM client — mock HTTP responses, verify prompt formatting and error handling
- [ ] Integration test for `ProviderRegistry` + factory — verify all registered providers construct without error given valid credentials
- [ ] Unit tests for `transcriber.py` — mock `faster-whisper` and the OpenAI API, verify both backends return a string and handle empty audio gracefully
- [ ] Manual end-to-end test checklist (documented in `tests/e2e_checklist.md`)

### LLM Accuracy Evaluation (`tests/accuracy/`)

Validates that the assistant returns *correct, grounded* answers from campaign content — not hallucinations, cross-campaign contamination, or fabricated lore.

#### Test Case Format

- [ ] Define a JSON schema for test cases in `tests/accuracy/schema.json`:
  ```json
  {
    "id": "ll_001",
    "campaign": "La Llorona",
    "question": "Who hired the party to investigate the river spirit?",
    "expected_contains": ["Consuela Vargas"],
    "expected_absent": [],
    "source_file": "characters.md",
    "memory_layer": "campaign_lore",
    "type": "factual_recall",
    "should_refuse": false
  }
  ```
  - `expected_contains`: list of strings that must appear (case-insensitive) in the response
  - `expected_absent`: strings that must *not* appear — used for hallucination and cross-contamination checks
  - `type`: one of `factual_recall` | `npc_disposition` | `location` | `creature` | `plot_thread` | `boundary` | `refusal`
  - `should_refuse`: `true` if the correct answer is "that information is not in the campaign files"

#### Test Data Files (seeded from existing campaigns)

- [ ] `tests/accuracy/la_llorona.json` — seed with at minimum:
  - Factual recall: "Who is the quest giver?" → Consuela Vargas
  - NPC disposition: "What is Alcalde Vásquez's role?" → antagonist / cover-up
  - Location: "Where does Father Domingo Vela operate from?" → Church of Santa Muerte
  - Plot: "What is Esperanza Vargas de Reyes?" → La Llorona, the spirit haunting the river
  - Creature: sourced from `creatures.md` — at least two questions on creature weaknesses/abilities
  - Boundary: "What is the name of the tavern in Hafnheim?" → should refuse (that's Nordheim lore)
- [ ] `tests/accuracy/the_curse_of_the_pharaoh.json` — seed with at minimum:
  - Factual recall: "Who leads the Scarab Cult?" → Cult Leader (fanatical mage-priest)
  - NPC: "What is the Gynosphinx's role?" → Colosseum master
  - Location: "Where do the missing explorers need to be rescued from?" → Western Hive — Androsphinx Statue Chamber
  - Plot: "Who is the final boss?" → Anubis / Act 6 Temple of Anubis
  - Boundary: "Who is La Llorona?" → should refuse (cross-campaign contamination test)
- [ ] `tests/accuracy/the_rakshasa.json` — seed with at minimum:
  - Factual recall: "Who is the main villain?" → Grand Vizier Kiran / Vikramasura
  - NPC: "What is Yogi Ananda's role?" → ancient sage / lore source / key ally
  - Location: "Where is the real General Abhaya imprisoned?" → hidden prison beneath the barracks
  - Refusal: "What level are the player characters?" → should refuse (not in campaign files)
- [ ] `tests/accuracy/the_salvation_of_nordheim.json` — seed with at minimum:
  - Factual recall: "Who is the main quest-giver?" → Bjorn Ironclad
  - NPC: "What is Melissa Sutton secretly?" → controlled by the thieves guild
  - Location: "What tavern is in Woodvost?" → The Giant Fox (owner: Guy Clayden)
  - Boundary: "Who is Consuela Vargas?" → should refuse (La Llorona lore, wrong campaign)

#### Test Runner (`tests/accuracy/runner.py`)

- [ ] CLI script: `python -m tests.accuracy.runner --campaign "La Llorona" --provider ollama`
  - Loads the campaign content via the real `loader.py`
  - Runs each test case question through the real LLM client
  - Evaluates each response using two methods:
    1. **Keyword match**: checks `expected_contains` and `expected_absent` strings (fast, deterministic, offline)
    2. **LLM-as-judge** (optional, `--judge` flag): sends `(question, expected, actual_response)` to a second LLM call asking "Does this response correctly and only answer from the provided context? Score 0–2" — surfaces nuanced failures keyword matching misses
  - Outputs a results table: test id | pass/fail | method | notes
  - Exit code `1` if any keyword-match test fails (CI-friendly)
- [ ] `--generate` flag: given a campaign folder, use the LLM to *draft* new test cases from the campaign files and write them to the appropriate JSON — DM reviews and approves before committing
  - Prompt instructs the LLM to produce one question per character in `characters.md`, one per creature in `creatures.md`, and two boundary/refusal questions; output must conform to the schema
- [ ] Results are optionally written to `tests/accuracy/results/` as timestamped JSON for trend tracking across providers and models

---

## Documentation

- [ ] Add usage screenshots to `README.md` once the UI exists
- [ ] Document the `questions.json` override format in `README.md`
- [ ] Add a `CONTRIBUTING.md` if the project is opened up

---

## Stretch Goals (v2)

- [ ] Support multiple campaign folders — selector in the sidebar
- [ ] Vector embeddings for smarter campaign context retrieval — replace keyword heuristics in `memory.py` with semantic search over campaign files and entity state (avoid token limit issues on large campaigns)
- [ ] Player-facing view — a read-only mode showing only what players should know
- [ ] Export recap as a PDF or shareable markdown file
- [ ] Automatic session number detection from the database
- [ ] Support additional LLM providers (Cohere, Together AI, OpenRouter aggregator)
- [ ] PC initiative tracker / combat helper tab surfacing creature stat blocks from `creatures.md` inline
- [ ] Automatic entity extraction: after saving debrief answers, use the LLM to suggest NPC/location/thread updates rather than requiring manual DM review
