# PyOB — Complete Technical Documentation

> **Version**: 2.0.0 · **Last Updated**: May 2026
> **Architecture**: Python 3.12+ · Mixin-Based Package · GitHub Marketplace Action

---

## Table of Contents

1. [System Philosophy](#1-system-philosophy-constrained-surgical-autonomy)
2. [Architecture Overview](#2-architecture-overview)
3. [Module Reference](#3-module-reference)
4. [The Verification & Healing Pipeline](#4-the-verification--healing-pipeline)
5. [Symbolic Dependency Management](#5-symbolic-dependency-management)
6. [The XML Edit Engine](#6-the-xml-edit-engine)
7. [The GitHub Librarian](#7-the-github-librarian-integration)
8. [Headless & Cloud Autonomy](#8-headless--cloud-autonomy)
9. [LLM Backend & Smart Fallbacks](#9-llm-backend--smart-fallbacks)
10. [Persistence & State Vault (.pyob/)](#10-persistence--state-management)
11. [Safety & Rollback Mechanisms](#11-safety--rollback-mechanisms)
12. [Marketplace & Docker Infrastructure](#12-marketplace--docker-infrastructure)
13. [Internal Constants & Rulesets](#13-internal-constants--defaults)
14. [Operational Workflow](#14-operational-workflow)
15. [Troubleshooting](#15-troubleshooting)

---

## 1. System Philosophy: Constrained Surgical Autonomy

PyOB is an autonomous agent built on **constrained agency**. Unlike chat-based assistants that require constant prompting, PyOB is a self-driven engine that operates within a strict "Safety Cage" defined by:

1. **Surgical Patching** — Patches are applied via `<SEARCH>/<REPLACE>` blocks limited to 2-5 line anchors.
2. **Atomic Commits** — Changes are isolated in unique Git branches and submitted as PRs via the Librarian.
3. **Multi-Step Verification** — Every edit must pass a multi-layer gate (XML match → Linter → Mypy → PIR → Smoke Test).
4. **Self-Evolution** — The engine is recursive; it can identify its own logic flaws and refactor its source code.

---

## 2. Architecture Overview

### Modular Package Structure
PyOB has been heavily refactored from a monolithic script into a highly decoupled, mixin-based architecture located in `src/pyob/`.

```text
Entrance System (entrance.py, entrance_mixins.py)
├── Master loop, Librarian PR logic, Recursive Reboot Management

Review & Pipeline Orchestration (autoreviewer.py, targeted_reviewer.py)
├── Orchestrates the 6-Phase Pipeline over the codebase

Implementation & Validation Mixins (feature_mixins.py, scanner_mixins.py, evolution_mixins.py)
├── Ruff/Mypy validation, Runtime Auto-Heal, AI Proposal interpretation

XML Engine (xml_mixin.py, get_valid_edit.py)
├── Multi-strategy patch matching, strict syntax enforcement

LLM & Models (models.py, prompts_and_memory.py, prompts.py)
├── OpenRouter/Gemini streaming, Rule-based Templates, CRUD Memory

Architect HUD & Stats (dashboard_server.py, dashboard_html.py, stats_updater.py)
├── SOTA Real-time Cyberpunk Web Interface

Core Utilities (core_utils.py, pyob_launcher.py, data_parser.py)
├── Smart Sleep, Environment Detection, Config parsing
```

### System Data Flow (Cloud Service Mode)
```
[User / Schedule] ─▶ [GitHub Action] ─▶ [Docker Container]
                                              │
                    ┌─────────────────────────┴────────────────────────┐
                    │      ENTRANCE CONTROLLER (Master Loop)           │
                    │ 1. Sync Remote Main  2. Pick Target  3. Backup   │
                    └───────────┬────────────────────────────┬─────────┘
                                ▼                            ▼
                    ┌──────────────────────┐      ┌────────────────────┐
                    │ TARGETED REVIEWER    │      │    LIBRARIAN       │
                    │ (6-Phase Pipeline)   │      │ (Branch/Commit/PR) │
                    └───────────┬──────────┘      └────────────────────┘
                                ▼
                    ┌──────────────────────────────────────────────────┐
                    │           VERIFICATION & HEALING                 │
                    │ [Ruff --fix] ─▶ [Mypy] ─▶ [10s Smoke Test]      │
                    └──────────────────────────────────────────────────┘
```

---

## 3. Module Reference

### 3.1 `pyob_launcher.py` & `data_parser.py`
The environment bootstrapper. It loads the `~/.pyob_config`, configures the OS runtime, and ensures proper terminal rendering. 

### 3.2 `entrance.py` & `entrance_mixins.py`
The master orchestrator. Runs the infinite loop, manages Git lifecycles, and evaluates the `self_evolved_flag` for Hot-Reboots.

### 3.3 `targeted_reviewer.py` & `autoreviewer.py`
Ties the specialized mixins together to execute the autonomous analysis cycle on individual files or entire projects.

### 3.4 `models.py` & `prompts_and_memory.py`
Handles all interaction with the AI. `models.py` controls the OpenRouter/Gemini/Ollama hierarchy, executing the multi-model fallback logic.

### 3.5 `xml_mixin.py` & `get_valid_edit.py`
The surgical engine. Analyzes the AI's `<SEARCH>/<REPLACE>` payloads and carefully splices them into the live codebase using advanced whitespace and AST tolerance.

### 3.6 `dashboard_server.py` & `dashboard_html.py`
A modern Python HTTP server serving the Cyberpunk Architect HUD. Provides a responsive HTML/CSS dashboard with live AJAX updates powered by `stats_updater.py`.

---

## 4. The Verification & Healing Pipeline

PyOB follows a "Proactive Defense" model to ensure code stability.

### Layer 1: Atomic XML Match
Edits are binary: either every block in a response matches perfectly against the live file, or the entire iteration is discarded.

### Layer 2: Syntactic "Broom"
1. **`ruff format`**: Normalizes all whitespace.
2. **`ruff check --fix`**: Automatically clears unused imports and variables without costing AI tokens.
3. **Remaining Errors**: Grouped by file and fed into the AI for surgical repair via the Post-Implementation Repair (PIR) loop.

### Layer 3: Runtime Smoke Test
- Locates the project entry point.
- Launches the process for 10 seconds.
- **Auto-Dependency Locking**: If a `ModuleNotFoundError` is detected, PyOB runs `pip install` and immediately updates `requirements.txt`.

---

## 5. Symbolic Dependency Management

### `SYMBOLS.json` Ledger
PyOB maintains a mapping of **Definitions** (where a function/class is born) to **References** (where it is used).

### Symbolic Ripple Engine
1. When a file is edited, the engine identifies changed symbols.
2. It looks up the ledger to see if those symbols are "Definitions."
3. It finds all "References" in other files.
4. **Cascade Queue:** Impacted files are prioritized for the next iteration, with the original change-diff provided as mandatory context.

---

## 6. The XML Edit Engine

### Multi-Strategy Matching
`xml_mixin.py` attempts 5 strategies per block:
1. **Exact** (Literal string match)
2. **Stripped** (Newline tolerance)
3. **Normalized** (Comment/Whitespace stripping)
4. **Regex Fuzzy** (Indentation tolerance)
5. **Robust Line Match** (Content-only line comparison)

### Smart Indent Alignment
The engine detects the target line's indentation and re-aligns the AI's `<REPLACE>` block to match, preventing the "Unexpected Indentation" errors common in Python agents.

---

## 7. The GitHub Librarian Integration

PyOB acts as a professional developer through the **Librarian** logic:

- **Isolated Branches:** Every change is pushed to a unique branch (`pyob-evolution-vX...`).
- **Bot Identity:** Commits are attributed to `pyob-bot` using `BOT_GITHUB_TOKEN`.
- **Automated PRs:** Uses the GitHub CLI (`gh`) to open Pull Requests targeting `main`.
- **PR Body:** Includes the AI's `<THOUGHT>` process as the PR description for human review.

---

## 8. Headless & Cloud Autonomy

PyOB detects when it is running in **GitHub Actions** (via `GITHUB_ACTIONS=true`):

- **Auto-Approval:** Bypasses "Press ENTER to apply" prompts.
- **Non-TTY Safety:** Skips all terminal UI manipulations to prevent crashes.
- **Cloud Tunneling:** Starts a background **Pinggy** tunnel to provide a public URL for the dashboard HUD directly to your phone.

---

## 9. LLM Backend & Smart Fallbacks

### OpenRouter Multi-Model Pivot
PyOB defaults to the **OpenRouter API** with highly sophisticated per-model cooldowns configured in `models.py`. 
It prioritizes heavy-hitting models like **DeepSeek V4 Flash**, **Llama 3.3 70B**, and **Qwen 2.5 Coder 32B**. 
If a specific model stalls, 404s, or hits a rate limit, PyOB immediately places *only that model* on cooldown and seamlessly pivots to the next OpenRouter model in the list, eventually hitting the `openrouter/free` auto-router.

### Gemini API Rotation
If the entire OpenRouter provider goes offline, PyOB falls back to a massive pool of up to 10 Gemini API keys (`GEMINI_API_KEYS`). It actively tracks which keys are rate-limited and rotates through them on the fly.

### Smart Sleep Backoff
When all keys across all providers are exhausted, the engine calculates:
`sleep_duration = min(key_cooldowns) - current_time`
The bot "naps" for the exact number of seconds until the very first key is freed up, ensuring zero API spam while preserving Cloud Runner minutes.

---

## 10. Persistence & State Management (.pyob/)

All project metadata is stored in the hidden `.pyob/` vault to prevent root directory clutter.

| File | Purpose |
|---|---|
| `.pyob/ANALYSIS.md` | Persistent map used by the AI to select targets. |
| `.pyob/SYMBOLS.json` | The symbolic dependency graph. |
| `.pyob/MEMORY.md` | Transactional AI memory; refactored every 2 iterations to prevent context bloat. |
| `.pyob/HISTORY.md` | Detailed ledger of applied patches. |

---

## 11. Safety & Rollback Mechanisms

- **External Safety Pods:** Before editing an "Engine File", PyOB shelters a copy of the current source in `~/Documents/PYOB_Backups/`.
- **Workspace Backup:** Every iteration starts with an in-memory snapshot of the entire project.
- **Atomic Rollback:** If any verification layer (Linter, Mypy, or Runtime) fails 3 times, the entire workspace is immediately restored to the pristine backup.

---

## 12. Marketplace & Docker Infrastructure

### Marketplace Action
PyOB is a containerized GitHub Action (`action.yml`). It uses a `Dockerfile` based on `python:3.12-slim` with `git`, `curl`, and `gh` pre-installed.

### Docker Environment
The Docker container maps the user's repository to `/github/workspace`, allowing PyOB to operate on the files identically to a local CLI tool without permission headaches.

---

## 13. Internal Constants & Rulesets

### Mandatory Import Rule (Rule 7)
The AI is strictly prohibited from using the `src.` prefix in imports.
- **Correct:** `from pyob.core_utils import ...`
- **Incorrect:** `from src.pyob.core_utils import ...`

### Indentation Guard (Rule 6)
Deletions must leave a placeholder comment (e.g., `# [Logic moved to new module]`) to maintain Python's indentation integrity and AST structure.

---

## 14. Operational Workflow

1. **Remote Sync:** Pull latest merges from GitHub.
2. **Genesis / Update:** Build or refresh `ANALYSIS.md` and `SYMBOLS.json`.
3. **Targeting:** Select file via AI or the `Cascade Queue`.
4. **Pipeline:** Scan → Propose → Verify → Auto-Heal.
5. **Librarian:** Push Branch → Open PR.
6. **Self-Evolution:** If engine changed, verify importability and Hot-Reboot.

---

## 15. Troubleshooting

### `ModuleNotFoundError: No module named 'src'`
**Cause:** AI incorrectly added `src.` to an import statement.
**Fix:** Remove the `src.` prefix. Ensure `pyproject.toml` is installed via `pip install -e .`.

### `EOFError: EOF when reading a line`
**Cause:** PyOB tried to call `input()` in a cloud environment.
**Fix:** Ensure `sys.stdin.isatty()` checks are present in the launcher.

### `termios.error: Inappropriate ioctl for device`
**Cause:** `get_user_approval` tried to manipulate a non-existent keyboard.
**Fix:** The "Headless Auto-Approval" logic in `core_utils.py` handles this.

---
> **PyOB** — The engine that builds itself, with surgical precision. 🦅
---
