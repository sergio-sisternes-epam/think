# Contributing

Thank you for your interest in contributing to `think`.

## Prerequisites

| Tool | Minimum version | Install |
|------|----------------|---------|
| Git | 2.x | [git-scm.com](https://git-scm.com) |
| APM CLI | 0.28.0 (see `apm-version` in workflows) | Use `microsoft/apm-action@v1` in CI; pin the same version locally |

## Repository structure

```
├── apm.yml
├── .apm/skills/               # Author skills here
│   ├── think-challenge/SKILL.md
│   ├── think-grill/SKILL.md
│   └── think-ramble/SKILL.md
├── .github/workflows/         # microsoft/apm-action compile checks
└── CONTRIBUTING.md
```

This is a single APM package, not a marketplace. Do not add a `marketplace:` block or `packages/` tree.

## Development workflow

1. Create a feature branch from `main`.
2. Edit skills under `.apm/skills/<name>/SKILL.md`.
3. Validate before pushing:

   ```bash
   apm compile --dry-run --verbose
   ```

4. Open a pull request against `main`.

## Commit conventions

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>
```

Examples:
- `feat(think-grill): tighten question limits`
- `docs: clarify conversation-only install`
