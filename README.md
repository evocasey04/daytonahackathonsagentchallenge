# CyberAgent Arena

An AI security agent that learns to find vulnerabilities in code. Runs inside isolated Daytona sandboxes, gets scored by an evaluator, and improves its strategy across generations. Three agent variants compete in parallel — the strongest gets promoted.

---

## Person 1 — Challenges + Evaluator

**Goal:** Create the vulnerable repos and the scoring system.

- Create 5 small vulnerable repositories, one per vulnerability type:
  - SQL Injection
  - Cross-Site Scripting (XSS)
  - Command Injection
  - Path Traversal
  - Hardcoded Credentials
- Each repo has one vulnerable file and a hidden `ground_truth.json` containing: vulnerability type, file, line number, severity
- Build `evaluator/evaluate.py` — takes the agent's answer and compares it against ground truth
- Scoring: +5 correct vulnerability, +2 correct file, +2 correct line, +1 correct severity, -3 false positive, -5 missed, -0.1 per unnecessary tool call
- Final score formula: 40% detection + 25% localisation + 15% explanation + 10% severity + 10% efficiency
- Return a feedback string explaining what the agent got wrong so it can improve next round

---

## Person 2 — Agent + Daytona Integration

**Goal:** Build the agent that investigates repos inside Daytona sandboxes.

- `sandbox.py` — create a fresh Daytona sandbox per run, upload the challenge repo into it, run commands, destroy it after
- `tools.py` — implement four tools the agent can call inside the sandbox:
  - `list_files` — list all files in the repo
  - `read_file` — read a specific file
  - `search_code` — grep for a pattern across the repo
  - `run_static_analysis` — run bandit inside the sandbox and return JSON results
- `agent.py` — LLM agent loop using Claude with tool use:
  - **Baseline variant** — no tools, reasons from prompt alone
  - **Tool Agent variant** — has access to all four tools
  - **Self-Improving variant** — receives reward + feedback from previous round and adjusts its strategy
- Each run returns: the agent's answer (vulnerability, file, line, severity, explanation) and number of tool calls used

---

## Person 3 — Orchestrator + Frontend + Demo

**Goal:** Wire everything together, build the React dashboard, run the arena, prepare the demo.

### Backend (first half)
- `main.py` — runs all three agent variants across all five challenges using a thread pool (one Daytona sandbox per agent per challenge)
- Runs 3 generations — each generation passes the previous round's feedback back into the self-improving agent
- Saves all results to `results.json` as they come in
- Add a small Flask/FastAPI server (`server.py`) with two endpoints:
  - `POST /run` — triggers `main.py` and streams progress
  - `GET /results` — returns current `results.json`

### Frontend (second half)
- React app in `dashboard/` — single page, no routing needed
- Three panels:
  - **Leaderboard** — bar chart showing Baseline vs ToolAgent vs Self-Improving scores per generation
  - **Agent Activity Log** — live scrolling feed of what each agent is doing (sandbox created, tool calls, answer submitted, reward received)
  - **Challenge Results Table** — per challenge, per variant: ✓/✗ for detection, file, line, severity
- Polls `GET /results` every 2 seconds to update in real time
- Stack: React + Vite, TailwindCSS for styling, Recharts for the score graph
- Keep it to one file (`App.jsx`) if time is tight — ship something that works over something that looks perfect

### Demo
- Owns the demo — clean run from scratch before 4:30 PM
- Show: sandboxes spinning up → agent activity → generation 1 vs 3 score comparison → leaderboard with winner highlighted

---

## Daytona's Role

Every agent run gets its own isolated Daytona sandbox — the vulnerable code never runs on your machine. Sandboxes are created in ~90ms and destroyed immediately after the scan. This lets us run all three agent variants simultaneously without them interfering with each other.

---

## Setup

```bash
pip install -r requirements.txt
```

```
DAYTONA_API_KEY=your_key
ANTHROPIC_API_KEY=your_key
```

```bash
python main.py