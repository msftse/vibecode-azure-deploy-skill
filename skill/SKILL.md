---
name: deploy-azure
description: One-command fullstack deploys to Azure — Static Web Apps + Container Apps (Flex profile) + Postgres Flexible Server. Vercel-grade DX, idempotent, stdlib-only Python CLI.
when_to_use: User wants to ship a web app or fullstack project to Azure with minimal config. Especially useful for vibe-coded prototypes, FastAPI/Flask + Next.js apps, or anything where you'd reach for `vercel` if it were running on Azure. Default backend profile is the new Container Apps Flex workload type.
---

# deploy-azure

A skill that ships full-stack apps to Azure with one command:

```bash
deploy-azure init     # scans the repo, writes azure.toml
deploy-azure up       # builds, pushes, and provisions everything via ARM
```

## What it provisions

- **Frontend**: Azure Static Web Apps (Free SKU, global CDN). Auto-detected from `next.config.*` or a Next.js `package.json`.
- **Backend**: Azure Container Apps on the **Flex** workload profile (the new "Container Apps Express" SKU). Auto-detected from a shallowest `Dockerfile`. Provisioned via ARM REST `PUT` against `Microsoft.App/managedEnvironments` and `Microsoft.App/containerApps` (api-version `2025-10-02-preview`), because the az CLI hasn't shipped a friendly `--profile flex` flag yet.
- **Database**: Postgres Flexible Server (Burstable B1ms), with the connection string injected as an ACA secret named `database-url` and surfaced to the container as `DATABASE_URL`.
- **Custom domain**: bound via SWA `hostname set` or ACA `hostname bind` with CNAME validation.

## Tools required on PATH

- `az` (Azure CLI, ≥ 2.85) — includes `az acr build`, which we use to build images in the cloud
- Python 3.11+ (the script re-execs under a newer interpreter if invoked under 3.9)

> No local Docker daemon required. Images are built and pushed by `az acr build` running on ACR's own build agent. This sidesteps Docker Desktop credential-helper hangs and works inside CI runners that don't have Docker available.

## Researching Azure APIs

Before changing any ARM body, region availability claim, SKU list, or preview-API behaviour in this skill, query the official Microsoft docs via the **Microsoft Learn MCP** (`mcp_microsoft_learn_*` tools). It's the canonical source — fresher than Stack Overflow, less hallucinated than a web search.

Recommended queries:

- `microsoft_docs_search("Container Apps Flex workload profile workloadProfileType")` — for the env/app ARM body shape
- `microsoft_code_sample_search("az acr build linux/amd64")` — for the build/push pipeline
- `microsoft_docs_fetch(url)` — to pull a specific learn.microsoft.com page in full

If you discover a Flex constraint, a new region, or an API-version bump that's not in this skill, patch it.

## Auth

Either an `az login` session, or these env vars for unattended/CI use:

- `AZURE_CLIENT_ID`
- `AZURE_CLIENT_SECRET`
- `AZURE_TENANT_ID`
- `AZURE_SUBSCRIPTION_ID`

## Commands

| Command                              | What it does                                                  |
| ------------------------------------ | ------------------------------------------------------------- |
| `deploy-azure init [--profile flex]` | Scan the cwd, write `azure.toml`.                             |
| `deploy-azure up [--profile X]`      | Idempotent: build, push, ensure RG/ACR/env/app/SWA.           |
| `deploy-azure db add postgres`       | Provision a Postgres Flexible Server, save the conn string.   |
| `deploy-azure domain add <host>`     | Bind a custom hostname to the frontend or backend.            |
| `deploy-azure logs [--tail]`         | Stream container logs.                                        |
| `deploy-azure status`                | Show URLs and a resource table.                               |
| `deploy-azure destroy`               | Delete the resource group.                                    |

## Flex profile constraints

- **CPU/memory** must be one of: `0.25/1Gi`, `0.5/2Gi`, `1/4Gi`, `2/8Gi`, `4/16Gi`, `8/32Gi`, `16/64Gi`, `32/128Gi`. Any other combo → `ContainerAppInvalidResourceTotal`.
- **minReplicas ≥ 1** in preview (scale-to-zero is on Microsoft's roadmap).
- **Regions**: `westeurope`, `eastus`, `eastus2` confirmed. Others may work.

## Workflow

1. `cd` into the project (must contain a Dockerfile and/or a Next.js app).
2. `deploy-azure init` — writes `azure.toml`. Edit it if you want.
3. (Optional) `deploy-azure db add postgres`.
4. `deploy-azure up`. First deploy ≈ 5 min. Subsequent ≈ 1 min.
5. Get a URL, ship.

## See also

- `references/troubleshooting.md` — error catalog with fixes.
- `references/arm-rest-patterns.md` — exact ARM bodies for Flex env + app.
- `templates/` — ready-to-copy `azure.toml`, `Dockerfile.fastapi`, ARM JSON.
