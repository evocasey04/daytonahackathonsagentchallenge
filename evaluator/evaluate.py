import json


REWARDS = {
    "correct_vulnerability": 5,
    "correct_file": 2,
    "correct_line": 2,
    "correct_severity": 1,
    "false_positive": -3,
    "missed_vulnerability": -5,
    "unnecessary_tool_call": -0.1,
}

WEIGHTS = {
    "detection": 0.40,
    "localisation": 0.25,
    "explanation": 0.15,
    "severity": 0.10,
    "efficiency": 0.10,
}


def load_ground_truth(challenge_dir: str) -> dict:
    with open(f"{challenge_dir}/ground_truth.json") as f:
        return json.load(f)


def evaluate(agent_answer: dict, ground_truth: dict, tool_calls_used: int = 0) -> dict:
    """
    agent_answer expects:
    {
        "vulnerability": str,
        "file": str,
        "line": int,
        "severity": str,
        "explanation": str
    }
    """
    reward = 0
    breakdown = {}

    vuln_match = agent_answer.get("vulnerability", "").lower() == ground_truth["vulnerability"].lower()
    file_match = agent_answer.get("file", "").lower() == ground_truth["file"].lower()
    line_match = abs(agent_answer.get("line", -1) - ground_truth["line"]) <= 2
    sev_match = agent_answer.get("severity", "").lower() == ground_truth["severity"].lower()
    has_explanation = bool(agent_answer.get("explanation", "").strip())

    if vuln_match:
        reward += REWARDS["correct_vulnerability"]
    else:
        reward += REWARDS["missed_vulnerability"]

    if file_match:
        reward += REWARDS["correct_file"]

    if line_match:
        reward += REWARDS["correct_line"]

    if sev_match:
        reward += REWARDS["correct_severity"]

    reward += tool_calls_used * REWARDS["unnecessary_tool_call"]

    detection_score = 1.0 if vuln_match else 0.0
    localisation_score = ((1 if file_match else 0) + (1 if line_match else 0)) / 2
    explanation_score = 1.0 if has_explanation else 0.0
    severity_score = 1.0 if sev_match else 0.0
    efficiency_score = max(0.0, 1.0 - (tool_calls_used * 0.05))

    weighted_score = (
        detection_score * WEIGHTS["detection"]
        + localisation_score * WEIGHTS["localisation"]
        + explanation_score * WEIGHTS["explanation"]
        + severity_score * WEIGHTS["severity"]
        + efficiency_score * WEIGHTS["efficiency"]
    ) * 100

    breakdown = {
        "detection": vuln_match,
        "file": file_match,
        "line": line_match,
        "severity": sev_match,
        "explanation": has_explanation,
        "tool_calls": tool_calls_used,
        "reward": round(reward, 1),
        "weighted_score": round(weighted_score, 1),
    }

    feedback = build_feedback(breakdown, ground_truth, agent_answer)

    return {**breakdown, "feedback": feedback}


def build_feedback(breakdown: dict, ground_truth: dict, agent_answer: dict) -> str:
    notes = []
    if not breakdown["detection"]:
        notes.append(f"You missed the vulnerability — it was {ground_truth['vulnerability']}.")
    if not breakdown["file"]:
        notes.append(f"Wrong file — it was in {ground_truth['file']}.")
    if not breakdown["line"]:
        notes.append(f"Line was off — actual line is {ground_truth['line']}.")
    if not breakdown["severity"]:
        notes.append(f"Severity was {ground_truth['severity']}, not {agent_answer.get('severity')}.")
    if breakdown["tool_calls"] > 10:
        notes.append("Too many tool calls — try to narrow your search earlier.")
    if not notes:
        notes.append("Perfect score — no adjustments needed.")
    return " ".join(notes)
