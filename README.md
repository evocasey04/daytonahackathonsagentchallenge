# CyberAgent Arena

An AI security agent that learns to find vulnerabilities in code. It runs inside isolated Daytona sandboxes, gets scored by an evaluator, and improves its strategy across generations through continuous learning.

## Quick Start

### 1. Install Dependencies

```bash
pip install -r requirements.txt
cd dashboard && npm install && cd ..
```

### 2. Set Environment Variables

Create a `.env` file or export directly:

```bash
export DAYTONA_API_KEY="your_daytona_key"
export GEMINI_API_KEY="your_gemini_key"
```

Get your keys:
- **Daytona:** https://app.daytona.io
- **Gemini:** https://aistudio.google.com/app/apikey (free tier)

### 3. Start the System

```bash
# Terminal 1: Backend
python server.py

# Terminal 2: Frontend
cd dashboard && npm run dev
```

### 4. Open the Dashboard

Go to **http://localhost:5173** and click **Run** to start the arena.

---

## How It Works

### The Challenge
5 vulnerable Python apps, each with a hidden security flaw:
- SQL Injection
- Cross-Site Scripting (XSS)
- Command Injection
- Path Traversal
- Hardcoded Credentials

### The Agents
Three AI variants compete to find vulnerabilities:

| Variant | Description | Tools |
|---------|-------------|-------|
| **Baseline** | Reasons from general knowledge only | None |
| **Tool Agent** | Investigates code inside sandbox | list_files, read_file, search_code, run_static_analysis |
| **Self-Improving** | Learns from feedback each generation | Same + feedback loop |

### The Process
1. **Sandbox Creation** — Daytona spins up an isolated container (~1 sec)
2. **Code Upload** — Vulnerable app uploaded (ground truth hidden from agent)
3. **Investigation** — Agent uses tools to analyze the code
4. **Report** — Agent outputs: `{vulnerability_type, file, line, severity, explanation}`
5. **Scoring** — Evaluator compares to ground truth
6. **Learning** — Feedback saved for next generation

### Scoring Formula
- +5 correct vulnerability type
- +2 correct file
- +2 correct line (±3 lines tolerance)
- +1 correct severity
- -3 false positive
- -0.1 per extra tool call

**Final Score:** 40% detection + 25% localization + 15% explanation + 10% severity + 10% efficiency

---

## Continuous Learning

The agent learns across sessions via `strategies.json`:

```json
{
  "SQL Injection": {
    "strategy": "Look for f-strings in database queries...",
    "score": 8.7
  }
}
```

When an agent scores ≥7, its successful strategy is saved. Future runs load these patterns into the system prompt, making the agent smarter over time.

---

## Project Structure

```
├── challenges/           # 5 vulnerable apps + ground_truth.json
│   ├── sql_injection/
│   ├── xss/
│   ├── command_injection/
│   ├── path_traversal/
│   └── hardcoded_secret/
├── agent/
│   ├── agent.py          # LLM agent loop (Gemini)
│   ├── sandbox.py        # Daytona integration
│   └── tools.py          # 4 investigation tools
├── evaluator/
│   └── evaluate.py       # Scoring system
├── dashboard/            # React frontend
├── server.py             # Flask API
├── main.py               # Arena orchestrator
├── strategies.json       # Learned patterns (persistent)
└── results.json          # Run results
```

---

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/run` | POST | Start arena run |
| `/results` | GET | Get current results |

---

## Tech Stack

- **AI:** Google Gemini (gemini-flash-lite)
- **Sandboxing:** Daytona
- **Backend:** Python, Flask
- **Frontend:** React, Vite, TailwindCSS, Recharts
- **Evaluation:** Custom scoring engine

---

## Demo Results

Example scores from a successful run:

| Challenge | Tool Agent Score |
|-----------|-----------------|
| SQL Injection | 8.7/10 |
| Command Injection | 8.7/10 |
| XSS | 7.4/10 |
| Path Traversal | 3.0/10 |
| Hardcoded Secret | 2.0/10 |

The Tool Agent significantly outperforms the Baseline (avg 1.1/10) by using its investigation tools.

---

## Team

Built for the Daytona Hackathon 2026.
