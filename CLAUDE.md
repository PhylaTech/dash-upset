# CLAUDE.md -- dash-upset

Orientation for Claude Code sessions opened in this folder. Read this first.
The living plan is [ROADMAP.md](./ROADMAP.md); this file tells you what the
project is, where we left off, and how to work here.

## What this is

`dash-upset` is a library for interactive **UpSet plots** (https://upset.app)
in Plotly Dash. It is a new **PhylaTech** project
(https://github.com/PhylaTech), a sibling of `dash-seqviz` (`../dash-seqviz`),
which is the template for the overall project shape. PhylaTech is the
organization that the Full Spectrum Analytics (FSA) tools, including
dash-seqviz, are being migrated to.

## Current status (as of 2026-07-16): M1 implemented, engine decided

**ROADMAP Milestone 0 is decided: Option B, Plotly-native** (pure Python,
`go.Bar` + `go.Scatter` composed via subplots, to be packaged as a Dash
All-in-One component in M2). The decision record and the full option analysis
live in ROADMAP.md. Option C (custom MIT React component) remains the
documented fallback if Plotly's interaction ceiling is ever reached; UpSet.js
stays off the table (AGPLv3).

**M1 (data model + static figure) is implemented and tested:**

- `dash_upset/data.py` -- the canonical `UpSetData` model plus
  `from_memberships` / `from_contents` / `from_indicators` (upsetplot-style
  conventions, reimplemented, no upsetplot dependency) and a `from_counts`
  convenience for pre-aggregated data.
- `dash_upset/figure.py` -- `create_upset(...) -> go.Figure`: intersection-size
  bars, set-size bars, dot matrix with connectors, sorting
  (`sort_by`/`sort_sets_by`), `show_empty`/`show_counts`, hover tooltips with
  percentages. Traces carry stable `meta` ids so the M2 component can address
  them.
- Behavioral tests in `tests/test_data.py` and `tests/test_figure.py`;
  `pixi run lint` + `pixi run test` pass.

## Next step: M2 (interactive AIO component)

Build the self-wiring `UpSet(...)` Dash All-in-One component: `dcc.Graph` +
pattern-matching callbacks, click-to-select via the bar traces' `meta` /
`customdata`, and `selected_intersection` / `selected_sets` outputs. See the
"Milestones" section of ROADMAP.md and its Interaction/UX prop sketch.

## Working conventions

- **Environment: pixi** (not mamba, which is what dash-seqviz uses).
  Dependencies come from **conda-forge**, the preferred channel. Tasks:
  - `pixi install` -- create or update the environment (installs the package
    editable, so `import dash_upset` resolves to the working tree)
  - `pixi run test` -- pytest
  - `pixi run lint` -- ruff check
  - `pixi run format` -- ruff format
- **Commits: Conventional Commits**, because release-please drives versioning
  and the changelog. `feat:` bumps the minor (pre-1.0), `fix:` bumps the patch,
  and `chore:` / `docs:` / `test:` / `ci:` produce no release. Do NOT hand-edit
  `CHANGELOG.md` or version numbers.
- **Version** is single-sourced in `dash_upset/__init__.py` (`__version__`);
  hatchling reads it, `pyproject.toml` declares it dynamic, and release-please
  bumps it on release.
- The user's global rules still apply (see `~/.claude/CLAUDE.md`): no em dashes
  anywhere, and no AI-attribution or co-authorship trailers in commits, PRs, or
  issues.

## Layout

- `dash_upset/` -- the package: `data.py` (model + `from_*` constructors) and
  `figure.py` (`create_upset`); `component.py` and `theming.py` arrive with
  M2/M3 per the ROADMAP architecture sketch.
- `tests/` -- pytest (`test_data.py`, `test_figure.py`, import smoke tests).
- `pyproject.toml` -- packaging (hatchling) plus pixi, ruff, and pytest config.
- Release automation: `release-please-config.json`,
  `.release-please-manifest.json`, and `.github/workflows/`
  (`test.yml`, `publish.yml`, `release-please.yml`).
- **Deliberately not present yet:** a `docs/` GitHub Pages site (Milestone M4),
  a `usage.py` demo app, and any npm/webpack toolchain (added only if Option C
  is chosen).

## Related

- Sibling and template project: `../dash-seqviz` (a Dash component wrapping the
  MIT `seqviz` npm library; it uses mamba and `setup.py`, whereas dash-upset
  uses pixi and `pyproject.toml`).
- Prior art: `upsetplot` (BSD, matplotlib) for the data-input conventions, and
  UpSet.js (AGPL) as the interactive reference implementation we are explicitly
  NOT wrapping.
- GitHub remote: `https://github.com/PhylaTech/dash-upset` (created private;
  flip visibility when ready to publish). The local repo lives at
  `/Users/evan/fsa/dash-upset` on branch `main`.
