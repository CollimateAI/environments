# swe-flask: pallets/flask frozen at 3.1.3 with test dependencies installed and
# the full pytest suite green at build time. An RL trainer forks this
# environment per rollout and grades candidate patches by running pytest.
FROM python:3.12-slim@sha256:c3d81d25b3154142b0b42eb1e61300024426268edeb5b5a26dd7ddf64d9daf28

ENV PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

RUN apt-get update \
 && apt-get install -y --no-install-recommends git ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# pallets/flask @ 3.1.3
ARG REPO_URL=https://github.com/pallets/flask.git
ARG REPO_SHA=22d924701a6ae2e4cd01e9a15bbaf3946094af65

# Fetch exactly the pinned commit and verify we got it.
RUN git init -q /repo \
 && cd /repo \
 && git remote add origin "$REPO_URL" \
 && (git fetch -q --depth 1 origin "$REPO_SHA" || git fetch -q origin) \
 && git checkout -q "$REPO_SHA" \
 && [ "$(git rev-parse HEAD)" = "$REPO_SHA" ]

WORKDIR /repo

# Editable install with the async/dotenv extras, plus the "tests" dependency
# group from pyproject.toml (asgiref, greenlet, pytest, python-dotenv).
RUN pip install -e ".[async,dotenv]" "pytest<9" "werkzeug==3.1.3" greenlet

# The environment contract: the suite is green when the image builds.
RUN python -m pytest -q

CMD ["sleep", "infinity"]
