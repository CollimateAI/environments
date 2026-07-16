# Collimate Environments

**The environment catalog for [Collimate Cloud](https://collimate.ai) — the
sandbox cloud built for RL post-training.**

Training a policy against real software means running thousands of isolated,
reproducible environments per rollout, over and over, without the sandbox
layer ever becoming your bottleneck. That's what Collimate is for: every image
in this repo is baked into a warm, ready-to-run microVM environment — imports
done, caches hot, test suites runnable. Your trainer asks for a sandbox and
gets one instantly; ask for a thousand and copy-on-write forking means they
cost what they touch, not a thousand boots.

This catalog covers the common ground — Python/ML, Node, browsers, Rust, Go —
and the part built specifically for RL teams: [SWE-bench-style frozen software
worlds](#for-rl-post-training-swe-environments) you can grade rollouts against.

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
3. Collimate Cloud bakes the published image into a warm template. Each
   `env.yaml` declares a **ready command** — `import torch`, a pytest
   collection pass, a Chromium launch — that runs once at bake time, and
   every fork inherits the finished result. That's why a fresh sandbox is
   interactive instantly: imports resolved, caches hot, test suites
   collected, nothing left to warm up. From that moment it shows up in
   `client.images()` and every `create_sandbox("<name>")` is a fork of that
   ready state.

**Catalog environments work on every tier**, including free demo keys —
browse with `client.images()`, create, exec, fork. The images are plain OCI
images: you can `docker run` any of them locally; they behave the same way,
just without the forking. (The baking step — turning an OCI image into a
warm, ready-state microVM artifact — happens on Collimate's side when an
image is admitted to the catalog or baked by a Pro tenant.)

## Bring your own environment (Pro)

Everything in this repo — including environments you generate with
[`swe/make-swe-env.sh`](swe/make-swe-env.sh) and the build workflow — is
ordinary OCI tooling: fork this repo and publish images wherever you like,
no gate. **Running a custom image on Collimate is a Pro feature**: baking
your own environment is how private, team-specific worlds get onto the
platform (demo keys are catalog-only). On the Pro tier, bake straight from
the SDK:

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

## Licensing

The files in this repository (Dockerfiles, `env.yaml` definitions, scripts) are
licensed under [Apache-2.0](LICENSE).

The container images built from these definitions **bundle third-party software
under its own licenses**, which are retained inside each image (Python packages
keep their license files under `*.dist-info/licenses/`; the SWE environments
clone the upstream repository — including its `LICENSE` file — at a pinned
commit into `/repo`). Notable upstream licenses: Flask (BSD-3-Clause),
Requests (Apache-2.0), FastAPI (MIT), PyTorch (BSD-style), Transformers and
Datasets (Apache-2.0), NumPy/SciPy/pandas/scikit-learn (BSD-3-Clause),
Matplotlib (PSF-based), Node.js (MIT), Go (BSD-3-Clause), and the Python and
Debian base images under their respective licenses. Nothing in this repository
relicenses that software; using these images means accepting the bundled
projects' own terms.

The SWE environments pin public open-source repositories at exact commits for
reproducible RL grading; they contain only code those projects publish
publicly.
