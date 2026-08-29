import asyncio
import json
import os
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from agent.agent import run_agent
from evaluator.evaluate import evaluate, load_ground_truth

CHALLENGES_DIR = Path("challenges")
VARIANTS = ["baseline", "tool_agent", "self_improving"]
GENERATIONS = 3


def run_variant_on_challenge(variant: str, challenge_name: str, feedback: str = "", history: list = None) -> dict:
    challenge_dir = str(CHALLENGES_DIR / challenge_name)
    ground_truth = load_ground_truth(challenge_dir)

    print(f"  [{variant}] Starting sandbox for challenge: {challenge_name}")
    result = run_agent(challenge_dir, variant=variant, feedback=feedback, history=history or [])

    score = evaluate(result["answer"], ground_truth, tool_calls_used=result["tool_calls"])

    print(f"  [{variant}] Challenge: {challenge_name} | Score: {score['weighted_score']}% | Reward: {score['reward']}")
    return {
        "variant": variant,
        "challenge": challenge_name,
        "answer": result["answer"],
        "tool_calls": result["tool_calls"],
        **score,
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
            "score": r["weighted_score"],
            "feedback": r["feedback"],
        })
    return agent_histories


def print_leaderboard(all_results: list):
    print("\n" + "=" * 50)
    print("         CYBERAGENT ARENA — FINAL RESULTS")
    print("=" * 50)

    for variant in VARIANTS:
        variant_results = [r for r in all_results if r["variant"] == variant]
        if not variant_results:
            continue
        avg = sum(r["weighted_score"] for r in variant_results) / len(variant_results)
        bar = "█" * int(avg / 10) + "░" * (10 - int(avg / 10))
        print(f"  {variant:<20} {bar}  {avg:.1f}%")

    print("=" * 50)
    winner = max(VARIANTS, key=lambda v: sum(
        r["weighted_score"] for r in all_results if r["variant"] == v
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
