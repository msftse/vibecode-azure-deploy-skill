# Troubleshooting

## `ARM REST GET ... failed: ResourceNotFound` on managed env or container app

You're on a deploy-azure script older than commit `c6c0906` (May 2026). That version raised on the GET-existence check used to make provisioning idempotent. `pull` the latest and re-run `deploy-azure up` — it will resume from the failed step. The fix lives in `az_rest()`: GETs that return 404 now return `None` so the caller falls through to `PUT`.

## `--profile express` deploys but lands on Flex anyway

You passed a region that isn't in the Express preview list (`westcentralus`, `eastasia`). The script downgrades the profile and prints a warning. To get true scale-to-zero Express, rerun with `--region westcentralus` or `--region eastasia`.

## `ContainerAppInvalidResourceTotal`

You picked a CPU/memory combo that isn't on the Flex matrix. Allowed pairs:

```
0.25 / 1Gi     0.5 / 2Gi     1 / 4Gi      2 / 8Gi
4 / 16Gi       8 / 32Gi      16 / 64Gi    32 / 128Gi
```

Edit `[backend] cpu = ... memory = "..."` in `azure.toml`, re-run `up`.

## Managed env stuck in `Provisioning` past 5 min

ARM occasionally takes longer for first-ever Flex env in a region. The script polls up to 8 minutes; if it times out, GET the env in the portal — usually it finishes shortly after. Re-running `up` is safe.

## `ACR name not available`

Container Registry names are globally unique. The script auto-retries with a 4-hex-char suffix and rewrites `azure.toml`. If you keep hitting collisions, pick a more unique `[backend] acr_name`.

## `RegistryAuthFailed` on app create

The ACR admin user is created via `--admin-enabled true`. If the script ran before `az acr create` finished propagating, the credential pull can fail. Re-run `deploy-azure up`.

## SWA `create` fails with "no source"

`az staticwebapp create` without `--source` creates an unlinked SWA — which is what we want for the CLI-deploy flow. If you see an error, you might be on an older `az` version. Upgrade: `az upgrade`.

## `az login` opens a browser in CI

Set the four `AZURE_*` env vars (`AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, `AZURE_TENANT_ID`, `AZURE_SUBSCRIPTION_ID`) and the script will use service-principal auth automatically.

## Custom domain stuck on "Validating"

You need a CNAME from your hostname to the SWA / ACA default hostname **before** binding. `deploy-azure domain add` prints the exact record when binding fails.

## "Postgres connection refused" from the container

Postgres Flexible Server is created with `--public-access 0.0.0.0` — i.e. the firewall allows all Azure-internal IPs. If you tightened that, you'll need to add a VNet integration; see the `flex-vs-consumption` doc for the VNet-injected env shape.

## "Docker buildx target platform required"

The script always passes `--platform linux/amd64`. If you see this anyway, you may be on an old Docker without buildx; install Docker Desktop ≥ 4.27 or enable buildx.
