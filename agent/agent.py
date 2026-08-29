import json
import anthropic
from agent.tools import TOOL_DEFINITIONS, dispatch
from agent.sandbox import create_sandbox, destroy_sandbox

SYSTEM_PROMPT = """You are a security researcher investigating a code repository for vulnerabilities.
Use the available tools to inspect files, search for patterns, and run static analysis.
Be efficient — minimise tool calls. Once you are confident, submit your finding as JSON.

Your final answer MUST be a JSON object in this exact format:
{
  "vulnerability": "<type e.g. SQL Injection>",
  "file": "<filename>",
  "line": <line number as integer>,
  "severity": "<critical|high|medium|low>",
  "explanation": "<one sentence explaining the vulnerability>"
}

Do not include any text outside the JSON in your final answer."""


def run_agent(challenge_dir: str, variant: str = "self_improving", feedback: str = "", history: list = None) -> dict:
    """
    Run the agent on a challenge. Returns the raw answer dict and tool call count.

    variant: "baseline" | "tool_agent" | "self_improving"
    feedback: previous round feedback string (used by self_improving)
    history: list of previous (score, feedback) tuples for self_improving
    """
    client = anthropic.Anthropic()
    sandbox = create_sandbox(challenge_dir)
    tool_call_count = 0

    try:
        system = _build_system_prompt(variant, feedback, history)
        messages = [{"role": "user", "content": "Investigate the repository and find the security vulnerability."}]

        while True:
            kwargs = {"model": "claude-opus-4-5", "max_tokens": 1024, "system": system, "messages": messages}

            if variant != "baseline":
                kwargs["tools"] = TOOL_DEFINITIONS

            response = client.messages.create(**kwargs)

            if response.stop_reason == "end_turn":
                answer_text = _extract_last_text(response)
                answer = _parse_answer(answer_text)
                return {"answer": answer, "tool_calls": tool_call_count}

            if response.stop_reason == "tool_use":
                tool_results = []
                for block in response.content:
                    if block.type == "tool_use":
                        tool_call_count += 1
                        result = dispatch(sandbox, block.name, block.input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block.id,
                            "content": result,
                        })

                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results})
                continue

            break

    finally:
        destroy_sandbox(sandbox)

    return {"answer": {}, "tool_calls": tool_call_count}


def _build_system_prompt(variant: str, feedback: str, history: list) -> str:
    prompt = SYSTEM_PROMPT

    if variant == "baseline":
        prompt += "\n\nYou do not have access to tools. Reason from general knowledge only."

    if variant == "self_improving" and feedback:
        prompt += f"\n\nFeedback from your last attempt: {feedback}"

    if variant == "self_improving" and history:
        scores = [h["score"] for h in history]
        prompt += f"\n\nYour scores across previous rounds: {scores}. Adjust your strategy to improve."

    return prompt


def _extract_last_text(response) -> str:
    for block in reversed(response.content):
        if hasattr(block, "text"):
            return block.text
    return ""


def _parse_answer(text: str) -> dict:
    try:
        start = text.index("{")
        end = text.rindex("}") + 1
        return json.loads(text[start:end])
    except (ValueError, json.JSONDecodeError):
        return {}
