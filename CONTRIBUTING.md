# Contributing

## Environment

This project uses [pixi](https://pixi.sh). Dependencies come from conda-forge.

```bash
pixi install          # create/update the environment
pixi run test         # pytest
pixi run lint         # ruff check
pixi run format       # ruff format
```

The package installs editable into the environment, so `import dash_upset`
resolves to your working tree.

## Commit messages: Conventional Commits

Releases are automated with
[release-please](https://github.com/googleapis/release-please), which reads the
git history. Commit messages **must** follow
[Conventional Commits](https://www.conventionalcommits.org):

| Type | Effect on version (pre-1.0) | Example |
|---|---|---|
| `feat:` | minor bump | `feat: add intersection-size bar sorting` |
| `fix:` | patch bump | `fix: correct empty-set handling` |
| `docs:`, `chore:`, `test:`, `refactor:`, `ci:` | no release | `docs: expand quick start` |
| `feat!:` / `BREAKING CHANGE:` | minor bump while pre-1.0 | `feat!: rename memberships prop` |

Scopes are encouraged, e.g. `feat(matrix): ...`, `fix(callbacks): ...`.

## Release flow

1. Merge Conventional-Commit PRs into `main`.
2. `release-please` opens/updates a "release PR" that bumps the version and the
   changelog.
3. Merging that PR tags the release and publishes a GitHub Release, which
   triggers publishing to PyPI.

Do not hand-edit `CHANGELOG.md` or the version in `pyproject.toml` /
`dash_upset/__init__.py`; release-please owns them.
