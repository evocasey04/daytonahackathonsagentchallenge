# CyberAgent Arena

An AI security agent that learns to find vulnerabilities in code. It investigates deliberately vulnerable repositories inside isolated Daytona sandboxes, gets scored by an automated evaluator, and improves its strategy across generations. Multiple agent variants run in parallel — the strongest gets promoted.

---

## The Pitch

> "We built a cybersecurity agent that learns from its mistakes. It investigates vulnerable code inside isolated Daytona sandboxes, gets rewarded for finding real vulnerabilities, and improves its investigation strategy over repeated experiments."

---

## How It Works

1. **Challenges** — 5 small vulnerable repositories (SQL injection, XSS, command injection, path traversal, hardcoded secrets). Each has a hidden `ground_truth.json`.
2. **Daytona sandbox** — every agent run gets its own fresh, isolated sandbox spun up in ~90ms. Sandbox is destroyed after the run.
3. **Agent** — uses LLM + tools (`list_files`, `read_file`, `search_code`, `run_static_analysis`) to investigate the repo and submit a vulnerability report.
4. **Evaluator** — compares the agent's report against ground truth and returns a reward score.
5. **Feedback loop** — reward + feedback is passed back to the agent so it can adjust its investigation strategy next round.
6. **Parallel arena** — three agent variants (Baseline, ToolAgent, Self-Improving) run simultaneously, each in its own Daytona sandbox.
7. **Dashboard** — live React UI showing sandbox activity, scores per generation, and agent comparison.

---

## Reward Scoring

| Behaviour | Points |
|---|---|
| Correct vulnerability type | +5 |
| Correct file | +2 |
| Correct line | +2 |
| Correct severity | +1 |
| False positive | -3 |
| Missed vulnerability | -5 |
| Unnecessary tool call | -0.1 |

**Score = 40% detection + 25% localisation + 15% explanation + 10% severity + 10% efficiency**

---

## Daytona Architecture

```
          CyberAgent Arena
                 │
   ┌─────────────┼─────────────┐
   ↓             ↓             ↓
Sandbox 1     Sandbox 2     Sandbox 3
 Baseline      ToolAgent    Self-Improving
   │             │             │
 Agent          Agent         Agent
   └─────────────┼─────────────┘
                 ↓
             Evaluator
                 ↓
             Dashboard
```

Each sandbox is created fresh per run via `daytona.create()` and deleted after — isolated, reproducible, and disposable.

---

## Project Structure

```
/
├── challenges/                  # Person 1
│   ├── sql_injection/           # Vulnerable repo + ground truth
│   ├── xss/
│   ├── command_injection/
│   ├── path_traversal/
│   └── hardcoded_secret/
├── evaluator/                   # Person 1
│   └── evaluate.py              # Scores agent answer vs ground truth
├── agent/                       # Person 2
│   ├── sandbox.py               # Daytona create/run/destroy
│   ├── tools.py                 # list_files, read_file, search_code, run_static_analysis
│   └── agent.py                 # LLM agent loop + feedback/self-improvement
├── dashboard/                   # Person 3
│   └── (React app)              # Live scores, sandbox activity, generation graph
├── main.py                      # Person 3 — orchestrator, runs arena
└── requirements.txt
```

---

## Team Split

### Person 1 — Challenges + Evaluator
- Create the 5 vulnerable challenge repos with realistic vulnerable code
- Write `ground_truth.json` for each (vulnerability, file, line, severity)
- Build `evaluator/evaluate.py` — takes agent answer + ground truth, returns scored result

### Person 2 — Agent + Daytona Integration
- Wire up Daytona: `sandbox.py` — create sandbox, upload challenge, exec commands, destroy
- Build `tools.py` — `list_files`, `read_file`, `search_code`, `run_static_analysis` (runs bandit inside sandbox)
- Build `agent.py` — LLM loop that uses tools, submits report, receives reward, updates strategy

### Person 3 — Orchestrator + Dashboard
- `main.py` — runs all three agent variants in parallel using `asyncio` + Daytona
- React dashboard — generation score graph, live agent activity log, challenge results table
- Demo prep — clean run from scratch before 4:30 PM

---

## Setup

```bash
pip install -r requirements.txt
```

```powershell
$env:DAYTONA_API_KEY = "your_key"      # https://app.daytona.io → Settings → API Keys
$env:ANTHROPIC_API_KEY = "your_key"    # https://console.anthropic.com
```

```bash
python main.py
```

---

## Demo Flow (2 min)

1. Show dashboard. "Security agents are hard to evaluate objectively. So we built an arena."
2. Click **Run Arena** — three Daytona sandboxes spin up live.
3. Show agent activity log: `READ app.py → SEARCH "query" → FOUND SQL injection → Score: +10`
4. Show generation 1 → 5 score improvement graph.
5. Show three agents running in parallel, scores updating in real time.
6. "The best agent gets promoted. The weak ones are killed. That's the loop."

---

Built at **Give(a)Go × Daytona HackSprint**, Dublin, August 2026.