# VulnHunter — Sandbox-Isolated Code Vulnerability Scanner

An AI agent that spins up an isolated [Daytona](https://daytona.io) sandbox for every scan, identifies real security vulnerabilities in a GitHub repository, and uses an LLM to eliminate false positives — returning only confirmed findings with file, line, type, and severity.

---

## What It Does

1. **Accepts a GitHub repo URL** as input
2. **Spins up a fresh Daytona sandbox** — the target code never touches your machine
3. **Clones the repo and runs two scanners inside the sandbox:**
   - `bandit` — Python-specific AST-based vulnerability detection
   - `semgrep` — multi-language static analysis (OWASP, CWE rulesets)
4. **Feeds raw results to Claude** to cross-reference findings, remove false positives, and rank by real exploitability
5. **Outputs a structured report** — vulnerability type, exact file + line, severity (CRITICAL / HIGH / MEDIUM / LOW), and a one-line explanation
6. **Deletes the sandbox** — nothing persists after the scan

---

## Why Sandboxes?

Running untrusted code through a scanner is itself a risk. Malicious repos can exploit scanner bugs or contain files that execute on clone. Daytona spins up a fully isolated environment in ~90ms — the scanner runs there, not on your machine.

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Set environment variables

```bash
# Windows PowerShell
$env:DAYTONA_API_KEY = "your_daytona_api_key"
$env:ANTHROPIC_API_KEY = "your_anthropic_api_key"  # optional — skips LLM dedup if not set
```

Get your Daytona API key at https://app.daytona.io → Settings → API Keys

### 3. Run

```bash
python agent.py --repo https://github.com/someuser/somerepo
```

---

## Output Example

```
=== VulnHunter Report ===
Repo: https://github.com/example/vulnerable-flask-app
Sandbox: sandbox-abc123 (deleted after scan)

[CRITICAL] SQL Injection
  File: app/db.py  Line: 42
  Raw user input passed directly to execute() — attacker can read/write entire DB.

[HIGH] Hardcoded Secret
  File: config/settings.py  Line: 7
  AWS secret key hardcoded in source. Rotate immediately.

[HIGH] Command Injection
  File: utils/runner.py  Line: 88
  os.system() called with unsanitised user input — arbitrary command execution.

[MEDIUM] Insecure Deserialization
  File: api/handlers.py  Line: 134
  pickle.loads() on untrusted data — can lead to remote code execution.

4 findings. 0 false positives filtered.
```

---

## Architecture

```
agent.py
  └── Daytona.create()          # fresh sandbox per scan
       ├── git clone <repo>
       ├── pip install bandit semgrep
       ├── bandit -r . -f json
       ├── semgrep --config=auto --json
       └── Daytona.delete()     # cleanup

  └── Claude (optional)
       ├── Cross-references bandit + semgrep findings
       ├── Filters scanner noise / false positives
       └── Returns ranked, deduplicated findings
```

---

## Files

| File | Purpose |
|------|---------|
| `agent.py` | Main scanner agent |
| `requirements.txt` | Python dependencies |
| `test_sandbox.py` | Quick Daytona connectivity test |

---

## Hackathon

Built at **Give(a)Go × Daytona HackSprint**, Dublin, August 2026.