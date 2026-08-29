import asyncio
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from agent.agent import run_agent
from evaluator.evaluate import AgentFinding, evaluate, generate_feedback_string, load_challenge

CHALLENGES_DIR = Path("challenges")
VARIANTS = ["baseline", "tool_agent", "self_improving"]
GENERATIONS = 3
FINDING_FIELDS = {"vulnerability_type", "file", "line", "severity", "explanation"}


def _answer_to_findings(answer: dict) -> list:
    """Convert the agent's raw JSON answer into AgentFinding objects the evaluator expects."""
    if not answer:
        return []
    fields = {k: v for k, v in answer.items() if k in FINDING_FIELDS}
    try:
        return [AgentFinding(
            vulnerability_type=fields["vulnerability_type"],
            file=fields["file"],
            line=int(fields["line"]),
            severity=fields["severity"],
            explanation=fields.get("explanation", ""),
        )]
    except (KeyError, TypeError, ValueError):
        return []


def run_variant_on_challenge(variant: str, challenge_name: str, feedback: str = "", history: list = None) -> dict:
    ground_truth, challenge_dir = load_challenge(challenge_name, str(CHALLENGES_DIR))

    print(f"  [{variant}] Starting sandbox for challenge: {challenge_name}")
    result = run_agent(challenge_dir, variant=variant, feedback=feedback, history=history or [])

    answer = result["answer"]
    findings = _answer_to_findings(answer)

    eval_result = evaluate(findings, ground_truth, tool_calls=result["tool_calls"])
    result_feedback = generate_feedback_string(eval_result)

    print(f"  [{variant}] Challenge: {challenge_name} | Score: {eval_result.total_score}/10.0")
    return {
        "variant": variant,
        "challenge": challenge_name,
        "answer": answer,
        "tool_calls": result["tool_calls"],
        **eval_result.to_dict(),
        "score": eval_result.total_score,
        "feedback": result_feedback,
    }


def run_generation(generation: int, agent_histories: dict) -> list:
    print(f"\n=== Generation {generation} ===")
    challenges = [d.name for d in CHALLENGES_DIR.iterdir() if d.is_dir()]
    results = []

    with ThreadPoolExecutor(max_workers=len(VARIANTS)) as executor:
        futures = []
        for variant in VARIANTS:
            for challenge in challenges:
                history = agent_histories.get(variant, [])
                feedback = history[-1]["feedback"] if history else ""
                futures.append(
                    executor.submit(run_variant_on_challenge, variant, challenge, feedback, history)
                )
        for future in futures:
            results.append(future.result())

    return results


def update_histories(agent_histories: dict, results: list) -> dict:
    for r in results:
        variant = r["variant"]
        if variant not in agent_histories:
            agent_histories[variant] = []
        agent_histories[variant].append({
            "score": r["score"],
            "feedback": r["feedback"],
        })
    return agent_histories


def print_leaderboard(all_results: list):
    print("\n" + "=" * 50)
    print("         CYBERAGENT ARENA - FINAL RESULTS")
    print("=" * 50)

    for variant in VARIANTS:
        variant_results = [r for r in all_results if r["variant"] == variant]
        if not variant_results:
            continue
        avg = sum(r["score"] for r in variant_results) / len(variant_results)
        bar = "#" * int(avg) + "." * (10 - int(avg))
        print(f"  {variant:<20} {bar}  {avg:.1f}/10.0")

    print("=" * 50)
    winner = max(VARIANTS, key=lambda v: sum(
        r["score"] for r in all_results if r["variant"] == v
    ))
    print(f"\n  Promoted Agent: {winner.upper()}")


def save_results(all_results: list):
    with open("results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print("\nResults saved to results.json")


def main():
    agent_histories = {}
    all_results = []

    for gen in range(1, GENERATIONS + 1):
        results = run_generation(gen, agent_histories)
        all_results.extend([{**r, "generation": gen} for r in results])
        agent_histories = update_histories(agent_histories, results)

    print_leaderboard(all_results)
    save_results(all_results)


if __name__ == "__main__":
    main()
