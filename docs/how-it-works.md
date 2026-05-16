# How it works

`deploy-azure` is a thin Python wrapper around three things:

1. The Azure CLI (`az`) for the surfaces that have stable, friendly commands — Resource Groups, Container Registry, Static Web Apps, Postgres Flexible Server, custom domains.
2. The **`containerapp` extension** (≥ 1.3.0b4) for Container Apps **Express** — `az containerapp env create --environment-mode express` is the canonical way to spin up an Express env.
3. Raw **ARM REST** calls (via `az rest`) for the Container Apps **Flex** workload profile, because the az CLI hasn't shipped a friendly workload-profile flag yet.

## The Express path (default)

Container Apps Express was announced [in May 2026 on the Apps on Azure blog](https://techcommunity.microsoft.com/blog/appsonazureblog/introducing-azure-container-apps-express/4519150). It's the new "Vercel for Azure" environment-mode — no managed environment to configure, sub-second cold starts, scale-to-zero, per-second billing, HTTP-only.

The whole creation flow is two CLI calls:

```bash
az containerapp env create \
  --environment-mode express \
  --name my-env -g my-rg --logs-destination none

az containerapp create \
  --name my-app -g my-rg --environment my-env \
  --image myacr.azurecr.io/my-app:latest \
  --target-port 8000 --ingress external
```

The env response carries `properties.environmentMode = "Express"` and `properties.workloadProfiles[].name = "Consumption"` (Express runs on shared consumption capacity under the hood). The app inherits Express defaults: scale-to-zero, max 2 replicas in preview, HTTP-only ingress.

Preview region availability is enforced by Azure itself: today Express only accepts `westcentralus` and `eastasia`. The script auto-falls-back to the Flex profile when the user's region isn't supported.

## Why ARM REST for Flex (fallback)

The Flex workload profile predates Express on the ARM control plane (api-version `2025-10-02-preview`), but `az containerapp env create` (as of az 2.85) doesn't expose a friendly `--workload-profile flex` flag. Rather than wait, we PUT directly to ARM:

```
PUT https://management.azure.com/subscriptions/{sub}/resourceGroups/{rg}
    /providers/Microsoft.App/managedEnvironments/{env}
    ?api-version=2025-10-02-preview

{
  "location": "westeurope",
  "properties": {
    "workloadProfiles": [
      { "name": "Flex", "workloadProfileType": "Flex" }
    ]
  }
}
```

The container app itself is a second PUT against `Microsoft.App/containerApps` that references the env's ARM ID and sets `workloadProfileName: "Flex"` on the template. See `skill/references/arm-rest-patterns.md` for the full request bodies.

## Provisioning loop

ARM is asynchronous. After each PUT, the script polls the resource's `properties.provisioningState` field with exponential backoff (4s → 6s → 9s → ... capped at 20s) until it sees `Succeeded`, or `Failed` / `Canceled`, or a timeout (8 min for env, 2 min for app).

Empirically (validated 2026-05-16):
- Express managed environment: **~20 seconds** from PUT to `Succeeded`.
- Flex managed environment: **~3 minutes** from PUT to `Succeeded`.
- Container app on an existing env: **~15-30 seconds**.

## Switching back to the az CLI once Microsoft ships the Flex flag

When `--workload-profile flex` lands in `az containerapp env create`, we'll route the Flex path through it too. The Express path already uses the CLI. Until Flex moves, the ARM REST path is the documented, supported integration — it's how the portal does it.

## Idempotency

Every subcommand of `up` is a GET-then-PUT. Re-running `deploy-azure up` after a successful deploy:
- Detects existing RG / ACR / env / app via GET.
- Rebuilds and pushes a new image via `az acr build` (cloud build, ~45s typical).
- Re-PUTs / `az containerapp update`s the container app with the new image digest.
- Returns the same fqdn.

## Source of truth for Azure API shapes

This skill assumes the Azure surface keeps moving. **Before changing any ARM body, region claim, SKU, or CLI flag, query the Microsoft Learn MCP** (`microsoft_docs_search`, `microsoft_code_sample_search`, `microsoft_docs_fetch` — hosted at `https://learn.microsoft.com/api/mcp`). Don't guess, don't trust generic search results. The MCP is wired into the recommended Hermes config and surfaces the canonical learn.microsoft.com corpus directly.
