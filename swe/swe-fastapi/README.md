# swe-fastapi

[fastapi/fastapi](https://github.com/tiangolo/fastapi) frozen at **0.139.0**
(`cecd96d9c6c318e0df1c40cedbc2e953381ddfd3`), checked out at `/repo` with the
`[all]` extras and the full `tests` dependency group installed. Full pytest
suite green at build time.

**Best for:** harder SWE-style rollouts. This is the biggest world of the
three — a modern, heavily-typed codebase (Pydantic v2, Starlette) with a large
test suite. Use targeted test subsets for per-task grading; the full suite is
better as a final pass-to-pass regression gate than a per-candidate reward.

```python
from collimate_rl import connect

client = connect(api_key="col_...")
sb = client.create_sandbox("swe-fastapi")

r = client.exec(
    sb["id"],
    files=[{"path": "/repo/fastapi/params.py", "content": candidate_source}],
    commands=[["bash", "-lc",
               "cd /repo && python -m pytest tests/test_path.py tests/test_query.py -q -p no:sugar"]],
    timeout_seconds=600,
)
print(r["exit_code"], r["stdout"])
```

Note: the test dependencies include `pytest-sugar`; pass `-p no:sugar` in
grading commands to keep plain, parseable pytest summary output (the shipped
examples all do).

See [`tasks.jsonl.example`](tasks.jsonl.example) for the task-record shape and
[`../grading.py`](../grading.py) for the full fork-per-candidate grading loop.
