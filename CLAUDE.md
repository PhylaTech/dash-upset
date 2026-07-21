# CLAUDE.md -- dash-upset

Orientation for Claude Code sessions opened in this folder. Read this first.
The living plan is [ROADMAP.md](./ROADMAP.md); this file tells you what the
project is, where we left off, and how to work here.
[SURVEY.md](./SURVEY.md) is the competitive survey of the UpSet ecosystem that
informs the roadmap's feature set and API vocabulary; consult it before
designing a new feature.

## What this is

`dash-upset` is a library for interactive **UpSet plots** (https://upset.app)
in Plotly Dash. It is a new **PhylaTech** project
(https://github.com/PhylaTech), a sibling of `dash-seqviz` (`../dash-seqviz`),
which is the template for the overall project shape. PhylaTech is the
organization that the Full Spectrum Analytics (FSA) tools, including
dash-seqviz, are being migrated to.

## Current status (as of 2026-07-20): M1+M2+M4 shipped, M3 mostly done

**Engine: Option B, Plotly-native** (the figure is pure Python, `go.Bar` +
`go.Scatter` composed via subplots), **plus a minimal compiled React shim for
the component layer** (2026-07-20 ROADMAP addendum): react-plotly.js renders
the Python-built figure and maps clicks onto two declared props, so callbacks
use the standard `Input("genes", "selected_intersection")` convention instead
of the earlier AIO `UpSet.ids.*` pattern-matching ids. Wrapping UpSet 2.0
(`@visdesignlab/upset2-react`, BSD-3) stays the documented M5 fallback;
UpSet.js stays off the table (AGPLv3).

**Implemented and tested:**

- `dash_upset/data.py` -- the canonical `UpSetData` model plus
  `from_memberships` / `from_contents` / `from_indicators` (upsetplot-style
  conventions, reimplemented, no upsetplot dependency) and a `from_counts`
  convenience for pre-aggregated data. `from_indicators` is
  dataframe-agnostic via **narwhals** (`narwhals.stable.v2`); Python floor is
  3.10. pandas + polars are dev-only test deps.
- `dash_upset/figure.py` -- `create_upset(...) -> go.Figure`: bars + dot
  matrix, `mode=` (distinct/intersect/union), sorting incl. deviation,
  filtering (size/degree/top-N), `show_counts`/`show_percentages`,
  `theme=` (light/dark/auto + okabe-ito/colorbrewer/tol CVD palettes).
  Traces carry stable `meta` ids; the component's click mapping keys on them.
- `dash_upset/component.py` -- `UpSet`, subclassing the compiled `DashUpset`;
  builds the figure from `data`/`sets` + `create_upset` kwargs and exposes
  `selected_intersection` / `selected_sets` as real component properties.
- `dash_upset_component/` -- the compiled inner package (webpack bundle with
  trimmed plotly.js core+bar+scatter, generated `DashUpset.py`). **Build
  artifacts are committed**; regenerate with `npm install && pixi run
  build-component` only when `src/lib/` changes. Its `__version__` is bumped
  by release-please's extra-files updater (x-release-please-version marker).
- Docs site (M4) at https://phylatech.github.io/dash-upset/ (gh-pages branch,
  PR previews via pr-preview-action; naturalist-press design).
- Tests: `tests/test_data.py`, `tests/test_figure.py`, `tests/test_component.py`;
  `pixi run lint` + `pixi run test` pass.

## Next steps

Remaining roadmap items: M3 leftovers (vertical orientation, auto text
descriptions/accessibility), the deviation/attribute multi-panel grid, a
drill-into-members element table + cross-filter example (original M2 scope),
and an explorer theme toggle in the docs. Release PR #1 (v0.1.0) stays open
until the user decides to publish.

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

- `dash_upset/` -- the package: `data.py` (model + `from_*` constructors),
  `figure.py` (`create_upset`, incl. the `theme=` system), `component.py`
  (`UpSet`).
- `dash_upset_component/` -- compiled inner package behind `UpSet` (committed
  webpack bundle + `dash-generate-components` output). Source lives in
  `src/lib/`; npm toolchain: `package.json`, `webpack.config.js`, `.babelrc`.
  `DashUpset.py` and `_imports_.py` are generated (ruff-excluded); the
  package `__init__.py` is hand-written.
- `tests/` -- pytest (`test_data.py`, `test_figure.py`, `test_component.py`,
  import smoke tests).
- `pyproject.toml` -- packaging (hatchling; both packages ship in the wheel)
  plus pixi, ruff, and pytest config.
- `docs/` -- the GitHub Pages site (published from the `gh-pages` branch by
  `.github/workflows/docs.yml`; PR previews via `docs-preview.yml`).
- Release automation: `release-please-config.json`,
  `.release-please-manifest.json`, and `.github/workflows/`
  (`test.yml`, `publish.yml`, `release-please.yml`).

## Related

- Sibling and template project: `../dash-seqviz` (a Dash component wrapping the
  MIT `seqviz` npm library; it uses mamba and `setup.py`, whereas dash-upset
  uses pixi and `pyproject.toml`).
- Prior art: `upsetplot` (BSD, matplotlib) for the data-input conventions;
  UpSet 2.0 (`visdesignlab/upset2`, BSD-3) as the license-clean React engine
  candidate if Option C is ever triggered (ROADMAP M0 addendum); and UpSet.js
  (AGPL) as the implementation we are explicitly NOT wrapping.
- GitHub remote: `https://github.com/PhylaTech/dash-upset` (created private;
  flip visibility when ready to publish). The local repo lives at
  `/Users/evan/fsa/dash-upset` on branch `main`.
