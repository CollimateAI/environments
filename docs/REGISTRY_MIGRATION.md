# Environment catalog: registry & build migration

**Goal:** builds happen inside our GCP project and publish to a private Artifact
Registry we control; GHCR (the "open" public registry) becomes disposable.
Public distribution of prebuilt images is a *separate, optional, later* decision
(org policy blocks anonymous AR pulls; Docker Hub would be the path if ever wanted).

## Why (decided 2026-07-16)

- The fleet builder authenticates as a **GCP workload identity** — it has no
  GitHub credential, so it cannot pull a *private* GHCR image. GHCR is the wrong
  registry for the fleet to consume.
- Anonymous/public AR is blocked org-wide by `iam.allowedPolicyMemberDomains`
  (domain-restricted sharing) — verified by a refused `allUsers` binding. So
  "just make AR public" is not available without an org-admin policy change.
- Nothing in the product or the demo needs a *public* image: the source repo is
  public (anyone can `docker build`), and both bake + demo pull privately.

## Target architecture

```
GitHub (source Dockerfiles, public repo)
        │  release tag / dispatch
        ▼
Cloud Build (builds INSIDE GCP)  ──push──▶  AR: collimate-environments  (PRIVATE)
                                                    │  env-<name>:src (+ :<digest>)
                                                    ▼
                                    fleet builder pulls by DIGEST → bakes warm template
                                                    ▼
                                    AR: collimate  (tpl-… baked artifacts) → node-agents fork
```

- **Registry:** `us-central1-docker.pkg.dev/collimateai/collimate-environments`
  (created 2026-07-16). IAM: builder + node-agent WIF principals = reader;
  Cloud Build compute SA = writer. No `allUsers`.
- **Catalog admission pins by DIGEST**, never a mutable tag (`edge`/`src`) — a
  repushed tag must never silently change what a catalog template bakes.

## Phases

**P1 — unblock (done first):** Cloud Build `env-browser` → `collimate-environments`,
point the `browser` catalog Template CR at the AR digest, bake, admit.

**P2 — pipeline:** replace the GHCR-only workflow with an in-GCP build. **DONE
in this repo** (`cloudbuild.yaml` + `.github/workflows/build.yml`); the WIF
binding below is the remaining prerequisite the orchestrator must apply.

- `cloudbuild.yaml` at repo root: discovers every `environments/*/Dockerfile`
  and `swe/*/Dockerfile` in one bash-loop step, builds each, and pushes to
  `.../collimate-environments/env-<name>` with two tags — `:src` (mutable
  convenience) and `:$SHORT_SHA` (immutable, git-pinned; the catalog admits by
  the digest under this tag). `machineType: E2_HIGHCPU_8`, `timeout: 3600s` for
  the heavy playwright/torch/swe builds. The Cloud Build compute SA
  (`827405099373-compute@developer.gserviceaccount.com`) is writer on the AR
  repo; builder + node-agent WIF principals are reader.
- Trigger: a thin GH workflow (`build.yml`) that authenticates via **Workload
  Identity Federation** (no long-lived keys) and runs
  `gcloud builds submit --config cloudbuild.yaml --substitutions=SHORT_SHA=<7-char>`.
  Triggers: release tag (`v*`) and `workflow_dispatch`. GHCR login/push removed.
  (A pure Cloud Build GitHub trigger — zero GH compute — is an alternative that
  needs no WIF; we chose the WIF-dispatch form so the build is visible in the GH
  Actions UI and gated on the same `v*`/dispatch triggers as before.)
- GHCR push is dropped entirely (no convenience mirror). GHCR is retired in P4.

### P2 prerequisite — GitHub-Actions WIF pool/provider + SA binding

The workflow needs a Workload Identity **pool with a GitHub OIDC provider**. The
project's existing WIF pool is the GKE/k8s pool (issuer
`container.googleapis.com` / `*.svc.id.goog`) — it does **not** trust GitHub's
OIDC issuer, so a **separate `github-actions` pool + provider is required**. The
orchestrator/user must create these once (values below assume project
`collimateai`, number `827405099373`):

