# Collimate Environments

**Ready-to-fork sandbox environments. Pick one, fork it a thousand times.**

This is the public catalog behind [Collimate Cloud](https://collimate.ai) — a
microVM sandbox cloud built around one signature move: instant copy-on-write
forking of warm environments. Every image in this repo is baked into a warm,
ready-to-run environment on Collimate. You don't boot it, you don't install
into it, you don't wait for it. You fork it — in milliseconds, as many times as
your workload needs — and every fork is a fully isolated microVM.

## 30 seconds to a thousand sandboxes

```bash
pip install collimate-rl
```

```python
from collimate_rl import connect

client = connect(api_key="col_...")           # your Collimate API key

print([img["id"] for img in client.images()])  # browse this catalog, live

sb = client.create_sandbox("python-ml")        # a warm fork, ready instantly
kids = client.fork(sb["id"], count=1000)["children"]   # 1,000 CoW copies

r = client.exec(
    kids[0]["id"],
    commands=[["bash", "-lc", "python -c 'import sklearn; print(sklearn.__version__)'"]],
)
print(r["stdout"])
```

Each fork shares memory and disk with its parent until it diverges, so a
thousand copies of a multi-gigabyte environment cost what they touch — not a
thousand boots, not a thousand installs.

## The catalog

| Environment | What's inside | Best for |
|---|---|---|
| [`python-ml`](environments/python-ml) | Python 3.12, NumPy, pandas, SciPy, scikit-learn, Matplotlib | Data analysis, classic ML, code-exec agents |
| [`pytorch-cpu`](environments/pytorch-cpu) | PyTorch (CPU), Transformers, Datasets | CPU inference, eval harnesses, tokenizer/data work |
| [`node`](environments/node) | Node 22, pnpm, TypeScript, Vitest | JS/TS coding agents, test-driven codegen |
| [`browser`](environments/browser) | Playwright + Chromium (Python) | Browser agents, web automation, scraping evals |
| [`rust`](environments/rust) | Rust 1.79, cargo-nextest, common build deps | Rust codegen, compile-and-test reward loops |
| [`go`](environments/go) | Go 1.23, golangci-lint | Go coding agents, lint-gated codegen |
| [`datasci-notebook`](environments/datasci-notebook) | Python + Jupyter kernel, DuckDB, Polars, PyArrow | Notebook-style exec, SQL-on-files, dataframe agents |

### For RL post-training: SWE environments

The [`swe/`](swe) directory is the centerpiece for RL teams: **frozen,
reproducible software worlds**. Each one is a real open-source repository
checked out at a pinned commit with its dependencies installed and its test
suite green at build time. Fork one per rollout, let your policy edit the code,
and grade by running the tests — the exec-grader pattern.

| Environment | Repo (pinned) | Test suite |
|---|---|---|
| [`swe-requests`](swe/swe-requests) | `psf/requests` @ v2.34.2 | pytest, runs offline |
| [`swe-flask`](swe/swe-flask) | `pallets/flask` @ 3.1.3 | pytest |
| [`swe-fastapi`](swe/swe-fastapi) | `fastapi/fastapi` @ 0.139.0 | pytest, full test group |

Want an environment for a different repo? [`swe/make-swe-env.sh`](swe/make-swe-env.sh)
generates one from any git URL + commit SHA in one command, and
[`swe/grading.py`](swe/grading.py) is a complete fork-and-grade reward function
you can drop into a trainer today.

## How images become catalog entries

1. An environment lands in this repo: a `Dockerfile`, an `env.yaml` describing
   it, and a README.
2. A release tag triggers [the build workflow](.github/workflows/build.yml),
   which builds every environment and publishes it to
   `ghcr.io/collimateai/env-<name>:<tag>`.
3. Collimate Cloud bakes the published image into a warm template. From that
   moment it shows up in `client.images()` and every `create_sandbox("<name>")`
   is an instant fork of a ready environment — imports done, caches hot,
   test suites runnable.

The images are plain OCI images. You can `docker run` any of them locally;
they behave the same way, just without the forking.

## Bring your own environment

Anything you can put in a container, Collimate can serve warm. On the Pro
tier, bake your own image straight from the SDK:

```python
client.create_template(
    name="my-env",
    image="ghcr.io/you/your-image:v1",
    width=64,           # how wide you want to fork
)
```

Your private environments live alongside the catalog and fork exactly the same
way. See the [Collimate docs](https://collimate.ai/docs) for ready-state
checks, egress policy, and template lifecycle.

## Contributing

New environment ideas are very welcome — the quality bar and the process are in
[CONTRIBUTING.md](CONTRIBUTING.md). Short version: pinned base, pinned
versions, slim, honest description, and (for SWE environments) a test suite
that's green at build time.

## License

[Apache-2.0](LICENSE) © 2026 Collimate contributors.
