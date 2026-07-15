# swe-requests: psf/requests frozen at v2.34.2 with its dev dependencies
# installed and the full pytest suite green at build time. An RL trainer forks
# this environment per rollout and grades candidate patches by running pytest —
# the suite runs fully offline (pytest-httpbin serves a local httpbin).
FROM python:3.12-slim

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# psf/requests @ v2.34.2
ARG REPO_URL=https://github.com/psf/requests.git
ARG REPO_SHA=6e83187b8feb273ed4c6cdab5efd8d54901dfab3

# Fetch exactly the pinned commit and verify we got it.
RUN git init -q /repo \
 && cd /repo \
 && git remote add origin "$REPO_URL" \
 && (git fetch -q --depth 1 origin "$REPO_SHA" || git fetch -q origin) \
 && git checkout -q "$REPO_SHA" \
 && [ "$(git rev-parse HEAD)" = "$REPO_SHA" ]

WORKDIR /repo

# requirements-dev.txt includes the editable install (-e .[socks]) plus the
# full test stack (pytest, pytest-httpbin, httpbin, trustme).
RUN pip install -r requirements-dev.txt

# The environment contract: the suite is green when the image builds.
RUN python -m pytest -q

CMD ["sleep", "infinity"]
