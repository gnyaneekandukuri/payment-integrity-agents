# Payment integrity agents

A working prototype of how AI agents can support a health plan's payment integrity team, from an unusual billing pattern to a decision a person can explain and defend.

**All people, plans, hospitals, claims and medical records here are fictional.** The clinical cases have not been reviewed by a clinician. Nothing here is medical or billing advice.

## The problem
Monitoring can flag unusual billing. Deciding whether it's justified still means people working manually at every step: analysts dig through claims data to understand why a pattern exists, and clinical reviewers read medical records claim by claim. Every finding has to be explainable to the provider and hold up on appeal.

## What the prototype does
| Step | Who | What happens |
|---|---|---|
| **Finding leads** | Fixed rules | A monitoring job compares every hospital with its peers using three methods: written rules, peer profiling (no pattern named in advance) and change detection on each hospital's own history. Leads caught by more methods rank higher. |
| **Root-cause analysis** | Pattern Investigation Agent → analyst | For a lead, the agent tests the legitimate explanations (sicker patients, transfers, better documentation and more) against cited metrics, and marks each as supported, supported in part, weakened or unresolved. The analyst confirms, reviews a hypothetical sensitivity table, and approves a targeted records review. |
| **Record review** | Clinical Evidence Agent → clinical reviewer | When records arrive, the agent reads them, records evidence with exact quotes, flags gaps and conflicts, and drafts a plain-language finding (supported / not supported / unable to determine). When the record can't answer, it drafts a targeted records request. The reviewer decides. |

## Design principles
- **Agents only where the work is open-ended** (reading records, testing explanations). Detection, scoring and checks are fixed code.
- **No invented evidence.** Every quote is checked against the source page; numbers come from fixed calculations the agent must cite.
- **Missing stays missing.** Undocumented values are never treated as normal.
- **People decide.** No tool exists to deny, regroup, price or send anything.
- **Traceable and replayable.** Every agent step is logged, and saved runs replay without network access.

## How it was checked
Seven test records with known answers, each run three times: the agent reached the right conclusion every time, and every citation was valid. The failures found along the way, and how each became a rule in code, are written up in [`docs/EVALUATION.md`](docs/EVALUATION.md).

## Stack
Python (FastAPI, SQLite, PyMuPDF), a plain tool-calling loop over the OpenAI API (no agent framework), React + Vite + Tailwind.

## Run it
Requirements: Python 3.12+ with [uv](https://docs.astral.sh/uv/), and Node 20+.

**An OpenAI API key is only needed for live agent runs.** Every agent step also has a **Replay** option that plays back a saved run, so you can explore the whole flow with no key and no network. For live runs, copy `.env.example` to `.env` and set `OPENAI_API_KEY` and `OPENAI_MODEL` (built and tested with `gpt-5.4-mini`).

**macOS / Linux** (two terminals):
```bash
# terminal 1: build the fictional data and start the API
cd backend
uv sync
uv run python -m tools.demo_reset
uv run uvicorn app.main:app --port 8765

# terminal 2: start the app
cd frontend
npm install
npx vite --port 5199
```

**Windows (PowerShell):**
```powershell
cd backend; uv sync; cd ..\frontend; npm install; cd ..
.\reset.ps1      # build the fictional data, start both servers, open the browser
.\stop.ps1       # stop both servers
```

Then open http://localhost:5199. Start on **Leads**, open the Riverside lead, and run or replay the investigation; then open the **Clinical review queue**. Records to upload for the two claims awaiting records are in `demo_uploads/` (Samuel Adeyemi → Metro Regional; Joseph Kim → Crestview Regional). Running `tools.demo_reset` again returns everything to the starting state.

## Checks (from `backend\`)
| Command | What it proves |
|---|---|
| `uv run python -m seed.check` | Scenario numbers are computed from the claims; key quotes exist in the records |
| `uv run python -m tools.evaluate --runs 3` | Agent behaviour against the answer keys (live) |
| `uv run python -m tools.offline_check` | The whole flow runs with no model access (stop the API first) |

## Design documents
`docs/design/` has the current-state user journeys, the product flow and the system design (open in [draw.io](https://app.diagrams.net)).
