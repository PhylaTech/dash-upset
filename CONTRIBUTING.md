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

The documentation site is a static site in `docs/`, served in production by
**GitHub Pages** from `main` at https://phylatech.github.io/dash-upset/. The
example datasets and demo figures are generated from Python (the source of
truth) and committed; regenerate them after changing the figure factory:

```bash
pixi run python scripts/build_docs_data.py   # docs/data/examples.js
pixi run python scripts/build_docs_demo.py   # docs/assets/demo.js
```

### Per-PR previews on Cloudflare Pages

`.github/workflows/docs-preview.yml` deploys each PR's `docs/` to a
[Cloudflare Pages](https://developers.cloudflare.com/pages/) preview and posts
the URL as a comment, so reviewers can see the rendered docs before merging.
Production stays on GitHub Pages; Cloudflare only serves previews.

The workflow **skips cleanly until the Cloudflare secrets are set**, so it never
fails a PR before configuration. To enable it (one-time, needs a Cloudflare
account):

1. **Create the Pages project** (direct-upload type), named `dash-upset-docs`:

   ```bash
   npx wrangler pages project create dash-upset-docs --production-branch main
   ```

   or in the dashboard: **Workers & Pages → Create → Pages → Upload assets**.

2. **Create an API token** at
   <https://dash.cloudflare.com/profile/api-tokens> with the
   **Account → Cloudflare Pages → Edit** permission (scoped to the account that
   owns the project). Copy the account ID from **Workers & Pages** in the
   dashboard.

3. **Add both as repository secrets** (Settings → Secrets and variables →
   Actions), or with the GitHub CLI:

   ```bash
   gh secret set CLOUDFLARE_API_TOKEN --repo PhylaTech/dash-upset
   gh secret set CLOUDFLARE_ACCOUNT_ID --repo PhylaTech/dash-upset
   ```

Once the secrets exist, the next PR push deploys a preview at
`https://pr-<number>.dash-upset-docs.pages.dev` and comments the link.

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
