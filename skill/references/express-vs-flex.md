# Express vs Flex — when to pick which Container Apps profile

Quick decision table for the `--profile` flag on `deploy-azure init` / `up`.

| Question | Answer |
| --- | --- |
| **My region is West Europe / EU / anywhere outside North America or East Asia** | `flex` (or `consumption`) |
| **My region is West Central US or East Asia, and I want true scale-to-zero** | `express` |
| **I need VNet, managed identity, or custom domains today** | `flex` or `consumption` (Express adds these on the road to GA) |
| **I need TCP ingress** | `flex` or `consumption` (Express is HTTP-only in preview) |
| **I need autoscaling rules (KEDA, queue-length, etc.)** | `flex` or `consumption` (Express has autoscaling on the roadmap) |
| **I'm logging in with a personal Microsoft account (outlook.com, hotmail.com)** | `flex` or `consumption` (Express requires Microsoft Entra ID) |
| **I want the cheapest possible idle cost** | `express` (scale-to-zero) > `consumption` (scale-to-zero) > `flex` (min ≥ 1) |
| **I want the fastest cold start** | `express` (sub-second, per the [announcement blog](https://techcommunity.microsoft.com/blog/appsonazureblog/introducing-azure-container-apps-express/4519150)) |
| **I want zero environment config** | `express` |
| **I want exact CPU/memory pairs and explicit workload profiles** | `flex` |
| **I just want it to work in any region with no preview footguns** | `consumption` |

## The decision the script makes by default

`deploy-azure init` writes `profile = "express"` unless you pass `--profile flex|consumption`. On `up`:

1. If `profile == express` and the region isn't `westcentralus` / `eastasia`, the script warns and **transparently falls back to `flex`** so the deploy still succeeds. You don't have to edit anything.
2. If `profile == flex` and the region isn't in the Flex preview list, the script warns but proceeds — Microsoft is expanding Flex regularly.
3. If `profile == consumption`, the script always proceeds; Consumption is GA everywhere.

## Sources

- [Introducing Azure Container Apps Express (blog, 2026-05)](https://techcommunity.microsoft.com/blog/appsonazureblog/introducing-azure-container-apps-express/4519150)
- [Container Apps Express overview](https://learn.microsoft.com/azure/container-apps/express-overview)
- [Container Apps Express FAQ](https://learn.microsoft.com/azure/container-apps/express-faq)
- [Container Apps workload profiles (Flex)](https://learn.microsoft.com/azure/container-apps/workload-profiles-overview)

When in doubt, consult Microsoft Learn MCP (`microsoft_docs_search`, `microsoft_docs_fetch`) for the latest preview-region list and constraint changes.
