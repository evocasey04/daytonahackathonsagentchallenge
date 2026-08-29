import json
import os
import requests
from pathlib import Path
from agent.tools import GEMINI_TOOLS, dispatch
from agent.sandbox import create_sandbox, destroy_sandbox

SYSTEM_PROMPT = """You are a security researcher investigating a code repository for vulnerabilities.
Use the available tools to inspect files, search for patterns, and run static analysis.
Be efficient — minimise tool calls. Once you are confident, submit your finding as JSON.

Your final answer MUST be a JSON object in this exact format:
{
  "vulnerability_type": "<type e.g. SQL Injection>",
  "file": "<filename>",
  "line": <line number as integer>,
  "severity": "<critical|high|medium|low>",
  "explanation": "<one sentence explaining the vulnerability>"
}

Do not include any text outside the JSON in your final answer."""

MODEL = "gemini-flash-lite-latest"
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/{MODEL}:generateContent"
MAX_TOOL_CALLS = 20

STRATEGIES_FILE = Path(__file__).parent.parent / "strategies.json"


def load_strategies() -> dict:
    """Load learned strategies from disk."""
    if STRATEGIES_FILE.exists():
        with open(STRATEGIES_FILE, "r") as f:
            return json.load(f)
    return {}


def save_strategy(vuln_type: str, strategy: str, score: float):
    """Save a successful strategy for a vulnerability type."""
    strategies = load_strategies()

    # Only save if score is good (>= 7) or better than existing
    existing = strategies.get(vuln_type, {})
    if score >= 7 and score > existing.get("score", 0):
        strategies[vuln_type] = {
            "strategy": strategy,
            "score": score
        }
        with open(STRATEGIES_FILE, "w") as f:
            json.dump(strategies, f, indent=2)
        print(f"  [LEARNED] Saved strategy for {vuln_type} (score: {score})")


def run_agent(challenge_dir: str, variant: str = "self_improving", feedback: str = "", history: list = None) -> dict:
    """
    Run the agent on a challenge. Returns the raw answer dict and tool call count.

    variant: "baseline" | "tool_agent" | "self_improving"
    feedback: previous round feedback string (used by self_improving)
    history: list of previous (score, feedback) tuples for self_improving
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    sandbox = create_sandbox(challenge_dir)
    tool_call_count = 0

    try:
        system = _build_system_prompt(variant, feedback, history)
        contents = [
            {"role": "user", "parts": [{"text": "Investigate the repository and find the security vulnerability."}]}
        ]

        while True:
            payload = {
                "system_instruction": {"parts": [{"text": system}]},
                "contents": contents,
            }

            if variant != "baseline":
                payload["tools"] = GEMINI_TOOLS

            response = requests.post(
                API_URL,
                headers={
                    "Content-Type": "application/json",
                    "X-goog-api-key": api_key,
                },
                json=payload,
                timeout=120,
            )

            if response.status_code != 200:
                print(f"API error: {response.status_code} - {response.text}")
                break

            data = response.json()

            if not data.get("candidates"):
                break

            candidate = data["candidates"][0]
            parts = candidate.get("content", {}).get("parts", [])

            function_calls = [p["functionCall"] for p in parts if "functionCall" in p]

            if not function_calls:
                answer_text = ""
                for p in parts:
                    if "text" in p:
                        answer_text += p["text"]
                answer = _parse_answer(answer_text)
                return {"answer": answer, "tool_calls": tool_call_count}

            if tool_call_count >= MAX_TOOL_CALLS:
                break

            contents.append({"role": "model", "parts": parts})

            function_responses = []
            for fc in function_calls:
                tool_call_count += 1
                args = fc.get("args", {})
                result = dispatch(sandbox, fc["name"], args)
                function_responses.append({
                    "functionResponse": {
                        "name": fc["name"],
                        "response": {"result": result}
                    }
                })

            contents.append({"role": "user", "parts": function_responses})

    finally:
        destroy_sandbox(sandbox)

    return {"answer": {}, "tool_calls": tool_call_count}


def _build_system_prompt(variant: str, feedback: str, history: list) -> str:
    prompt = SYSTEM_PROMPT

    # Load learned strategies for all variants except baseline
    if variant != "baseline":
        strategies = load_strategies()
        if strategies:
            prompt += "\n\n## Learned Patterns from Previous Sessions:\n"
            for vuln_type, data in strategies.items():
                prompt += f"- {vuln_type}: {data['strategy']}\n"

    if variant == "baseline":
        prompt += "\n\nYou do not have access to tools. Reason from general knowledge only."

    if variant == "self_improving" and feedback:
        prompt += f"\n\nFeedback from your last attempt: {feedback}"

    if variant == "self_improving" and history:
        scores = [h["score"] for h in history]
        prompt += f"\n\nYour scores across previous rounds: {scores}. Adjust your strategy to improve."

    return prompt


def _parse_answer(text: str) -> dict:
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        return {}
