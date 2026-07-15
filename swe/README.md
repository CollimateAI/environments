# SWE environments — frozen software worlds for RL post-training

A SWE environment is a **real open-source repository, frozen at a pinned
commit, with its dependencies installed and its test suite runnable** — a
complete, reproducible software world your policy can act on. It's the
SWE-bench pattern turned into a warm, forkable sandbox:

```
environment = frozen repo state + runnable tests
rollout     = fork the environment, let the policy edit the code
reward      = run the test suite (or a subset); score the result
```

## Why this shape works

- **Fork per rollout.** Every rollout gets its own microVM fork of the
  environment: repo checked out, dependencies imported, caches hot. A GRPO
  group of 64 candidates is 64 forks of the same parent — identical starting
  state by construction, isolated by construction. No shared temp dirs, no
  cross-contamination between candidates, no cleanup between episodes:
  discard the fork, fork again.
- **Grade by exec.** The reward function is just an exec: apply the candidate's
  edits, run `pytest` (the full suite, or the task's target subset), and turn
  the outcome into a scalar — pass fraction, or a binary fail-to-pass check.
  This is the exec-grader pattern: environment logic stays in your trainer,
  the sandbox produces an isolated, reproducible signal.
- **Deterministic by construction.** The repo is pinned to a commit SHA (the
  build fails if the checkout drifts), dependencies are resolved at build time,
  and the test suite must be green when the image builds. What's left as
  nondeterminism is your policy's — and the exec API's `seed` parameter covers
  the rest when you need common random numbers across a group.

## The environments

| Environment | Repo | Pinned at | Install | Suite |
|---|---|---|---|---|
| [`swe-requests`](swe-requests) | [psf/requests](https://github.com/psf/requests) | `v2.34.2` (`6e83187b`) | `pip install -r requirements-dev.txt` | `python -m pytest -q` (offline, local httpbin) |
| [`swe-flask`](swe-flask) | [pallets/flask](https://github.com/pallets/flask) | `3.1.3` (`22d92470`) | `pip install -e ".[async,dotenv]" pytest greenlet` | `python -m pytest -q` |
| [`swe-fastapi`](swe-fastapi) | [fastapi/fastapi](https://github.com/tiangolo/fastapi) | `0.139.0` (`cecd96d9`) | `pip install -e ".[all]" --group tests` | `python -m pytest tests -q -p no:sugar` |

Each image checks the repo out at `/repo`, verifies the SHA, installs the
dependencies, and **runs the full test suite during `docker build`** — a red
suite fails the build, so a published image is a green world.

Each environment ships a `tasks.jsonl.example` showing the task-record shape
(bug description → target files → grading command) in a SWE-bench-like format.
The records are illustrative — they show the shape your curated task set
should take, they are not a benchmark.

## Grading a rollout

[`grading.py`](grading.py) is the whole pattern in one file, using the
`collimate-rl` SDK: fork the environment once per candidate, push the
candidate's edited files with `files=[...]`, run the task's test command, and
score the pass fraction:

```bash
COLLIMATE_API_KEY=col_... python grading.py
```

The same loop drops into SkyRL/verl-style trainers as the reward function —
`connect()` picks the right transport whether you're on a laptop with an API
key or inside a rollout worker.

## Make your own SWE environment

```bash
./make-swe-env.sh <git-url> <sha> '<install-cmd>' '<test-cmd>' [name]

# example: pallets/click at its 8.4.2 release commit
./make-swe-env.sh https://github.com/pallets/click.git \
    b2e30a175449cfda909ee4fbf4a29a6a071cad53 \
    'pip install -e . pytest' \
    'python -m pytest -q'
```

This emits a complete environment directory (Dockerfile, env.yaml, README,
tasks.jsonl.example) following the same conventions: checkout at the exact
SHA, install, run the suite at build time, fail if red. Add it to the repo,
tag a release, and it's in the catalog.
