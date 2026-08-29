# Contributing

Thank you for your interest in contributing to this marketplace.

## Prerequisites

| Tool | Minimum version | Install |
|------|----------------|---------|
| Git | 2.x | [git-scm.com](https://git-scm.com) |
| APM CLI | 0.28.0 (see `apm-version` in workflows) | Use `microsoft/apm-action@v1` in CI; pin the same version locally |

## Repository structure

```
├── apm.yml                    # Root marketplace manifest
├── .claude-plugin/
│   └── marketplace.json       # Generated marketplace index (do not edit manually)
├── .github/
│   ├── workflows/             # CI/CD workflows (use microsoft/apm-action)
│   ├── CODEOWNERS             # Review requirements
│   └── ISSUE_TEMPLATE/        # Issue and PR templates
├── packages/                  # ALL packages live here
│   ├── think-challenge/
│   │   ├── apm.yml
│   │   └── SKILL.md
│   ├── think-grill/
│   └── think-ramble/
└── CONTRIBUTING.md            # This file
```

Do not add an Atlas store package to this marketplace.

## Development workflow

1. **Fork and clone** the repository.
2. **Create a feature branch** from `main`:
   ```bash
   git checkout -b feat/my-change main
   ```
3. **Make your changes** and commit following the conventions below.
4. **Run validation locally** before pushing:
   ```bash
   apm marketplace check
   apm pack
   git diff --exit-code .claude-plugin/marketplace.json

   (cd packages/think-challenge && apm compile --dry-run --verbose)
   ```
5. **Open a pull request** against `main`.

## Commit conventions

Use [Conventional Commits](https://www.conventionalcommits.org/) format:

```
<type>(<scope>): <short summary>
```

| Type | When to use |
|------|-------------|
| `feat` | New feature or package |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `chore` | Maintenance (CI, deps, tooling) |
| `refactor` | Code restructuring without behaviour change |

**Examples:**
- `feat(think-grill): tighten question limits`
- `fix(marketplace): use source instead of path in apm.yml`
- `chore(ci): pin APM CLI to 0.28.0`

## Release process

Releases are triggered by pushing a scoped Git tag.

1. Merge your PR to `main` (**merge commit, not squash**).
2. Pull `main` locally.
3. Tag the merge commit: `git tag <name>/v<version>`.
4. Push the tag: `git push origin <name>/v<version>`.
5. CI creates a GitHub Release automatically.

## Squash-merge warning

**Do not squash-merge PRs** that touch package directories. Squash-merging rewrites commit history, making marketplace refs unreachable and breaking `apm install` for consumers. Always use merge commits.
