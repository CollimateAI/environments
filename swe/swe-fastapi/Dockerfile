# swe-fastapi: fastapi/fastapi frozen at 0.139.0 with the [all] extras and the
# "tests" dependency group installed, full pytest suite green at build time.
# The largest of the three SWE environments — a modern, type-heavy codebase
# with a big test suite for RL rollouts that need a harder world.
FROM python:3.12-slim@sha256:c3d81d25b3154142b0b42eb1e61300024426268edeb5b5a26dd7ddf64d9daf28

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# fastapi/fastapi @ 0.139.0
ARG REPO_URL=https://github.com/tiangolo/fastapi.git
ARG REPO_SHA=cecd96d9c6c318e0df1c40cedbc2e953381ddfd3

# Fetch exactly the pinned commit and verify we got it.
RUN git init -q /repo \
 && cd /repo \
 && git remote add origin "$REPO_URL" \
 && (git fetch -q --depth 1 origin "$REPO_SHA" || git fetch -q origin) \
 && git checkout -q "$REPO_SHA" \
 && [ "$(git rev-parse HEAD)" = "$REPO_SHA" ]

WORKDIR /repo

# Editable install with the [all] extras plus the PEP 735 "tests" dependency
# group from pyproject.toml (needs pip >= 25.1 for --group).
RUN pip install --upgrade pip \
 && pip install -e ".[all]" --group tests

# The environment contract: the suite is green when the image builds.
# (-p no:sugar keeps plain pytest output so graders can parse the summary line.)
RUN python -m pytest tests -q -p no:sugar -n auto

CMD ["sleep", "infinity"]
