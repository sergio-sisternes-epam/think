## Related issue

Fixes #

External contributors should open an issue first for substantive work.
Maintainers may skip that for small documentation or maintenance changes.

## Human scope approval

- [ ] This change is small docs/maintenance, or a maintainer approved the scope

## Agent-authored work

The pull request author owns any agent-generated diffs. Do not submit
unattended agent work that lists an agent as the GitHub author.

- [ ] I own these changes and can explain and maintain them

## Summary

<!-- What changed and why. -->

## Type of change

- [ ] Bug fix
- [ ] Feature / package change
- [ ] Breaking change
- [ ] Documentation
- [ ] Maintenance
- [ ] Marketplace pin

## Checklist

- [ ] No secrets, credentials, or private tokens in the diff
- [ ] Generated files were not hand-edited
- [ ] Lockfiles / packed artefacts match the source change, or N/A
- [ ] CHANGELOG.md updated, or N/A
- [ ] CONTRIBUTING.md checks considered

## Think validation

- [ ] `python3 -m unittest discover -s scripts -p 'test_*.py'` succeeds
- [ ] [Release metadata](https://github.com/sergio-sisternes-epam/think/blob/main/CONTRIBUTING.md#fast-local-checks) matches `apm.yml`
- [ ] [APM source audit](https://github.com/sergio-sisternes-epam/think/blob/main/CONTRIBUTING.md#fast-local-checks) succeeds
- [ ] If release-sensitive surfaces changed, [disposable consumer installs, frozen replay, and consumer audit](https://github.com/sergio-sisternes-epam/think/blob/main/CONTRIBUTING.md#full-package-validation) succeed
- [ ] CI checks pass
