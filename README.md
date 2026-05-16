<div align="center">

<img src="docs/assets/microsoft-logo.svg" alt="Microsoft" width="64" height="64">

# vibecode-azure-deploy

**A skill that lets AI coding agents ship full-stack apps to Azure with one command. Vercel-grade DX, powered by Azure Container Apps Express.**

<img src="docs/assets/hero-to-build-or-not.jpg" alt="To build or not to build your startup idea" width="60%">

*Stop deliberating. Ship it in 90 seconds and find out.*

> **Built for agents.** This repo is optimized for AI agents (Claude Code, Codex, Cursor, Hermes, OpenCode) to consume as a tool. See [`AGENTS.md`](AGENTS.md) for the machine-readable contract: command shapes, exit codes, idempotency rules, and recovery patterns.

[![License: MIT](https://img.shields.io/badge/license-MIT-0078D4.svg)](LICENSE)
[![Azure](https://img.shields.io/badge/Azure-Container%20Apps%20Express-0078D4.svg?logo=microsoftazure&logoColor=white)](https://learn.microsoft.com/azure/container-apps/express-overview)
[![Preview](https://img.shields.io/badge/preview-2026--05-orange.svg)](#status-and-roadmap)
[![PRs welcome](https://img.shields.io/badge/PRs-welcome-243A5E.svg)](CONTRIBUTING.md)
[![Made by @msftse](https://img.shields.io/badge/made%20by-%40msftse-243A5E.svg)](https://github.com/msftse)

</div>

---

## Why this exists

Vibe-coded apps need to ship the moment they work. Azure already has the primitives to match what Vercel does. Static Web Apps for the frontend, Container Apps Express for the backend (per-second billing, sub-second cold starts, scale-to-zero, no environment to provision), Postgres Flexible Server for data. The developer-experience gap has been the problem, not the platform. Most tutorials still want you to wire ARM templates, learn Bicep, or click through six portal blades. This skill closes that gap. One TOML file, one command, one URL.

> **What is Container Apps Express?** Announced [May 2026 on the Apps on Azure blog](https://techcommunity.microsoft.com/blog/appsonazureblog/introducing-azure-container-apps-express/4519150), Express is an environment-mode that goes from a container image to a public URL on Azure with no env config. Bring an image, Express handles the rest. It was built for SaaS apps, AI app frontends, MCP servers, and agent endpoints.

## <img src="docs/assets/microsoft-logo.svg" width="20" height="20" alt=""> Architecture

<img src="docs/architecture.svg" alt="vibecode-azure-deploy architecture" width="100%">

- **Agent** runs `deploy-azure up` after a one-time `init`.
- The **CLI** is a single stdlib-only Python script. No pip installs, no node_modules.
- For **Express**, the script uses `az containerapp env create --environment-mode express` (`containerapp` extension ≥ 1.3.0b4), with full first-class CLI support.
- For **Flex** (the fallback profile for regions where Express isn't available yet), the CLI talks directly to the **ARM REST API** (`Microsoft.App` provider, api-version `2025-10-02-preview`), because `az` hasn't shipped a friendly workload-profile flag yet.
- For everything else (ACR, Postgres, Static Web Apps, custom domains), it shells out to `az`.
- Provisioning is idempotent. Every step is a GET-then-PUT, so re-running `up` is always safe.
- Images are built in the cloud via `az acr build`, so no local Docker daemon is required.

## <img src="docs/assets/microsoft-logo.svg" width="20" height="20" alt=""> Quickstart

```bash
git clone https://github.com/msftse/vibecode-azure-deploy-skill
cd vibecode-azure-deploy-skill/examples/hello-fullstack
../../skill/scripts/deploy-azure init           # writes azure.toml, profile=express
../../skill/scripts/deploy-azure up
# => https://your-app.eastasia.azurecontainerapps.io
```

Prereqs: `az` ≥ 2.85, the `containerapp` extension ≥ 1.3.0b4 (`az extension update -n containerapp`), Python 3.11+, an `az login` session backed by a Microsoft Entra ID account (personal Microsoft accounts aren't supported by Express). No local Docker required.

### Live proof

Two apps were deployed end-to-end with this script on the Flex profile in West Europe.

**deadpool** (full-stack, May 2026) - a graveyard of dead startup ideas with Shakespearean eulogies. FastAPI + Postgres Flexible Server + static frontend, all behind one Container App. Scaffolded, provisioned, and deployed by an AI agent following [`AGENTS.md`](AGENTS.md):

```
GET  https://ca-deadpool.kindflower-420c2c9e.westeurope.azurecontainerapps.io/healthz
=> 200 {"ok": true}

POST https://ca-deadpool.kindflower-420c2c9e.westeurope.azurecontainerapps.io/api/ideas
=> 201 {"id":1,"name":"NFT Litter Box","eulogy":"Lo, where NFT Litter Box now sleepeth!..."}
```

Wall time: cloud build ~35s, managed env ~3 min (cold ARM region), container app ~30s. Repo: [github.com/msftse/deadpool](https://github.com/msftse/deadpool) (if published).

**ca-vibecode-demo** (backend-only smoke):

```
GET https://ca-vibecode-demo.delightfulhill-c9a8cab6.westeurope.azurecontainerapps.io/healthz
=> 200 {"ok": true}
```

Build: ~45s (cloud build). Env: ~20s. App: ~15s. Total wall: ~90s (env was already warm).

Express deploys in the supported preview regions (West Central US, East Asia) finish noticeably faster. Microsoft's announcement post calls out sub-second cold starts and "running in seconds, not minutes" because there's no env to provision.

## <img src="docs/assets/microsoft-logo.svg" width="20" height="20" alt=""> What you get

| Feature                | vibecode-azure (Express)          | Vercel                            |
| ---------------------- | --------------------------------- | --------------------------------- |
| One-command deploy     | ✅ `deploy-azure up`              | ✅ `vercel`                       |
| Bring-your-own Docker  | ✅ any container, any language    | ❌ Functions only                 |
| Long-running processes | ✅ no timeout                     | ❌ max 5 min (Pro)                |
| Per-second billing     | ✅ Express, Flex                  | ❌ per-invocation                 |
| Scale-to-zero          | ✅ Express                        | ✅                                |
| Sub-second cold start  | ✅ Express                        | ✅                                |
| PR previews            | ⏳ on the roadmap                | ✅                                |

Full table in [`docs/comparison-vercel.md`](docs/comparison-vercel.md).

## <img src="docs/assets/microsoft-logo.svg" width="20" height="20" alt=""> The Express path

Container Apps Express removes the managed-environment configuration surface entirely. You don't pick a workload profile, you don't size compute, and you don't write scaling rules. Azure provisions a lightweight, fully managed environment on shared sandbox capacity, applies production defaults, and gives you a public URL.

The full creation flow is two CLI calls:

```bash
az containerapp env create \
  --environment-mode express \
  --name my-env --resource-group my-rg --logs-destination none

az containerapp create \
  --name my-app --resource-group my-rg --environment my-env \
  --image myacr.azurecr.io/my-app:latest \
  --target-port 8000 --ingress external
```

That's it. The env response carries `properties.environmentMode = "Express"`, the app inherits scale-to-zero, and you're live.

For regions where Express isn't available yet, the script falls back to the Flex workload profile. Flex is a more configurable per-second-billed profile we provision via raw ARM REST against `Microsoft.App` (api-version `2025-10-02-preview`):

```json
{
  "location": "westeurope",
  "properties": {
    "workloadProfiles": [
      { "name": "Flex", "workloadProfileType": "Flex" }
    ]
  }
}
```

See [`docs/how-it-works.md`](docs/how-it-works.md) and [`skill/references/arm-rest-patterns.md`](skill/references/arm-rest-patterns.md) for the full request bodies and ARM endpoints.

## <img src="docs/assets/microsoft-logo.svg" width="20" height="20" alt=""> Install as a Hermes skill

```bash
hermes skills install https://github.com/msftse/vibecode-azure-deploy-skill
```

Or the manual path. Clone and symlink:

```bash
git clone https://github.com/msftse/vibecode-azure-deploy-skill ~/code/vibecode-azure-deploy-skill
mkdir -p ~/.hermes/skills/devops
ln -s ~/code/vibecode-azure-deploy-skill/skill ~/.hermes/skills/devops/deploy-azure
```

For research and validation of any Azure surface this skill touches, wire in the official Microsoft Learn MCP server:

```yaml
# ~/.hermes/config.yaml
mcp_servers:
  microsoft-learn:
    url: https://learn.microsoft.com/api/mcp
```

That gives any agent using this skill three tools (`microsoft_docs_search`, `microsoft_code_sample_search`, `microsoft_docs_fetch`) backed by the live Microsoft Learn corpus. It's the source of truth for every Azure API call this script makes.

## <img src="docs/assets/microsoft-logo.svg" width="20" height="20" alt=""> Commands

| Command                          | Purpose                                                              |
| -------------------------------- | -------------------------------------------------------------------- |
| `deploy-azure init`              | Scan the cwd, write `azure.toml`. Defaults to `--profile express`.   |
| `deploy-azure up`                | Idempotent build, push, and provision.                               |
| `deploy-azure db add postgres`   | Provision a Postgres Flexible Server.                                |
| `deploy-azure domain add <host>` | Bind a custom domain (frontend or backend).                          |
| `deploy-azure logs --tail`       | Stream backend container logs.                                       |
| `deploy-azure status`            | Show URLs and a resource table.                                      |
| `deploy-azure destroy`           | Delete the resource group.                                           |

Profiles: `express` (default, preview, West Central US / East Asia). `flex` (workload profile, preview, West Europe / East US / East US 2). `consumption` (GA, every region).

## <img src="docs/assets/microsoft-logo.svg" width="20" height="20" alt=""> Status and roadmap

- [x] Container Apps Express environment-mode (preview, May 2026)
- [x] Container Apps Flex workload profile (ARM REST fallback)
- [x] Consumption profile (GA fallback)
- [x] Static Web Apps frontend
- [x] Postgres Flexible Server
- [x] Custom domains
- [x] Cloud-side image builds via `az acr build`, no local Docker required
- [ ] Express expanded region availability (Microsoft is rolling out, the script auto-uses any new region passed via `--region`)
- [ ] Express autoscaling, VNet, managed identity, custom domains (preview gaps, Microsoft is filling them on the road to GA)
- [ ] PR preview deployments
- [ ] GPU containers (Consumption-GPU profile)

## FAQ

**How much does this cost?**
Express runs on consumption-based CPU with per-second billing and scale-to-zero, so an idle Express app costs $0. Under traffic, expect tens of cents per million requests for typical web workloads. Flex (fallback): a 0.5 vCPU / 2Gi backend with `minReplicas=1` is about $13/month at list prices. Postgres B1ms is about $13/month. SWA Free tier is $0.

**Which regions are supported?**
- Express: West Central US, East Asia (Public Preview, May 2026). Microsoft is expanding.
- Flex: West Europe, East US, East US 2 (preview).
- Consumption: every Container Apps region (GA).

The script picks the right profile automatically based on `--region`, and warns then falls back when it sees a region that doesn't match the requested profile.

**Why not just use `az containerapp up`?**
`az containerapp up` works great for the Consumption profile. But it doesn't yet wire identity-aware ingress safely in Express preview stage regions, it doesn't speak Flex via a friendly flag, and we also wanted one command that wires Static Web Apps, Postgres, and custom domain. That's the gap.

**How do I migrate off this later?**
Everything provisioned is standard ARM. Your image is a normal OCI artifact in a normal ACR. You can `az containerapp show ... -o yaml > app.yaml`, take it to Bicep, Terraform, or Pulumi, and never look back. No lock-in.

**Is this official Microsoft?**
No. This is a community-built skill by [@msftse](https://github.com/msftse) (a Microsoft STU in Israel), and it uses only documented, supported Azure APIs. The Azure team isn't behind it, but every primitive it calls is.

## Acknowledgments

Built on top of work shipped by the Microsoft Azure Container Apps team. See [Introducing Azure Container Apps Express](https://techcommunity.microsoft.com/blog/appsonazureblog/introducing-azure-container-apps-express/4519150), the [Express overview](https://learn.microsoft.com/azure/container-apps/express-overview), and the [Express FAQ](https://learn.microsoft.com/azure/container-apps/express-faq). They did the hard part. This skill is the wrapper that makes it one command.

This project is community-built and unaffiliated with Microsoft. "Microsoft", "Azure", "Container Apps", and "Static Web Apps" are trademarks of Microsoft Corporation. The Microsoft logo is used per Microsoft's [Trademark & Brand Guidelines](https://www.microsoft.com/en-us/legal/intellectualproperty/trademarks) for referential use only.

## License

MIT. See [LICENSE](LICENSE).