```bash
PROJECT=collimateai
PROJECT_NUMBER=827405099373
POOL=github-actions
PROVIDER=github
GH_ORG=CollimateAI          # owner of the environments repo
GH_REPO=environments        # -> repo:CollimateAI/environments
SA=gh-actions-builder@collimateai.iam.gserviceaccount.com

# 1) Pool
gcloud iam workload-identity-pools create "$POOL" \
  --project="$PROJECT" --location=global \
  --display-name="GitHub Actions"

# 2) OIDC provider trusting GitHub's issuer, with an attribute condition that
#    restricts token acceptance to this org (defense in depth vs. any GH repo).
gcloud iam workload-identity-pools providers create-oidc "$PROVIDER" \
  --project="$PROJECT" --location=global \
  --workload-identity-pool="$POOL" \
  --display-name="GitHub OIDC" \
  --issuer-uri="https://token.actions.githubusercontent.com" \
  --attribute-mapping="google.subject=assertion.sub,attribute.repository=assertion.repository,attribute.ref=assertion.ref" \
  --attribute-condition="assertion.repository_owner == '${GH_ORG}'"

# 3) Runtime SA the workflow impersonates. Needs to launch Cloud Build and
#    actAs the Cloud Build runtime SA.
gcloud iam service-accounts create gh-actions-builder \
  --project="$PROJECT" --display-name="GitHub Actions -> Cloud Build"
gcloud projects add-iam-policy-binding "$PROJECT" \
  --member="serviceAccount:${SA}" --role="roles/cloudbuild.builds.editor"
# Allow it to actAs the Cloud Build compute/runtime SA that actually builds+pushes:
gcloud iam service-accounts add-iam-policy-binding \
  "${PROJECT_NUMBER}-compute@developer.gserviceaccount.com" \
  --project="$PROJECT" \
  --member="serviceAccount:${SA}" --role="roles/iam.serviceAccountUser"

# 4) Bind the principalSet to allow WIF impersonation from this repo only.
#    The k8s/WIF principal string uses `*.svc.id.goog`; the GitHub-Actions pool
#    principal is under the pool resource path, keyed by attribute.repository.
POOL_RES="projects/${PROJECT_NUMBER}/locations/global/workloadIdentityPools/${POOL}"
gcloud iam service-accounts add-iam-policy-binding "$SA" \
  --project="$PROJECT" --role="roles/iam.workloadIdentityUser" \
  --member="principalSet://iam.googleapis.com/${POOL_RES}/attribute.repository/${GH_ORG}/${GH_REPO}"
```

The exact `principalSet` member strings (attribute-scoped — the workflow's
`main` branch and `v*` tag refs both satisfy `attribute.repository`):

```
# any workflow run in the repo (covers refs/heads/main and refs/tags/v*):
principalSet://iam.googleapis.com/projects/827405099373/locations/global/workloadIdentityPools/github-actions/attribute.repository/CollimateAI/environments

# to pin harder to specific refs, map attribute.ref and bind these instead:
principalSet://iam.googleapis.com/projects/827405099373/locations/global/workloadIdentityPools/github-actions/attribute.ref/refs/heads/main
principalSet://iam.googleapis.com/projects/827405099373/locations/global/workloadIdentityPools/github-actions/attribute.ref/refs/tags/<tag>
```

Then set the two repo **Actions secrets** the workflow reads:

```
GCP_WIF_PROVIDER = projects/827405099373/locations/global/workloadIdentityPools/github-actions/providers/github
GCP_BUILD_SA     = gh-actions-builder@collimateai.iam.gserviceaccount.com
```

(Note: `collimateai.svc.id.goog` is the GKE **workload identity** namespace for
in-cluster pods — it is unrelated to and cannot be used for GitHub OIDC. GitHub
Actions must go through the `github-actions` pool/provider above.)

**P3 — migrate all envs:** Cloud Build the remaining 9 (`python-ml`, `pytorch-cpu`,
`node`, `rust`, `go`, `datasci-notebook`, `swe-*`) into `collimate-environments`;
record digests; admit the good ones to the managed catalog with descriptions +
`ready.cmd` from each `env.yaml`.

**P4 — cutover & cleanup:** once every artifact + catalog row references AR digests,
retire GHCR: stop the GHCR publish step and **delete the GHCR packages** (the
"open registry"). The **GitHub source repo stays** (source of truth, public
reproducibility, and the substrate for a future marketplace).

## Future: environment marketplace

The dedicated `collimate-environments` registry + the `env.yaml`/`ready.cmd`
contract + `make-swe-env.sh` generator are the substrate for letting outsiders
contribute gym environments (PR to the repo → CI builds in GCP → admitted to a
community catalog tier). Out of scope now; the private-registry + in-GCP-build
posture is the prerequisite that makes it safe later (untrusted Dockerfiles build
in an isolated, egress-locked Cloud Build, never touch tenant artifacts).
