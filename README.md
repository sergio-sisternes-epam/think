# think

> Harness-agnostic thinking primitives as one APM package: ramble, grill, and challenge.

[![CI](https://github.com/sergio-sisternes-epam/think/actions/workflows/ci.yml/badge.svg)](https://github.com/sergio-sisternes-epam/think/actions/workflows/ci.yml)
[![PR Validate](https://github.com/sergio-sisternes-epam/think/actions/workflows/pr-validate.yml/badge.svg)](https://github.com/sergio-sisternes-epam/think/actions/workflows/pr-validate.yml)

Install this repo as a single package. Skills live under `.apm/skills/`. There is no marketplace index and no Atlas store.

## Skills

| Skill | When to use |
|-------|-------------|
| `think-ramble` | Dump free-form thoughts so they can be captured. |
| `think-grill` | Be questioned to refine ideas and surface assumptions. |
| `think-challenge` | Stress-test an idea with search-grounded counter-arguments. |

Conversation-only use works when no durable store is present. If Atlas (or another store) is available, skills may optionally query or remember through it.

## Install

```bash
apm install sergio-sisternes-epam/think#v1.0.0
```

Or from a local clone:

```bash
apm install /path/to/think
```

## Layout

```
apm.yml
.apm/skills/
  think-ramble/SKILL.md
  think-grill/SKILL.md
  think-challenge/SKILL.md
```

## Contributing

See [CONTRIBUTING.md](./CONTRIBUTING.md).

## Support

See [SUPPORT.md](./SUPPORT.md).

## Security

To report a vulnerability, see [SECURITY.md](./SECURITY.md).

## Licence

Apache-2.0 as declared in `apm.yml`.
