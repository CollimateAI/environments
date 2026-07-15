# swe-requests

[psf/requests](https://github.com/psf/requests) frozen at **v2.34.2**
(`6e83187b8feb273ed4c6cdab5efd8d54901dfab3`), checked out at `/repo`, dev
dependencies installed, full pytest suite green at build time.

**Best for:** SWE-style RL rollouts on a small, well-tested, widely-known
codebase. The suite runs **fully offline** — `pytest-httpbin` spins up a local
httpbin inside the sandbox — which makes it the best starter environment of
the three: no egress needed to grade.

```python
from collimate_rl import connect

client = connect(api_key="col_...")
sb = client.create_sandbox("swe-requests")

# Grade a candidate: push edited files, run the target tests.
r = client.exec(
    sb["id"],
    files=[{"path": "/repo/src/requests/help.py", "content": candidate_source}],
    commands=[["bash", "-lc", "cd /repo && python -m pytest tests/test_help.py -q"]],
    timeout_seconds=300,
)
print(r["exit_code"], r["stdout"])
```

See [`tasks.jsonl.example`](tasks.jsonl.example) for the task-record shape and
[`../grading.py`](../grading.py) for the full fork-per-candidate grading loop.
