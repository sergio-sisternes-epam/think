# Contributing

Thank you for your interest in contributing to `think`.

## Prerequisites

| Tool | Minimum version | Install |
|------|----------------|---------|
| Git | 2.x | [git-scm.com](https://git-scm.com) |
| Python | 3.12 | Used by the repository-owned release checks |
| APM CLI | 0.29.0 (see `APM_VERSION` in CI) | CI verifies the pinned release archive checksum; pin the same version locally |

## Issues and pull requests

Use the GitHub issue and pull request templates in `.github/`.

Do not file public issues for vulnerabilities. Report them with a
[private security advisory](https://github.com/sergio-sisternes-epam/think/security/advisories/new).

Open an issue before substantive external work. Maintainers may skip that for
small documentation or maintenance changes. Human scope approval is required
before user-visible package, skill, or workflow changes.

If you used an agent, you own the diffs. Do not submit unattended agent work
that lists an agent as the GitHub author.

## Repository structure

```
├── apm.yml
├── .apm/skills/               # Author skills here
│   ├── think-challenge/SKILL.md
│   ├── think-grill/SKILL.md
│   └── think-ramble/SKILL.md
├── scripts/                   # Release and source-contract checks
├── .github/workflows/         # Source, consumer, and release gates
└── CONTRIBUTING.md
```

This is a single APM package, not a marketplace. Do not add a `marketplace:` block or `packages/` tree.
It has no dependencies and therefore no source `apm.lock.yaml`. Each consumer
installation creates its own lock with the resolved source identity and
deployed file hashes.

## Fast local checks

1. Create a feature branch from `main`.
2. Edit skills under `.apm/skills/<name>/SKILL.md`.
3. Run the fast repository checks before pushing:

   ```bash
   python3 -m unittest discover -s scripts -p 'test_*.py'
   python3 scripts/release_readiness.py --commit "$(git rev-parse HEAD)"
   python3 scripts/audit_source.py
   ```

4. Open a pull request against `main`.

## Full package validation

For release-sensitive changes to package metadata, installation, audit, or
workflow code, install the checkout into disposable consumers, replay the
generated lock with `--frozen`, and run `apm audit --ci --no-policy
--no-fail-fast`:

```bash
python3 scripts/validate_consumer.py --target agent-skills
python3 scripts/validate_consumer.py \
  --target claude,codex,copilot,cursor,gemini,grok-build,kiro,opencode,windsurf
```

CI always exercises both target sets with the same repository-owned validator,
so ordinary skill-prose edits do not need to repeat the full matrix locally.
`--no-policy` keeps this check package-local; organisation policy enforcement
is a separate repository or enterprise control.

`apm compile` is not a validation gate for Think because this package contains
skills rather than `.apm/instructions/`. `apm pack` is also not a release gate:
it builds dependency bundles, while Think is installed directly from an
immutable Git source tag.

## Release handoff

Think follows semantic versioning. While the package remains below `1.0.0`, use
a patch increment for compatible fixes and a minor increment for new capability
or a compatibility-breaking skill contract.

1. Update `apm.yml`, both README install commands, the bug-report version
   example, and `CHANGELOG.md`.
2. Merge the reviewed change through the protected `main` branch.
3. Run **Think CI** manually against the exact `main` commit intended for
   release. Its final job must report
   `release_readiness_decision=ready-to-tag`.
4. After separate approval, create and push the matching annotated `vX.Y.Z` tag
   against that exact commit.

   ```bash
   candidate_revision=<approved-40-character-SHA>
   version=<X.Y.Z>
   git fetch --no-tags origin \
     +refs/heads/main:refs/remotes/origin/main
   test "$(git rev-parse refs/remotes/origin/main)" = "$candidate_revision"
   git tag -a "v$version" "$candidate_revision" -m "Think v$version"
   git push origin "refs/tags/v$version"
   ```

   When using another configured remote, replace `origin` consistently in both
   the fetch source and `refs/remotes/<remote>/main` destination/readback.

5. The tag workflow verifies the authoritative remote tag object in an isolated
   namespace, requires it to peel to exact current `main`, reruns every gate,
   re-verifies the object immediately before publication, and creates the
   GitHub Release with curated CHANGELOG content followed by generated notes.

Never move, overwrite, delete, or reuse a pushed release tag. If validation
finds a candidate defect, fix `main`, increment the version, repeat readiness,
and use a new tag. If validation or Release creation fails only because of a
transient provider, network, or permission problem, rerun the failed workflow
for the unchanged tag.

The workflow uses only the repository `GITHUB_TOKEN`: read-only during
validation and `contents: write` only in the Release creation job. That
repository-scoped token can read private Think content during same-repository
tag validation. No custom secret is required because Think has no
cross-repository private package dependency.
Reusable CI remains read-only and cannot elevate permissions beyond its
caller's token context.
GitHub grants permissions per job, so the final read-only tag reverification
shares the Release job's `contents: write` token. Keeping reverification and
creation adjacent avoids reopening the validation-to-publication race.

## Repository protection

Protect `main` with the **Release metadata**, **APM source integrity**, both
**Consumer install** checks, and **Release readiness decision**. Require
branches to be current, and block direct pushes, force pushes, and deletion.
Protect `v*` tags so only release maintainers can create them and no actor can
update or delete them. The designated release-maintainer or administrator
bypass exists only to permit approved tag creation; because provider bypasses
can also bypass mutation rules, never use that bypass to update or delete an
existing release tag.

## Commit conventions

Use [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <short summary>
```

Examples:
- `feat(think-grill): tighten question limits`
- `docs: clarify conversation-only install`
