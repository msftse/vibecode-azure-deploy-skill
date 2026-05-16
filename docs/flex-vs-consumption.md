# Flex vs Consumption — which profile?

Container Apps offers several workload profiles. `deploy-azure` supports two of them today.

## TL;DR

| Use case                                   | Profile        |
| ------------------------------------------ | -------------- |
| Vibe-coded app, low-to-medium traffic      | **Flex**       |
| Background workers, batch, scale-to-zero   | **Consumption**|
| Production API with predictable load       | **Flex**       |
| Demo you want to cost ~$0 when idle        | **Consumption**|

## Flex (default)

- **CPU/memory pairs (exact):** 0.25/1Gi, 0.5/2Gi, 1/4Gi, 2/8Gi, 4/16Gi, 8/32Gi, 16/64Gi, 32/128Gi. Any other combo is rejected by ARM with `ContainerAppInvalidResourceTotal`.
- **Cold start:** sub-second.
- **Billing:** per-second, only when a replica is up.
- **Min replicas:** must be ≥ 1 during preview. (Scale-to-zero on the roadmap.)
- **Max replicas:** up to 1000 per app.
- **Cost ceiling at idle (1× minReplicas at 0.5/2Gi):** roughly $13/month at westeurope list prices. Cheaper if you stop the env.

## Consumption

- **CPU/memory:** any value in the continuous range (0.25–2.0 vCPU, 0.5–4Gi).
- **Cold start:** 5–15s typical when scaling from zero.
- **Billing:** per-second, with a generous free tier (180k vCPU-seconds + 360k GiB-seconds per month).
- **Min replicas:** 0 supported — true scale-to-zero.
- **Max replicas:** 300 per app.

## Decision tree

1. Does the app need to respond fast to a single user hitting it after an idle period?
   → **Flex** (sub-second cold start beats the consumption free tier).
2. Is cost-at-idle more important than latency?
   → **Consumption** with `min_replicas = 0`.
3. Are you running a Celery/RQ-style worker queue?
   → **Consumption** with KEDA scalers (auto-handled by ACA).
4. Production HTTP API, latency SLO, predictable cost?
   → **Flex**.

## Migrating between them

`deploy-azure` will recreate the managed environment if you flip the profile in `azure.toml`. It does **not** delete the old env automatically — destroy the resource group or remove the env manually after cutover.

```toml
[backend]
profile = "consumption"   # was "flex"
cpu = 0.5
memory = "1Gi"
min_replicas = 0
```
