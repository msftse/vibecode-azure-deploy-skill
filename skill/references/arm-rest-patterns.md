# ARM REST patterns

`deploy-azure` provisions Flex resources via raw ARM REST. This doc shows the exact requests so you can reproduce them by hand or port the logic to another language.

All endpoints use api-version **`2025-10-02-preview`**.

## 1. Create a Flex managed environment

```http
PUT /subscriptions/{SUB}/resourceGroups/{RG}
    /providers/Microsoft.App/managedEnvironments/{ENV}
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

The first `Flex` is the profile **name** (you reference it from container apps). The second is the profile **type** (the SKU). They can differ if you want multiple Flex profiles in one env; we keep them identical.

Provisioning is async. Poll the same URL until `properties.provisioningState == "Succeeded"` (~3 minutes).

## 2. Create a container app on the Flex profile

```http
PUT /subscriptions/{SUB}/resourceGroups/{RG}
    /providers/Microsoft.App/containerApps/{APP}
    ?api-version=2025-10-02-preview
```

Body:

```json
{
  "location": "westeurope",
  "properties": {
    "environmentId": "/subscriptions/{SUB}/resourceGroups/{RG}/providers/Microsoft.App/managedEnvironments/{ENV}",
    "workloadProfileName": "Flex",
    "configuration": {
      "ingress": {
        "external": true,
        "targetPort": 8000,
        "transport": "auto"
      },
      "registries": [{
        "server": "{ACR}.azurecr.io",
        "username": "{USER}",
        "passwordSecretRef": "registry-password"
      }],
      "secrets": [
        { "name": "registry-password", "value": "{PW}" },
        { "name": "database-url",      "value": "{CONN}" }
      ]
    },
    "template": {
      "containers": [{
        "name": "{APP}",
        "image": "{ACR}.azurecr.io/{PROJECT}:latest",
        "resources": { "cpu": 0.5, "memory": "2Gi" },
        "env": [{ "name": "DATABASE_URL", "secretRef": "database-url" }]
      }],
      "scale": {
        "minReplicas": 1,
        "maxReplicas": 10
      }
    }
  }
}
```

Provisioning takes about 30 seconds.

## 3. Doing it by hand with `az rest`

```bash
az rest --method put \
  --url "https://management.azure.com/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.App/managedEnvironments/$ENV?api-version=2025-10-02-preview" \
  --body @env-flex.json \
  --headers "Content-Type=application/json"
```

The CLI handles bearer-token injection from your `az login` session.

## 4. Tearing down

```bash
az group delete -n "$RG" --yes --no-wait
```

The whole RG (env, app, ACR, SWA, Postgres) goes away together. Or, more surgical:

```bash
az rest --method delete \
  --url "https://management.azure.com/subscriptions/$SUB/resourceGroups/$RG/providers/Microsoft.App/containerApps/$APP?api-version=2025-10-02-preview"
```

## 5. Known pitfalls

- The CPU/memory **must** be one of the 8 Flex pairs. ARM returns `ContainerAppInvalidResourceTotal` otherwise.
- `minReplicas` must be ≥ 1 in preview.
- The managed env's `workloadProfiles[*].name` is the value you reference from `containerApps.properties.workloadProfileName`. Mismatch → `WorkloadProfileNotFound`.
- The registry password must live in `properties.configuration.secrets`, not inline. `passwordSecretRef` points at the secret by name.
