# Contributing

Thanks for the interest. This project is small and pragmatic; PRs are very welcome.

## Ground rules

- The `deploy-azure` script is **stdlib-only**. No `requests`, no `pyyaml`, nothing pip-installed. If you need a dependency, justify it in the PR.
- The script must keep working on Python 3.11+. It re-execs under a newer interpreter if invoked under 3.9.
- Idempotency is sacred. `deploy-azure up` must be safe to re-run.
- ARM api-version is pinned to `2025-10-02-preview` until we have a reason to move.

## Dev loop

```bash
git clone https://github.com/msftse/vibecode-azure-deploy-skill
cd vibecode-azure-deploy-skill
python3 skill/scripts/deploy-azure --help
cd examples/hello-fullstack
python3 ../../skill/scripts/deploy-azure init --dry-run
```

## Pull requests

1. Open an issue first for non-trivial work.
2. Keep commits scoped and conventional (`feat:`, `fix:`, `docs:`, `chore:`).
3. Update the relevant doc under `docs/` if you change behavior.
4. The CI workflow runs a syntax check and a config-schema lint — both must pass.

## Reporting bugs

Please include: az CLI version (`az --version`), region, and the full output of the failing command with `--debug` if applicable.
