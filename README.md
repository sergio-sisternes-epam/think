# think

> One install gives nine agent harnesses three ways to think: capture ideas,
> interrogate assumptions, and challenge claims with sources.

Install this repo as a single package. Skills live under `.apm/skills/`. There is no marketplace index and no Atlas store.

## Skills

| Skill | When to use |
|-------|-------------|
| `think-ramble` | Dump free-form thoughts so they can be captured. |
| `think-grill` | Be questioned to refine ideas and surface assumptions. |
| `think-challenge` | Stress-test an idea with search-grounded counter-arguments. |

Conversation-only use works when no durable store is present. If Atlas (or another store) is available, skills may optionally query or remember through it.

## Install

Install [APM](https://github.com/microsoft/apm) 0.29.0 or later, then install
Think.

The repository is private. Remote consumers need an
[APM-supported Git credential](https://microsoft.github.io/apm/getting-started/authentication/)
authorised to read its contents; request repository access from the
[owner](https://github.com/sergio-sisternes-epam) and verify the active account
with `gh auth status` before installing.

The immutable `v0.1.0` install becomes available when the separately approved
annotated tag is published. Its GitHub Release then records the curated and
generated release notes.

```bash
apm install sergio-sisternes-epam/think#v0.1.0 --target agent-skills
```

This shared target covers Agent Skills, Codex, Copilot, Cursor, Gemini,
OpenCode, and Windsurf. Claude, Grok Build, and Kiro use native roots; use the
full target command in [Compatibility](#compatibility) when installing for
those runtimes.

Or from a local clone:

```bash
apm install /path/to/think --target agent-skills
```

Try one of these prompts after installation:

- `Ramble with me about a new product idea.`
- `Grill me on the assumptions behind this plan.`
- `Challenge this claim with evidence: ...`

## Compatibility

Think is validated with APM CLI 0.29.0 against the shared `agent-skills` target
and the stable Claude, Codex, Copilot, Cursor, Gemini, Grok Build, Kiro,
OpenCode, and Windsurf targets. A consumer install creates and owns its
`apm.lock.yaml`; this dependency-free source package does not commit one.

To exercise every stable runtime explicitly:

```bash
apm install sergio-sisternes-epam/think#v0.1.0 --target claude,codex,copilot,cursor,gemini,grok-build,kiro,opencode,windsurf
```

APM 0.29 deploys Codex, Copilot, Cursor, Gemini, OpenCode, Windsurf, and the
generic `agent-skills` target through `.agents/skills/<skill>/SKILL.md`.
Claude, Grok Build, and Kiro use their native `.claude/skills/`,
`.grok/skills/`, and `.kiro/skills/` roots respectively.

## Layout

```
apm.yml
.apm/skills/
  think-ramble/SKILL.md
  think-grill/SKILL.md
  think-challenge/SKILL.md
```

The package is distributed directly from immutable Git tags. `apm pack` builds
dependency bundles and is not a release artefact for this dependency-free
source-package layout.

## Releases

Curated release notes are maintained in [CHANGELOG.md](./CHANGELOG.md). GitHub
Release bodies start with that curated version section and append GitHub's
generated pull-request notes. A release tag must be a newly created annotated
`vX.Y.Z` tag on the exact current `main` commit. The tag workflow reruns source
and consumer validation, then re-verifies the remote tag object immediately
before creating the GitHub Release. Tags are never moved or reused.

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## Support

See [SUPPORT.md](./SUPPORT.md).

## Security

To report a vulnerability, see [SECURITY.md](./SECURITY.md).

## Licence

Copyright 2026 Sergio Sisternes.

Licensed under Apache-2.0. See [LICENSE](./LICENSE).
