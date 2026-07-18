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

## Docs site and previews

The documentation site is a static site in `docs/`, published by **GitHub
Pages** from the `gh-pages` branch at https://phylatech.github.io/dash-upset/.
Production deploys automatically: `.github/workflows/docs.yml` copies `docs/` to
the root of `gh-pages` on every push to `main`. The example datasets and demo
figures are generated from Python (the source of truth) and committed;
regenerate them after changing the figure factory:

```bash
pixi run python scripts/build_docs_data.py   # docs/data/examples.js
pixi run python scripts/build_docs_demo.py   # docs/assets/demo.js
```

### Per-PR previews (GitHub Pages)

`.github/workflows/docs-preview.yml` deploys each PR's `docs/` to the
`gh-pages` branch under `pr-preview/pr-<number>/` using
[pr-preview-action](https://github.com/rossjrw/pr-preview-action) and comments
the URL on the PR, so reviewers see the rendered docs before merging. The
preview is removed when the PR closes. **No external accounts or secrets** are
required; it reuses GitHub Pages, and production redeploys preserve the
`pr-preview/` directory (`clean-exclude`). Previews are live at:

```
https://phylatech.github.io/dash-upset/pr-preview/pr-<number>/
```

Previews only run for branches in this repository (fork PRs get a read-only
token that cannot push to `gh-pages`).

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
