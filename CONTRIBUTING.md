# Contributing

Environments are the product here, and good ones are genuinely useful to a lot
of people. If you've built a sandbox image you keep reaching for — or you want
one that doesn't exist yet — we'd love the contribution.

## Proposing an environment

1. **Open an issue first** with the name, a one-line description, and what
   workload it serves (coding agent? browser agent? RL grading? data work?).
   That's enough for a quick yes/no before you spend time on a PR.
2. **Send a PR** adding a directory under `environments/<name>/` (or
   `swe/<name>/` for repo-at-a-commit environments) containing:
   - `Dockerfile` — with a comment header saying what the image is for.
   - `env.yaml` — `id`, `name`, one-line `description`, `tags`, and a `probe`
     command that proves the environment works in one exec.
   - `README.md` — short: what's inside, what it's best for, one usage example.
3. For SWE-style environments, use [`swe/make-swe-env.sh`](swe/make-swe-env.sh)
   as the starting point — it emits the whole directory from a git URL and a
   commit SHA.

## Quality bar

Every environment in the catalog holds to the same standard:

- **Pinned.** Pinned base image, pinned package versions, pinned commit SHAs.
  A rebuild next year should produce the same environment. No `latest`, no
  floating majors.
- **Slim.** One clear purpose per environment. No kitchen sinks, no "might as
  well add" packages, no build caches left in layers. If two audiences need
  different things, that's two environments.
- **Tests green.** SWE environments must run their full test suite during
  `docker build` and fail the build if it's red. General environments must
  have a `probe` command that exercises the actual toolchain (import the
  libraries, compile a file — not just `--version`).
- **Honest description.** Say what the environment actually is. `pytorch-cpu`
  says CPU because it is CPU. If something is slow, limited, or offline-only,
  the README says so.
- **Self-contained build.** `docker build` from the environment directory with
  no secrets, no private registries, no network beyond public package indexes
  and public git hosts.

## What happens after merge

Merged environments are built and published to
`ghcr.io/collimateai/env-<name>` on the next release tag, and picked up by
Collimate Cloud as warm catalog templates from there.

## Code of conduct

Be kind, be direct, assume good faith.
