# Contributing

Thanks for the interest. This project is small and pragmatic. PRs welcome.

> Most contributors here will be AI coding agents. The norms below are written to be machine-readable. See [`AGENTS.md`](AGENTS.md) for the runtime contract.

## Ground rules

- The `deploy-azure` script is **stdlib-only**. No `requests`, no `pyyaml`, nothing pip-installed. If you need a dependency, justify it in the PR.
- The script must keep working on Python 3.11+. It re-execs under a newer interpreter if invoked under 3.9.
- **Idempotency is sacred.** `deploy-azure up` must be safe to re-run.
- **Non-interactivity is sacred.** No `input()`, no TTY prompts. New flags add behavior; nothing blocks waiting on a user.
- ARM api-version is pinned to `2025-10-02-preview` until we have a reason to move.
- If you change any command's exit code, stdout shape, or recovery semantics, update `AGENTS.md` in the same PR.

## Dev loop (works the same for humans and agents)

```bash
git clone https://github.com/msftse/vibecode-azure-deploy-skill
cd vibecode-azure-deploy-skill

# syntax check (run this before every commit)
python3 -c "import ast; ast.parse(open('skill/scripts/deploy-azure').read())"

# CLI smoke
python3 skill/scripts/deploy-azure --help
cd examples/hello-fullstack
python3 ../../skill/scripts/deploy-azure init --dry-run
```

## Pull requests

1. Open an issue first for non-trivial work.
2. Keep commits scoped and conventional (`feat:`, `fix:`, `docs:`, `chore:`).
3. Update the relevant doc under `docs/` or `skill/references/` if you change behavior.
4. Update `AGENTS.md` if you change any agent-facing contract.
5. CI runs a syntax check and a config-schema lint. Both must pass.

## Reporting bugs

Please include: `az --version`, region, profile (`express` / `flex` / `consumption`), and the full output of the failing command. If you're an agent reporting on behalf of a user, attach the JSON or text the script printed, not your paraphrase.
