# dash-upset -- Roadmap

This is the working plan for `dash-upset`. It is meant to be reviewed and
revised together before implementation starts. It follows the same house style
as the `dash-seqviz` specs: **Problem, Users, Scope, Data model, Interaction,
Milestones, Non-goals, Open questions.**

The **rendering engine** decision
([Milestone 0](#milestone-0-decide-the-rendering-engine-decided-option-b)) was
made on 2026-07-16: **Option B, Plotly-native**. Everything downstream builds
on it.

---

## Problem

Set-intersection analysis is everywhere (genes across conditions, users across
features, tags across documents, cohorts across filters), but Dash has no
first-class way to show it. Venn and Euler diagrams collapse past three or four
sets. The community answer today is either a static matplotlib image
(`upsetplot`) dropped into an `html.Img`, or hand-rolled Plotly figures that
are hard to reuse and not interactive.

`dash-upset` should make an interactive UpSet plot a one-import, drop-in Dash
component: feed it set memberships, get a matrix + set-size bars +
intersection-size bars, with hover, selection, and callbacks that fit the
normal Dash programming model.

## Users

Mirrors the `dash-seqviz` academic + industrial split:

- **Bioinformatics / genomics** -- differentially expressed genes across
  conditions, variants across callers, peaks across samples. This is UpSet's
  origin community and its strongest pull.
- **Data science / ML** -- feature co-occurrence, label overlap, cohort
  membership, error-set analysis across models.
- **General analytics** -- users across features/plans, tags across content,
  survey multi-select questions.

Two usage modes to support:

1. **Analyst in a notebook / quick app** -- wants `UpSet(memberships=...)` to
   just render.
2. **App developer** -- wants to wire clicks and selections into callbacks and
   cross-filter the rest of a dashboard.

## Scope (in)

- A reusable Dash component rendering the three core UpSet elements: the
  intersection **matrix**, **set-size bars**, and **intersection-size bars**.
- **Sorting** of intersections (by size / cardinality, by degree, by set
  membership) and of sets (by size, by name).
- **Filtering**: minimum intersection size, maximum degree, top-N
  intersections, hide-empty.
- **Interactivity**: hover tooltips, click-to-select an intersection (or set),
  and callback outputs that report the current selection so a dashboard can
  cross-filter.
- **Theming**: honor Plotly templates and a light/dark story consistent with
  the `dash-seqviz` look; configurable colors.
- Familiar **data-input helpers** modeled on `upsetplot`
  (`from_memberships`, `from_contents`, `from_indicators`).

## Scope (out) for the first stable release

- Full UpSet 2 feature parity (element table view, per-attribute box/scatter
  plots, saved queries, bookmarking). These are tracked as later milestones.
- Venn / Euler / Karnaugh rendering (UpSet.js does these; not our v1 goal).
- Any server, database, or persistence layer. `dash-upset` is a client-side
  component library, like `dash-seqviz`.

---

## Milestone 0: decide the rendering engine (DECIDED: Option B)

`dash-seqviz` wraps the MIT-licensed `seqviz` npm package. That playbook does
**not** transfer directly, because the mature JS UpSet library is not
permissively licensed. We must pick a foundation before writing component code.

### The licensing finding

- **UpSet.js** (`@upsetjs/react`, `@upsetjs/bundle`) is **AGPLv3**; commercial
  use requires a separate commercial license from the author. Wrapping it in an
  MIT, publicly published, commercially backed library is not viable: AGPL is
  copyleft and would force AGPL (and its network-use source-disclosure
  obligation) onto every downstream Dash app.
- **`upsetplot`** (Joel Nothman) is **BSD-3-Clause** and safe to depend on or
  learn from, but it renders with matplotlib (static images, no native Dash
  interactivity).
- Building UpSet from Plotly primitives is well-trodden and MIT-clean
  (community `figure_factory` attempts; the `plotly-upset` and `UpSetPlotly`
  packages).

### The options

| | A. Wrap UpSet.js | B. Plotly-native (recommended) | C. Custom React component |
|---|---|---|---|
| **How** | Dash component boilerplate wrapping `@upsetjs/react`, like dash-seqviz wraps seqviz | Pure Python: compose `go.Bar` + `go.Scatter` matrix into a figure, packaged as a Dash All-in-One (AIO) component | Dash component boilerplate wrapping our own React/SVG UpSet renderer |
| **License** | ❌ AGPLv3 / commercial | ✅ MIT-clean | ✅ MIT-clean |
| **Interactivity** | Best-in-class, built in | Good: Plotly hover + `clickData`/`selectedData` + Dash callbacks; clientside highlight | Best-in-class, but we build it |
| **Effort** | Low code, but licensing blocks it | Low-to-moderate, pure Python | High: reimplement UpSet rendering + interactions |
| **Toolchain** | npm + webpack + babel (like dash-seqviz) | Python only (no JS build) | npm + webpack + babel |
| **Maintainability** | Tied to an AGPL upstream that last released in 2022 | Owned by us, Python team can maintain | Owned by us, needs JS expertise |
| **Matches "like dash-seqviz"** | Yes (structurally) | No (no JS wrapper), but same project shape: pip/conda-installable, release-please, docs site | Yes (structurally) |

### Recommendation: Option B (Plotly-native, packaged as an AIO component)

Rationale, weighted toward simplicity, robustness, and long-term
maintainability:

- It is **license-clean** and can ship MIT like dash-seqviz.
- UpSet plots decompose naturally into Plotly primitives (bars + a scatter dot
  matrix on shared axes), so we are not fighting the tool.
- **Interactivity comes for free from Dash**: `clickData` on the
  intersection bars tells us which intersection was clicked; a `selection`
  output prop lets the surrounding dashboard cross-filter. Hover tooltips and
  matrix highlighting are standard Plotly.
- **No JS build toolchain** to maintain -- a Python team owns the whole stack.
- The [Dash All-in-One component pattern](https://dash.plotly.com/all-in-one-components)
  lets us ship `from dash_upset import UpSet` as a real, self-wiring,
  callback-bundled component (the drop-in feel of dash-seqviz) without writing
  React.

Keep **Option C in our back pocket**: if we later hit Plotly's interaction
ceiling (e.g. rich element/attribute views like UpSet 2), we can add an MIT
React component behind the same Python API. The scaffolding already committed
(release-please, pixi, CI, docs) supports adding an npm/webpack layer later
without rework.

**Option A is ruled out** unless the project acquires a commercial UpSet.js
license and accepts an AGPL/commercial posture, which conflicts with shipping
MIT.

> **Decision (2026-07-16): Option B confirmed.** The rest of this roadmap
> assumes **B** and notes where **C** would differ; C stays in the back pocket
> as the documented fallback if Plotly's interaction ceiling is reached (M5).

---

## Data model

Adopt `upsetplot`'s proven, familiar input conventions so users are not
learning a new mental model. Internally, normalize all of them to a single
canonical representation.

Accepted inputs:

- **`from_memberships`** -- a list of set-name tuples per data point (plus
  optional per-point values to aggregate). Best when you have raw records.
- **`from_contents`** -- `{set_name: iterable_of_element_ids}`. Best when you
  have membership lists per set.
- **`from_indicators`** -- a boolean DataFrame (rows = elements, columns =
  sets, `True` = member). Best when data already lives in a table.
- A convenience **counts mapping** for pre-aggregated data:
  `{"Action&Drama": 120, ...}` (the shape shown in the README quick start).

Canonical internal form (what the renderer consumes):

```
sets:           ordered list of set names + their total sizes
intersections:  ordered list of { degree, member_sets, size, element_ids? }
```

Element ids are retained when provided so that a future element/attribute view
(and richer selection payloads) can be layered on without an API change.

## Interaction / UX

Planned component surface (Option B, AIO). Props are illustrative and part of
what we are agreeing here:

```python
UpSet(
    id="genes",
    # data (one of):
    memberships=..., contents=..., indicators=..., counts=...,
    # layout / sorting:
    orientation="horizontal",        # or "vertical"
    sort_by="cardinality",           # "cardinality" | "degree" | "-cardinality" ...
    sort_sets_by="cardinality",
    # filtering:
    min_subset_size=0, max_degree=None, max_subsets=None, show_empty=False,
    # style:
    theme="light", colors={...}, height=520,
    # interaction outputs (read-only, for callbacks):
    selected_intersection=None,      # set when a user clicks a bar/row
    selected_sets=None,
)
```

Interaction model:

- **Hover** -> tooltip with set names, degree, size, and % of total.
- **Click an intersection** (bar or matrix row) -> `selected_intersection`
  updates -> user callbacks fire and can cross-filter the rest of the app.
- **Click a set** -> `selected_sets` updates.
- **Highlight**: hovering/selecting an intersection dims the others (clientside
  for snappiness).

For **Option C**, the same Python props map to a React component and selection
flows back through `setProps`, exactly like `onSelection` in dash-seqviz.

## Architecture (Option B)

```
dash_upset/
  __init__.py          # exports: UpSet (AIO), create_upset (figure factory), from_* helpers
  data.py              # input parsing + canonical model (from_memberships/contents/indicators)
  figure.py            # create_upset(model, ...) -> go.Figure (matrix + bars via subplots)
  component.py         # UpSet AIO: dcc.Graph + wiring + pattern-matching callbacks
  theming.py           # Plotly template integration, colorways, light/dark
tests/                 # unit (data, figure structure) + Dash integration (selenium)
docs/                  # GitHub Pages site + live examples (added in M4)
usage.py               # local demo app for manual testing (like dash-seqviz)
```

If **Option C** is chosen, add the dash-seqviz-style JS layer
(`package.json`, `webpack.config.js`, `.babelrc`, `.eslintrc`, `src/lib/...`,
`dash-generate-components`) and an npm publish job; the Python API stays the
same.

## Milestones

- **M0 -- Decision. DONE (2026-07-16):** Option B, Plotly-native, packaged as
  an AIO component.
- **M1 -- Data model + static figure. DONE (2026-07-16):** `from_memberships` /
  `from_contents` / `from_indicators` / `from_counts`, the canonical model
  (`UpSetData`), and `create_upset(...) -> go.Figure` with matrix + both bar
  tracks, sorting, and hover tooltips. Ships as `0.1.0`. Deliverable met:
  renders a correct UpSet figure in a notebook (or any `dcc.Graph`).
- **M2 -- Interactive AIO component.** `UpSet(...)` with hover, click-select,
  and `selected_intersection` / `selected_sets` outputs; example callback
  cross-filtering a table. Ship as `0.2.0`.
- **M3 -- Filtering, theming, polish.** min-size / max-degree / top-N,
  light/dark + Plotly templates, vertical orientation, accessibility pass.
  `0.3.0`.
- **M4 -- Docs site + examples.** GitHub Pages (mirroring dash-seqviz's `docs/`
  approach) with live examples; conda-forge feedstock; first `1.0.0` when the
  API is stable.
- **M5 -- Advanced views (post-1.0).** Element/attribute views (box/scatter per
  attribute), saved queries, aggregation by degree/sets. This is where Option C
  may become worthwhile if Plotly's ceiling is reached.

## Testing strategy

Consistent with dash-seqviz's approach and the project's engineering-excellence
bar:

- **Unit** -- data parsing (`from_*` round-trips, empty/edge cases), figure
  structure (correct number of traces, bar values match intersection sizes).
- **Integration** -- Dash `dash.testing` + selenium (as in
  `dash-seqviz/tests/`): render `usage.py`, click a bar, assert the selection
  output updates.
- **Visual** -- optional kaleido image snapshots for the static figure to catch
  layout regressions.
- CI runs `pixi run lint` + `pixi run test` on every push/PR (already wired).

## Packaging and release (already scaffolded)

Committed in this initial scaffold:

- **pixi** environment + tasks (`test`, `lint`, `format`), conda-forge channel.
- **release-please** (`release-please-config.json`,
  `.release-please-manifest.json`, workflow) -- Conventional Commits drive
  version bumps and the changelog.
- **CI** (`.github/workflows/test.yml`) via `setup-pixi`.
- **Publish** (`.github/workflows/publish.yml`) to PyPI on GitHub Release, using
  trusted publishing (no stored token).
- **Packaging** via `pyproject.toml` (hatchling), MIT license, `dash_upset`
  package skeleton, smoke tests.

First-release checklist (when M1 is ready):

1. Land M1 features with `feat:` commits.
2. Merge the release-please PR -> tag + GitHub Release created.
3. Configure PyPI trusted publishing for `dash-upset` (one-time).
4. Enable GitHub Pages for `docs/` (M4).
5. Submit a conda-forge feedstock (M4), consistent with the conda-forge-first
   preference.

## Non-goals

- Not a general-purpose charting library; it does one thing (UpSet) well.
- Not a from-day-one clone of every UpSet 2 feature.
- No backend, auth, or persistence -- it is a client-side component.
- Not wrapping AGPL code.

## Open questions (to decide together)

1. ~~**Rendering engine: B or C?**~~ **Decided 2026-07-16: B** (Milestone 0).
2. ~~**Depend on `upsetplot` (BSD) for data helpers, or reimplement?**~~
   **Decided with M1: reimplement the conventions** (no `upsetplot`
   dependency); the `from_*` input shapes stay familiar to `upsetplot` users.
3. **Primary input shape for the docs/quick start** -- counts mapping (simplest
   to show) vs. `from_contents` (most common in practice)?
4. **Orientation default** -- horizontal (publication-style) or vertical
   (scroll-friendly, matches UpSet.js)?
5. ~~**npm publishing**~~ -- moot: only relevant to Option C, and B was chosen.
6. **Docs domain** -- dash-seqviz uses `dash-seqviz.com`. Do we want a
   `dash-upset.com` equivalent, or host under a shared docs domain?

## References

- UpSet technique and interactive reference: https://upset.app
- UpSet.js (AGPLv3): https://upset.js.org
- `upsetplot` (BSD, matplotlib): https://upsetplot.readthedocs.io
- Dash All-in-One components: https://dash.plotly.com/all-in-one-components
- Community Plotly UpSet discussion:
  https://community.plotly.com/t/plotly-upset-plot/63858
