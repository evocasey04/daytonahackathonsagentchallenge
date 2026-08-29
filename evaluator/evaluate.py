"""
Evaluator for CyberAgent Arena

Compares agent findings against ground truth and produces a detailed score.

Scoring breakdown:
  - Detection:     +5 correct vulnerability type, -5 missed, -3 false positive
  - Localisation:  +2 correct file, +2 correct line (within 3 lines tolerance)
  - Severity:      +1 correct severity
  - Efficiency:    -0.1 per tool call beyond minimum (2 calls considered baseline)

Final score formula:
  40% detection + 25% localisation + 15% explanation + 10% severity + 10% efficiency
"""

import json
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class AgentFinding:
    vulnerability_type: str
    file: str
    line: int
    severity: str
    explanation: str = ""


@dataclass
class GroundTruth:
    vulnerability_type: str
    file: str
    line: int
    severity: str
    description: str = ""


@dataclass
class EvaluationResult:
    detection_score: float = 0.0
    localisation_score: float = 0.0
    explanation_score: float = 0.0
    severity_score: float = 0.0
    efficiency_score: float = 0.0

    total_score: float = 0.0
    max_possible: float = 10.0

    feedback: list = field(default_factory=list)

    correct_vuln_type: bool = False
    correct_file: bool = False
    correct_line: bool = False
    correct_severity: bool = False

    def to_dict(self) -> dict:
        return {
            "detection_score": self.detection_score,
            "localisation_score": self.localisation_score,
            "explanation_score": self.explanation_score,
            "severity_score": self.severity_score,
            "efficiency_score": self.efficiency_score,
            "total_score": self.total_score,
            "max_possible": self.max_possible,
            "feedback": self.feedback,
            "correct_vuln_type": self.correct_vuln_type,
            "correct_file": self.correct_file,
            "correct_line": self.correct_line,
            "correct_severity": self.correct_severity,
        }


VULN_TYPE_ALIASES = {
    "sql injection": ["sqli", "sql-injection", "sql_injection", "sql"],
    "cross-site scripting (xss)": ["xss", "cross-site scripting", "cross site scripting", "stored xss", "reflected xss"],
    "command injection": ["cmd injection", "os command injection", "rce", "command_injection", "cmd_injection", "shell injection"],
    "path traversal": ["directory traversal", "lfi", "local file inclusion", "path_traversal", "directory_traversal", "../"],
    "hardcoded credentials": ["hardcoded secret", "hardcoded secrets", "hardcoded_credentials", "hardcoded_secret", "secret leak", "credential leak", "api key exposure"],
}


def normalize_vuln_type(vuln_type: str) -> str:
    """Normalize vulnerability type to canonical form."""
    vuln_lower = vuln_type.lower().strip()

    for canonical, aliases in VULN_TYPE_ALIASES.items():
        if vuln_lower == canonical or vuln_lower in aliases:
            return canonical

    return vuln_lower


def normalize_severity(severity: str) -> str:
    """Normalize severity to canonical form."""
    severity_map = {
        "critical": "critical",
        "crit": "critical",
        "high": "high",
        "medium": "medium",
        "med": "medium",
        "moderate": "medium",
        "low": "low",
        "info": "low",
        "informational": "low",
    }
    return severity_map.get(severity.lower().strip(), severity.lower().strip())


def evaluate_explanation(explanation: str, ground_truth: GroundTruth) -> tuple[float, list[str]]:
    """
    Score the explanation quality (0-1 scale).
    Checks for key concepts that should be mentioned.
    """
    feedback = []
    score = 0.0

    if not explanation or len(explanation.strip()) < 10:
        feedback.append("Explanation is missing or too brief")
        return 0.0, feedback

    explanation_lower = explanation.lower()

    keywords_by_vuln = {
        "sql injection": ["user input", "query", "parameterized", "prepared statement", "escape", "sanitize"],
        "cross-site scripting (xss)": ["user input", "html", "script", "escape", "sanitize", "safe filter"],
        "command injection": ["user input", "shell", "os.system", "subprocess", "sanitize", "escape"],
        "path traversal": ["user input", "path", "directory", "../", "sanitize", "basename"],
        "hardcoded credentials": ["secret", "key", "password", "environment variable", "config", "rotation"],
    }

    vuln_type = normalize_vuln_type(ground_truth.vulnerability_type)
    keywords = keywords_by_vuln.get(vuln_type, [])

    matched = sum(1 for kw in keywords if kw in explanation_lower)

    if matched == 0:
        feedback.append("Explanation lacks key technical details")
        score = 0.2
    elif matched <= 2:
        score = 0.5
    elif matched <= 4:
        score = 0.8
    else:
        score = 1.0

    if len(explanation) > 500:
        score = min(score, 0.9)
        feedback.append("Explanation is verbose")

    return score, feedback


