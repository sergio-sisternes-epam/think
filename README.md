# think

One install gives nine agent harnesses three ways to think: capture ideas,
interrogate assumptions, and challenge claims with sources.

## Why / what this is not

Think is a harness-agnostic APM package of thinking primitives: capture,
Socratic questioning, and search-grounded counters. Conversation-only use
works when no durable store is present.

It is not a replacement for human thinking and judgement, but a tool to support and accelerate it.

## Install

```bash
apm marketplace add sergio-sisternes-epam/atlas-marketplace --name atlas
apm install think@atlas
```

`--name atlas` is required so the package resolves as `think@atlas`.

## Use

- `Ramble with me about a new product idea.`
- `Grill me on the assumptions behind this plan.`
- `Challenge this claim with evidence: ...`

## Modules

| Module | What it does |
| --- | --- |
| `think-ramble` | Dump free-form thoughts so they can be captured. |
| `think-grill` | Be questioned to refine ideas and surface assumptions. |
| `think-challenge` | Stress-test an idea with search-grounded counter-arguments. |

## Related

Think is listed on the [Atlas marketplace](https://github.com/sergio-sisternes-epam/atlas-marketplace).

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md). Maintainers are listed in
[AUTHORS](./AUTHORS). For bugs and questions, see [SUPPORT.md](./SUPPORT.md).

Do not file public issues for vulnerabilities. Report them with a
[private security advisory](https://github.com/sergio-sisternes-epam/think/security/advisories/new).

## License

Copyright 2026 Sergio Sisternes.

Licensed under Apache-2.0. See [LICENSE](./LICENSE).
