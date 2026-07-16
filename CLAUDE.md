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

## Current status (as of 2026-07-16): scaffolded, pre-implementation

The repository scaffolding is complete and verified: the pixi environment
solves, and `pixi run lint` + `pixi run test` pass. **No component code exists
yet.** One decision blocks implementation.

### BLOCKING DECISION: choose the rendering engine (ROADMAP Milestone 0)

How UpSet plots get rendered must be decided before any component code is
written. The dash-seqviz playbook (wrap a mature MIT JavaScript library) does
NOT transfer here, because the mature JS UpSet library, **UpSet.js, is AGPLv3**
and cannot be wrapped in an MIT-licensed library. Two MIT-clean options remain
(full pros/cons are in ROADMAP.md and were discussed with the user):

- **Option B (recommended): Plotly-native, pure Python, Dash All-in-One
  component.** Compose `go.Bar` (set-size and intersection-size bars) with a
  `go.Scatter` dot matrix; ship a self-wiring `UpSet(...)` component plus a
  `create_upset(...) -> go.Figure` factory. Fast to ship, single language,
  reusable in notebooks, free publication-quality static export via kaleido.
  Interactivity is bounded by Plotly's model.
- **Option C: custom MIT React component** (dash-seqviz-style JS wrapper via the
  Dash component boilerplate). Best interactivity and pixel fidelity, but a
  large multi-week build, dual-language maintenance, and Dash-only (no notebook
  reuse, no free static export).

B and C are not a permanent fork: B-first is low-regret, and a React renderer
can later slot behind the same Python API if Plotly's interaction ceiling is
reached. **Do not start component implementation until the user confirms the
engine.** If the user has since decided, update this section and ROADMAP
Milestone 0 to record the choice.

## Next step (once the engine is chosen)

M1: build the data model (`from_memberships` / `from_contents` /
`from_indicators`, mirroring the BSD-licensed `upsetplot` conventions) and a
`create_upset(...) -> go.Figure` static figure. See the "Milestones" section of
ROADMAP.md.

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

- `dash_upset/` -- the package (currently only `__init__.py`; component modules
  arrive in M1, e.g. `data.py`, `figure.py`, `component.py`, `theming.py` per
  the ROADMAP architecture sketch for Option B).
- `tests/` -- pytest (smoke tests today; behavioral tests land with M1).
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
- No GitHub remote has been created or pushed yet; the local repo lives at
  `/Users/evan/fsa/dash-upset` on branch `main`.