def evaluate(
    agent_findings: list[AgentFinding],
    ground_truth: GroundTruth,
    tool_calls: int = 0,
    line_tolerance: int = 3,
) -> EvaluationResult:
    """
    Evaluate agent findings against ground truth.

    Args:
        agent_findings: List of vulnerabilities found by the agent
        ground_truth: The actual vulnerability in the challenge
        tool_calls: Number of tool calls the agent made
        line_tolerance: How many lines off the agent can be and still get partial credit

    Returns:
        EvaluationResult with detailed scoring breakdown
    """
    result = EvaluationResult()

    if not agent_findings:
        result.detection_score = -5.0
        result.feedback.append("MISSED: No vulnerabilities reported")
        result.total_score = _calculate_final_score(result)
        return result

    gt_vuln_type = normalize_vuln_type(ground_truth.vulnerability_type)
    gt_severity = normalize_severity(ground_truth.severity)

    best_match = None
    best_match_score = -999

    for finding in agent_findings:
        match_score = 0
        finding_vuln_type = normalize_vuln_type(finding.vulnerability_type)

        if finding_vuln_type == gt_vuln_type:
            match_score += 10
        if finding.file.lower() == ground_truth.file.lower():
            match_score += 5
        if abs(finding.line - ground_truth.line) <= line_tolerance:
            match_score += 3

        if match_score > best_match_score:
            best_match_score = match_score
            best_match = finding

    if best_match is None:
        best_match = agent_findings[0]

    best_vuln_type = normalize_vuln_type(best_match.vulnerability_type)
    best_severity = normalize_severity(best_match.severity)

    if best_vuln_type == gt_vuln_type:
        result.detection_score = 5.0
        result.correct_vuln_type = True
    else:
        result.detection_score = -5.0
        result.feedback.append(
            f"WRONG TYPE: Reported '{best_match.vulnerability_type}' but actual is '{ground_truth.vulnerability_type}'"
        )

    if best_match.file.lower() == ground_truth.file.lower():
        result.localisation_score += 2.0
        result.correct_file = True
    else:
        result.feedback.append(
            f"WRONG FILE: Reported '{best_match.file}' but actual is '{ground_truth.file}'"
        )

    line_diff = abs(best_match.line - ground_truth.line)
    if line_diff == 0:
        result.localisation_score += 2.0
        result.correct_line = True
    elif line_diff <= line_tolerance:
        result.localisation_score += 1.0
        result.feedback.append(
            f"LINE OFF BY {line_diff}: Reported line {best_match.line}, actual is {ground_truth.line}"
        )
    else:
        result.feedback.append(
            f"WRONG LINE: Reported line {best_match.line}, actual is {ground_truth.line}"
        )

    if best_severity == gt_severity:
        result.severity_score = 1.0
        result.correct_severity = True
    else:
        result.feedback.append(
            f"WRONG SEVERITY: Reported '{best_match.severity}' but actual is '{ground_truth.severity}'"
        )

    explanation_score, explanation_feedback = evaluate_explanation(
        best_match.explanation, ground_truth
    )
    result.explanation_score = explanation_score * 1.5
    result.feedback.extend(explanation_feedback)

    false_positives = len(agent_findings) - 1
    if false_positives > 0:
        result.detection_score -= 3.0 * false_positives
        result.feedback.append(f"FALSE POSITIVES: {false_positives} extra finding(s) reported")

    baseline_tools = 2
    if tool_calls > baseline_tools:
        penalty = (tool_calls - baseline_tools) * 0.1
        result.efficiency_score = -penalty
        result.feedback.append(
            f"EFFICIENCY: Used {tool_calls} tool calls ({tool_calls - baseline_tools} over baseline)"
        )
    else:
        result.efficiency_score = 1.0

    result.total_score = _calculate_final_score(result)

    return result


