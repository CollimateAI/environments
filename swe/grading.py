# Fork-per-candidate grading for SWE environments (the exec-grader pattern).
#
# One parent sandbox per task, one CoW fork per candidate: push the candidate's
# edited files, run the task's test command, reward = fraction of tests passed
# (the UnitTestReward pattern). Drop `grade_group` into any trainer as-is.
#
#   pip install collimate-rl
#   COLLIMATE_API_KEY=col_... python grading.py
from __future__ import annotations

import os
import re
from collimate_rl import connect

_SUMMARY = re.compile(r"(\d+) (passed|failed|error)")


def pass_fraction(pytest_output: str) -> float:
    """Score a pytest run: passed / (passed + failed + errors); 0.0 if nothing ran."""
    tally = {"passed": 0, "failed": 0, "error": 0}
    for count, kind in _SUMMARY.findall(pytest_output):
        tally[kind] += int(count)
    total = sum(tally.values())
    return tally["passed"] / total if total else 0.0


def grade_group(client, template: str, candidates: list[list[dict]], test_cmd: str,
                timeout: int = 600) -> list[float]:
    """Grade a group of candidates against one SWE environment.

    Each candidate is a `files=[...]` payload: [{"path": ..., "content": ...}].
    Forks the warm environment once per candidate so every rollout starts from
    an identical, isolated world; returns one reward per candidate.
    """
    parent = client.create_sandbox(template)["id"]
    # One fork call is capped per plan; for GRPO-width groups use the SDK's
    # session.fork_group(n), which spreads a wide group across calls for you.
    children = [c["id"] for c in client.fork(parent, count=len(candidates))["children"]]
    rewards: list[float] = []
    try:
        for sandbox_id, files in zip(children, candidates):
            result = client.exec(
                sandbox_id,
                files=files or None,  # apply the candidate's edits, if any
                commands=[["bash", "-lc", f"cd /repo && {test_cmd}"]],
                timeout_seconds=timeout,
            )
            rewards.append(pass_fraction(result.get("stdout", "") + result.get("stderr", "")))
    finally:
        for sandbox_id in children + [parent]:
            client.delete_sandbox(sandbox_id)
    return rewards


if __name__ == "__main__":
    client = connect(api_key=os.environ["COLLIMATE_API_KEY"])
    # Two demo candidates against psf/requests @ v2.34.2:
    #   A: no edits           -> the frozen suite subset is green -> reward 1.0
    #   B: a broken conftest  -> collection fails                 -> reward 0.0
    good: list[dict] = []
    bad = [{"path": "/repo/tests/conftest.py", "content": "raise RuntimeError('sabotage')\n"}]
    rewards = grade_group(client, "swe-requests", [good, bad],
                          test_cmd="python -m pytest tests/test_structures.py -q")
    for name, reward in zip(("intact", "sabotaged"), rewards):
        print(f"{name}: reward={reward:.2f}")
