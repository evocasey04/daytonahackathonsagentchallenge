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

## Person 3 — Orchestrator + Demo

**Goal:** Wire everything together, run the arena, prepare the demo.

- `main.py` — runs all three agent variants across all five challenges using a thread pool (one Daytona sandbox per agent per challenge)
- Runs 3 generations — each generation passes the previous round's feedback back into the self-improving agent
- Prints a leaderboard after each generation showing scores per variant
- Saves all results to `results.json`
- Owns the demo — clean run from scratch before 4:30 PM showing score improvement across generations and three sandboxes running in parallel

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