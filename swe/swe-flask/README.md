# swe-flask

[pallets/flask](https://github.com/pallets/flask) frozen at **3.1.3**
(`22d924701a6ae2e4cd01e9a15bbaf3946094af65`), checked out at `/repo` with the
async/dotenv extras and test dependencies installed. Full pytest suite green
at build time.

**Best for:** SWE-style RL rollouts on a mid-size, idiomatic Python codebase
with a fast test suite — quick grading turnarounds make it a good fit for
wide GRPO groups.

```python
from collimate_rl import connect

client = connect(api_key="col_...")
sb = client.create_sandbox("swe-flask")

r = client.exec(
    sb["id"],
    files=[{"path": "/repo/src/flask/config.py", "content": candidate_source}],
    commands=[["bash", "-lc", "cd /repo && python -m pytest tests/test_config.py -q"]],
    timeout_seconds=300,
)
print(r["exit_code"], r["stdout"])
```

See [`tasks.jsonl.example`](tasks.jsonl.example) for the task-record shape and
[`../grading.py`](../grading.py) for the full fork-per-candidate grading loop.
