# AGENTS.md

This repository is built for **AI coding agents** (Hermes, Claude Code, Codex, Cursor, OpenCode, etc.) to consume as a tool. Humans can use it too, but every design choice. flags, output, idempotency, error surface. assumes the caller is an agent driving a terminal.

If you are an agent, read this first. It tells you exactly how to use the tool, what to expect on stdout, and how to recover from failures without asking the user.

## What this skill does

One command takes a repository containing a Dockerfile (and optionally a static frontend) and ships it to Azure as a public HTTPS URL.

```
deploy-azure init     # writes azure.toml next to the project
deploy-azure up       # builds + deploys, prints the URL
deploy-azure status   # prints URLs + resource state
deploy-azure destroy
```

There are no interactive prompts. No "press y to continue". Everything is flag-driven. `destroy` and `up` accept `--yes` to skip the one safety confirmation.

## How an agent should invoke this

```bash
# 1. Locate the script (installed as a Hermes skill, or run from this repo)
deploy-azure --help
# fallback:
python3 /path/to/skill/scripts/deploy-azure --help

# 2. Probe the project (no side effects, exits 0 with a written azure.toml plan)
deploy-azure init --dry-run

# 3. Commit to a deployment
deploy-azure init --profile express --region eastasia
deploy-azure up --yes
```

## Command contract

| Command | Exit 0 means | Side effects |
| --- | --- | --- |
| `init` | `azure.toml` exists in cwd, defaults sane for the detected stack | Writes `./azure.toml` unless `--dry-run` |
| `up` | Public URL is live and `GET /healthz` (or `/`) returns 2xx | Creates ACR, env, app, SWA, secrets; pushes image |
| `status` | Resource group exists and is queryable | None |
| `destroy` | RG deletion accepted by ARM (async) | Deletes everything under the RG |
| `db add postgres` | Postgres Flexible Server is live, `DATABASE_URL` secret bound | Creates server, firewall rule, db, secret |
| `domain add <host>` | CNAME wired to SWA/ACA, validation initiated | Adds hostname to SWA or ACA |
| `logs --tail` | Streams forever until SIGINT | None |

Final line of stdout on a successful `up` is always the public URL. An agent can grep for `^https://` to extract it. Example:

```bash
URL=$(deploy-azure up --yes | tail -n1)
```

A `--json` flag is available on `up`, `status`, and `doctor` for machine-readable output. Progress chatter is routed to stderr, so `command --json 2>/dev/null` returns clean JSON on stdout.

## Idempotency contract (this matters)

`deploy-azure up` is **safe to re-run**. Every provisioning step is GET-then-PUT. An agent that times out, loses network, or panics can simply call `up` again. There is no "rollback half-deploy" state to clean up.

The script is also safe to interrupt with SIGINT mid-step. The next `up` resumes from the first incomplete resource.

## Recovery without the user

When you get a non-zero exit, do this **before** asking the user anything:

1. **Re-run the same command once.** Most ARM 5xx errors are transient.
2. **Scan stderr for known patterns**, then act:
   - `ContainerAppInvalidResourceTotal` → edit `[backend] cpu` / `memory` in `azure.toml` to a valid Flex pair (see `skill/references/troubleshooting.md`) and re-run `up`.
   - `acr ... is already in use` / `ACR name not available` → re-run `up`. The script auto-suffixes ACR names on retry and rewrites `azure.toml`.
   - `RegistryAuthFailed` → re-run `up`. ACR admin credentials sometimes lag propagation.
   - `Express` + `region not supported` → re-run `init --profile flex --region westeurope` (or `eastus`, `eastus2`) and `up`.
   - `Please run 'az login'` or `AADSTS` errors → surface to the user. They must `az login`.
   - `quota` / `SubscriptionRequestsThrottled` → surface to the user. Manual action required.
3. Full error table: [`skill/references/troubleshooting.md`](skill/references/troubleshooting.md).

Only escalate to the user for: auth failures, billing/quota refusals, and confirmed bugs.

## Profile selection (cheat sheet)

| Region you want | Use profile |
| --- | --- |
| `westcentralus`, `eastasia` | `express` (default, scale-to-zero, sub-second cold start) |
| `westeurope`, `eastus`, `eastus2` | `flex` (per-second billing, min replicas ≥ 1) |
| Anywhere else | `consumption` (GA, every region) |

The script auto-falls-back from `express` → `flex` if you pass an Express profile with a non-Express region. Full decision table: [`skill/references/express-vs-flex.md`](skill/references/express-vs-flex.md).

## Environment expectations

You can assume an agent host has, or can install:

- `az` CLI ≥ 2.85 with the `containerapp` extension ≥ 1.3.0b4 (`az extension update -n containerapp`)
- Python 3.11+
- Network access to `*.azurecr.io`, `management.azure.com`, `learn.microsoft.com`
- An `az login` session backed by Microsoft Entra ID (Express does not support personal Microsoft accounts)

You **cannot** assume:

- Docker is running locally. the script always uses `az acr build` (cloud-side build)
- Bicep / Terraform / Pulumi is installed. never needed
- A particular shell. the script is invoked directly, not sourced

## Where to read next (priority order for an agent)

1. [`skill/SKILL.md`](skill/SKILL.md): when to load this skill, full command surface
2. [`skill/references/express-vs-flex.md`](skill/references/express-vs-flex.md): profile selection decision table
3. [`skill/references/troubleshooting.md`](skill/references/troubleshooting.md): error pattern reference
4. [`skill/references/arm-rest-patterns.md`](skill/references/arm-rest-patterns.md): exact ARM request bodies (for debugging / extending the script)

Human-facing docs (`README.md`, `docs/comparison-vercel.md`) are for context only. Skip them on a hot path.

## Microsoft Learn MCP (for live API validation)

If you need to validate an Azure API contract or check a region's preview status while debugging, use the **Microsoft Learn MCP server** (`https://learn.microsoft.com/api/mcp`). It exposes `microsoft_docs_search`, `microsoft_code_sample_search`, and `microsoft_docs_fetch` against the live Microsoft Learn corpus. This is the source of truth for everything the script does.

## Contributing as an agent

If you patch this repo:

- Run `python3 -c "import ast; ast.parse(open('skill/scripts/deploy-azure').read())"` before committing.
- Run `examples/hello-fullstack` end-to-end on at least one profile.
- Keep the script stdlib-only. No `requests`, no `pyyaml`.
- Update this file (`AGENTS.md`) if you change any command's exit-code or stdout contract.
- Commits should follow Conventional Commits (`feat:`, `fix:`, `docs:`, `chore:`).

## Agent-friendly roadmap

Tracked for the next release:

- [x] `--json` flag on `up`, `status`, `doctor` emitting structured output
- [x] `deploy-azure doctor`: pre-flight check (az version, extension version, login state, region/profile validity, ACR name availability)
- [ ] Stable error `code` strings in JSON failure envelopes
- [ ] `--json` on remaining commands (`init`, `db add`, `logs`, `destroy`)
- [ ] `--quiet` flag suppressing progress logs (only final URL on stdout)

PRs adding any of these are very welcome.
