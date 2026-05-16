# vibecode-azure vs Vercel

A direct, honest comparison. Vercel is excellent — this project exists because Azure has the raw infra to match it, not because Vercel is bad.

| Feature                          | vibecode-azure (Flex)                         | Vercel                                |
| -------------------------------- | --------------------------------------------- | ------------------------------------- |
| One-command deploy               | `deploy-azure up`                             | `vercel`                              |
| Frontend hosting                 | Static Web Apps (global CDN, free tier)       | Vercel Edge Network                   |
| Server-side runtime              | Container Apps (Flex profile)                 | Vercel Functions (Node, Python, Go)   |
| Long-running processes           | ✅ Full container, any language               | ❌ Function timeout (max 5 min Pro)   |
| Bring-your-own Dockerfile        | ✅                                            | ❌ (Functions only)                   |
| Managed Postgres                 | ✅ Postgres Flexible Server                   | ✅ Vercel Postgres                    |
| Custom domains + TLS             | ✅ ACME via SWA / ACA                         | ✅                                    |
| Per-second billing               | ✅ Flex                                       | ❌ per-invocation                     |
| Cold start                       | sub-second (Flex)                             | sub-second (Edge), 1–3s (Lambda)      |
| Scale-to-zero                    | ⏳ preview unlock pending                     | ✅                                    |
| Preview deploys per-PR           | ⏳ on the roadmap                             | ✅                                    |
| GPU containers                   | ⏳ Consumption-GPU on the roadmap             | ❌                                    |
| Region selection                 | ✅ westeurope / eastus / eastus2 (Flex)       | ✅ (regional Functions only on Pro+)  |
| Compliance posture               | Azure (SOC, ISO, FedRAMP, etc.)               | SOC 2                                 |
| Lock-in                          | Standard ARM + OCI images                     | Vercel-specific function shape        |
| Cost at idle (1 small backend)   | ~$13/mo (Flex minReplicas=1)                  | $0 on Hobby                           |
| Cost at scale (10 req/s, 1GB)    | ~$25–40/mo                                    | ~$20–60/mo depending on plan          |
| OSS / runs anywhere              | ✅ MIT, just `az` + `docker`                  | ❌ Vercel platform required           |

## Where Vercel still wins

- **PR previews out of the box.** We don't have this yet.
- **$0 idle cost on Hobby.** Flex preview can't scale to zero — coming soon, but not today.
- **Frontend framework integrations.** Vercel's Next.js / SvelteKit adapter polish is unmatched.

## Where vibecode-azure wins

- **Long-running anything.** Full container, no timeout.
- **Compliance-grade hosting** for shops that have to be on Azure anyway.
- **No vendor-specific function shape.** Your Dockerfile runs anywhere.
- **Per-second billing on Flex** beats Vercel Function pricing once you have steady traffic.

Use what fits. This project exists for the case where you need Azure-grade infra but want the Vercel-grade DX of "git push, get a URL".
