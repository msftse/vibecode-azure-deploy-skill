# How it works

`deploy-azure` is a thin Python wrapper around two things:

1. The Azure CLI (`az`) for the surfaces that have stable, friendly commands — Resource Groups, Container Registry, Static Web Apps, Postgres Flexible Server, custom domains.
2. Raw **ARM REST** calls (via `az rest`) for the Container Apps Flex workload profile, because the az CLI hasn't shipped a friendly `--profile flex` flag yet.

## Why ARM REST for Flex

The Flex workload profile is the runtime formerly pitched as "Container Apps Express": sub-second cold starts, per-second billing, 0.25–32 vCPU. It is fully GA on the ARM control plane under api-version `2025-10-02-preview`, but `az containerapp env create` (as of az 2.85) only accepts the older Consumption / Premium workload profile shapes.

Rather than wait for the CLI bits to ship, we PUT directly to ARM:

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

Empirically:
- Flex managed environment: **~3 minutes** from PUT to `Succeeded`.
- Container app on an existing Flex env: **~30 seconds**.

## Switching back to the az CLI once Microsoft ships the flag

`up --profile consumption` already uses `az containerapp create`. When `--profile flex` lands in `az`, we'll route the Flex path through it too. Until then, the ARM REST path is the documented, supported integration — it's how the portal does it.

## Idempotency

Every subcommand of `up` is a GET-then-PUT. Re-running `deploy-azure up` after a successful deploy:
- Detects existing RG / ACR / env / app via GET.
- Rebuilds and pushes a new image (the cheap part).
- Re-PUTs the container app with the new image digest.
- Returns the same fqdn.