def _calculate_final_score(result: EvaluationResult) -> float:
    """
    Calculate final weighted score.

    Formula: 40% detection + 25% localisation + 15% explanation + 10% severity + 10% efficiency

    Normalized so max score = 10.0
    """
    max_detection = 5.0
    max_localisation = 4.0
    max_explanation = 1.5
    max_severity = 1.0
    max_efficiency = 1.0

    detection_norm = (result.detection_score + 5) / 10
    localisation_norm = result.localisation_score / max_localisation
    explanation_norm = result.explanation_score / max_explanation
    severity_norm = result.severity_score / max_severity
    efficiency_norm = (result.efficiency_score + 1) / 2

    detection_norm = max(0, min(1, detection_norm))
    localisation_norm = max(0, min(1, localisation_norm))
    explanation_norm = max(0, min(1, explanation_norm))
    severity_norm = max(0, min(1, severity_norm))
    efficiency_norm = max(0, min(1, efficiency_norm))

    weighted = (
        0.40 * detection_norm +
        0.25 * localisation_norm +
        0.15 * explanation_norm +
        0.10 * severity_norm +
        0.10 * efficiency_norm
    )

    return round(weighted * 10, 2)


def load_ground_truth(filepath: str) -> GroundTruth:
    """Load ground truth from JSON file."""
    with open(filepath, 'r') as f:
        data = json.load(f)
    return GroundTruth(**data)


def list_challenges(challenges_dir: str = "challenges") -> list[dict]:
    """
    List all available challenges.

    Returns list of dicts with:
      - name: challenge directory name (e.g. 'sql_injection')
      - path: full path to challenge directory
      - ground_truth_path: path to ground_truth.json
      - files: list of non-ground-truth files in the challenge
    """
    import os

    challenges = []
    for name in sorted(os.listdir(challenges_dir)):
        challenge_path = os.path.join(challenges_dir, name)
        if not os.path.isdir(challenge_path):
            continue

        gt_path = os.path.join(challenge_path, "ground_truth.json")
        if not os.path.exists(gt_path):
            continue

        files = [
            f for f in os.listdir(challenge_path)
            if f != "ground_truth.json" and os.path.isfile(os.path.join(challenge_path, f))
        ]

        challenges.append({
            "name": name,
            "path": challenge_path,
            "ground_truth_path": gt_path,
            "files": files,
        })

    return challenges


def load_challenge(challenge_name: str, challenges_dir: str = "challenges") -> tuple[GroundTruth, str]:
    """
    Load a specific challenge by name.

    Returns:
        (ground_truth, challenge_path)
    """
    import os

    challenge_path = os.path.join(challenges_dir, challenge_name)
    gt_path = os.path.join(challenge_path, "ground_truth.json")
    ground_truth = load_ground_truth(gt_path)

    return ground_truth, challenge_path


def generate_feedback_string(result: EvaluationResult) -> str:
    """Generate a human-readable feedback string for the agent."""
    lines = [
        f"Score: {result.total_score}/10.0",
        "",
        "Breakdown:",
        f"  Detection:     {'[OK]' if result.correct_vuln_type else '[X]'} ({result.detection_score:+.1f})",
        f"  File:          {'[OK]' if result.correct_file else '[X]'}",
        f"  Line:          {'[OK]' if result.correct_line else '[X]'} ({result.localisation_score:.1f}/4.0)",
        f"  Severity:      {'[OK]' if result.correct_severity else '[X]'}",
        f"  Explanation:   {result.explanation_score:.1f}/1.5",
        f"  Efficiency:    {result.efficiency_score:+.1f}",
        "",
    ]

    if result.feedback:
        lines.append("Issues:")
        for fb in result.feedback:
            lines.append(f"  - {fb}")
    else:
        lines.append("Perfect score!")

    return "\n".join(lines)


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 3:
        print("Usage: python evaluate.py <ground_truth.json> <agent_output.json>")
        print("\nAgent output JSON format:")
        print(json.dumps({
            "findings": [
                {
                    "vulnerability_type": "SQL Injection",
                    "file": "app.py",
                    "line": 18,
                    "severity": "critical",
                    "explanation": "User input is interpolated directly into SQL query..."
                }
            ],
            "tool_calls": 3
        }, indent=2))
        sys.exit(1)

    gt_path = sys.argv[1]
    agent_path = sys.argv[2]

    ground_truth = load_ground_truth(gt_path)

    with open(agent_path, 'r') as f:
        agent_data = json.load(f)

    findings = [AgentFinding(**f) for f in agent_data.get("findings", [])]
    tool_calls = agent_data.get("tool_calls", 0)

    result = evaluate(findings, ground_truth, tool_calls)
    feedback = generate_feedback_string(result)

    print(feedback)
    print("\n--- Raw Result ---")
    print(json.dumps(result.to_dict(), indent=2))
