---
name: deploy-azure
description: One-command fullstack deploys to Azure. Static Web Apps + Container Apps Express (with Flex/Consumption fallbacks) + Postgres Flexible Server. Built for AI agents. Idempotent, stdlib-only Python CLI.
when_to_use: An AI agent (or user) wants to ship a web app or fullstack project to Azure with minimal config. Especially useful for vibe-coded prototypes, FastAPI/Flask + Next.js apps, AI app frontends, MCP servers, agent endpoints, or anything where you'd reach for `vercel` if it were running on Azure. Default backend profile is Azure Container Apps Express (May 2026 Public Preview). The CLI is fully non-interactive and safe to re-run. see AGENTS.md in the repo root for the full agent contract.
---

# deploy-azure

A skill that ships full-stack apps to Azure with one command:

```bash
deploy-azure init     # scans the repo, writes azure.toml (profile=express by default)
deploy-azure up       # builds via az acr build, provisions everything, prints a URL
```

## What it provisions

- **Frontend**: Azure Static Web Apps (Free SKU, global CDN). Auto-detected from `next.config.*` or a Next.js `package.json`.
- **Backend**: Azure Container Apps. Three profiles supported:
  - **`express`** (default, May 2026 Public Preview, `westcentralus` / `eastasia` only): uses `az containerapp env create --environment-mode express` from the `containerapp` extension ≥ 1.3.0b4. No env config to write, scale-to-zero, sub-second cold starts. HTTP only. Personal Microsoft accounts not supported (Entra ID only).
  - **`flex`** (workload profile, preview, `westeurope` / `eastus` / `eastus2`): provisioned via raw ARM REST against `Microsoft.App/managedEnvironments` and `Microsoft.App/containerApps` (api-version `2025-10-02-preview`) because `az` hasn't shipped a friendly workload-profile flag yet.
  - **`consumption`** (GA, every region): uses `az containerapp` end-to-end.

  Auto-detected from the shallowest `Dockerfile`. The script falls back from `express` → `flex` if the requested region isn't in the Express preview list.
- **Database**: Postgres Flexible Server (Burstable B1ms), with the connection string injected as an ACA secret named `database-url` and surfaced to the container as `DATABASE_URL`.
- **Custom domain**: bound via SWA `hostname set` or ACA `hostname bind` with CNAME validation.

## Tools required on PATH

- `az` (Azure CLI, ≥ 2.85): includes `az acr build`, which we use to build images in the cloud
- `az extension add -n containerapp --version 1.3.0b4` (or newer): provides `--environment-mode express`
- Python 3.11+ (the script re-execs under a newer interpreter if invoked under 3.9)

> No local Docker daemon required. Images are built and pushed by `az acr build` running on ACR's own build agent. This sidesteps Docker Desktop credential-helper hangs and works inside CI runners that don't have Docker available.

## Researching Azure APIs (mandatory)

**Before changing any ARM body, region availability claim, SKU list, CLI flag, or preview-API behaviour in this skill, query the official Microsoft docs via the Microsoft Learn MCP** (`mcp_microsoft_learn_*` tools, hosted at `https://learn.microsoft.com/api/mcp`). It's the canonical source. fresher than Stack Overflow, less hallucinated than a web search, and far more reliable than guessing.

If the MCP isn't wired into the current Hermes config, add it:

```yaml
# ~/.hermes/config.yaml
mcp_servers:
  microsoft-learn:
    url: https://learn.microsoft.com/api/mcp
```

Then `hermes` will expose three tools:

- `microsoft_docs_search(query)`: fast keyword search over the Learn corpus
- `microsoft_code_sample_search(query)`: code-aware search across the docs and samples
- `microsoft_docs_fetch(url)`: pull a specific learn.microsoft.com page in full

Recommended queries for this skill:

- `microsoft_docs_search("Container Apps Express environment-mode preview regions")`
- `microsoft_docs_search("Container Apps Flex workload profile workloadProfileType ARM")`
- `microsoft_code_sample_search("az containerapp env create --environment-mode express")`
- `microsoft_docs_fetch("https://learn.microsoft.com/azure/container-apps/express-faq")`

If you discover an Express region rollout, a new Flex constraint, or an API-version bump that's not in this skill, **patch it immediately** with `skill_manage(action='patch')`. The whole skill rests on the assumption that what's in here matches what Azure actually accepts.

## Auth

Either an `az login` session (must be a **Microsoft Entra ID** account for Express. personal Microsoft accounts are blocked in preview), or these env vars for unattended/CI use:

- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

## Commands

| Command                                          | What it does                                                  |
| ------------------------------------------------ | ------------------------------------------------------------- |
| `deploy-azure init [--profile express\|flex\|consumption]` | Scan the cwd, write `azure.toml`. Default profile: `express`. |
| `deploy-azure up [--profile X]`                  | Idempotent: build via `az acr build`, push, ensure RG/ACR/env/app/SWA. |
| `deploy-azure db add postgres`                   | Provision a Postgres Flexible Server, save the conn string.   |
| `deploy-azure domain add <host>`                 | Bind a custom hostname to the frontend or backend.            |
| `deploy-azure logs [--tail]`                     | Stream container logs.                                        |
| `deploy-azure status`                            | Show URLs and a resource table.                               |
| `deploy-azure destroy`                           | Delete the resource group.                                    |

## Profile constraints (validated 2026-05-16)

### Express (default)
- **Regions**: `westcentralus`, `eastasia` only (Public Preview). Locations resolve to a "Stage" sub-region under the hood (e.g. `northcentralusstage`): this is normal.
- **Max 2 replicas** per app in preview. Scale-to-zero supported.
- **HTTP only.** No TCP, no VNet, no managed identity yet.
- **No personal MSAs**: Entra ID accounts only.
- **New portal**: `https://containerapps.azure.com`.

### Flex (fallback)
- **CPU/memory** must be one of: `0.25/1Gi`, `0.5/2Gi`, `1/4Gi`, `2/8Gi`, `4/16Gi`, `8/32Gi`, `16/64Gi`, `32/128Gi`. Any other combo → `ContainerAppInvalidResourceTotal`.
- **minReplicas ≥ 1** in preview (no scale-to-zero yet).
- **Regions**: `westeurope`, `eastus`, `eastus2` confirmed.

### Consumption (GA)
- Everywhere. No preview gotchas. Use this if you need a region that neither Express nor Flex supports.

## Workflow

1. `cd` into the project (must contain a Dockerfile and/or a Next.js app).
2. `deploy-azure init`: writes `azure.toml`. Edit it if you want.
3. (Optional) `deploy-azure db add postgres`.
4. `deploy-azure up`. First Express deploy ≈ 1-2 min; first Flex deploy ≈ 5 min.
5. Get a URL, ship.

## See also

- `references/troubleshooting.md`: error catalog with fixes.
- `references/arm-rest-patterns.md`: exact ARM bodies for Flex env + app.
- `references/express-vs-flex.md`: when to pick which profile.
- `templates/`: ready-to-copy `azure.toml`, `Dockerfile.fastapi`, ARM JSON.
