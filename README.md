# think

One install gives nine agent harnesses three ways to think: capture ideas,
interrogate assumptions, and challenge claims with sources.

## Why / what this is not

Think is a harness-agnostic APM package of thinking primitives: capture,
Socratic questioning, and search-grounded counters. Conversation-only use
works when no durable store is present.

It is not a marketplace, not an Atlas store, and not a harness-specific
instruction pack. Extra depth lives in each skill's `SKILL.md`,
[CONTRIBUTING.md](./CONTRIBUTING.md), and [SUPPORT.md](./SUPPORT.md).

## Install

```bash
apm marketplace add sergio-sisternes-epam/atlas-marketplace --name atlas
apm install think@atlas
```

Install [APM](https://github.com/microsoft/apm) 0.29.0 or later first. Think is validated with APM CLI 0.29.0 against the shared `agent-skills` target and the stable Claude, Codex, Copilot, Cursor, Gemini, Grok Build, Kiro, OpenCode, and Windsurf targets.

Optional: install the immutable `v0.1.0` tag. The shared target covers Agent
Skills, Codex, Copilot, Cursor, Gemini, OpenCode, and Windsurf:

```bash
apm install sergio-sisternes-epam/think#v0.1.0 --target agent-skills
```

Claude, Grok Build, and Kiro use native roots; use the full target set for
those runtimes:

```bash
apm install sergio-sisternes-epam/think#v0.1.0 --target claude,codex,copilot,cursor,gemini,grok-build,kiro,opencode,windsurf
```

Or from a local clone:

```bash
apm install /path/to/think --target agent-skills
```

## Use

- `Ramble with me about a new product idea.`
- `Grill me on the assumptions behind this plan.`
- `Challenge this claim with evidence: ...`

## Modules

| Module | What it does |
|--------|----------------|
| `think-ramble` | Dump free-form thoughts so they can be captured. |
| `think-grill` | Be questioned to refine ideas and surface assumptions. |
| `think-challenge` | Stress-test an idea with search-grounded counter-arguments. |

## Related

Think is listed on the [Atlas marketplace](https://github.com/sergio-sisternes-epam/atlas-marketplace).
This package has no Atlas store. If [atlas](https://github.com/sergio-sisternes-epam/atlas)
is available, skills may optionally query or remember through it.

Other marketplace packages include [okf](https://github.com/sergio-sisternes-epam/okf),
[discuss](https://github.com/sergio-sisternes-epam/discuss),
[atlas-cartograph](https://github.com/sergio-sisternes-epam/atlas-cartograph),
and [autogenesis](https://github.com/sergio-sisternes-epam/autogenesis).

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). Maintainers are listed in
[AUTHORS](./AUTHORS). For bugs and questions, see [SUPPORT.md](./SUPPORT.md).

Do not file public issues for vulnerabilities. Report them with a
[private security advisory](https://github.com/sergio-sisternes-epam/think/security/advisories/new).

## License

Copyright 2026 Sergio Sisternes.

Licensed under Apache-2.0. See [LICENSE](./LICENSE).
