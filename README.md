# Think

One install provides three harness-agnostic thinking skills: capture ideas, interrogate assumptions, and challenge claims with evidence.

## Why / what this is not

Think supports and accelerates human thought; it does not replace human judgment. It works from the conversation alone, and uses an available Atlas store when durable context or capture is useful.

## Modules

| Module | What you get |
| --- | --- |
| [`think-ramble`](.apm/skills/think-ramble/SKILL.md) | Capture free-form thoughts and, when a store is available, consolidate them. |
| [`think-grill`](.apm/skills/think-grill/SKILL.md) | Ask focused questions to clarify ideas and surface assumptions. |
| [`think-challenge`](.apm/skills/think-challenge/SKILL.md) | Search for credible counters and evidence to stress-test a claim. |

## Install

```bash
apm marketplace add sergio-sisternes-epam/atlas-marketplace --name atlas
apm install think@atlas
```

## Use

- `Ramble with me about a new product idea.`
- `Grill me on the assumptions behind this plan.`
- `Challenge this claim with evidence: ...`

## Prerequisites

An Atlas store is optional. Conversation-only use is supported; when a store is available, the skills use Atlas for durable context or capture.

## Related

- [Atlas marketplace](https://github.com/sergio-sisternes-epam/atlas-marketplace) — package catalog.
- [`atlas`](https://github.com/sergio-sisternes-epam/atlas) — optional durable knowledge store.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md). Maintainers are listed in [`AUTHORS`](AUTHORS). For bugs and questions, see [`SUPPORT.md`](SUPPORT.md). Report vulnerabilities through a [private GitHub security advisory](https://github.com/sergio-sisternes-epam/think/security/advisories/new), not a public issue.

## License

Copyright 2026 Sergio Sisternes. Licensed under Apache-2.0; see [`LICENSE`](LICENSE).
