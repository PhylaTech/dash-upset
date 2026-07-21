# dash-upset -- Roadmap

This is the working plan for `dash-upset`. It is meant to be reviewed and
revised together before implementation starts. It follows the same house style
as the `dash-seqviz` specs: **Problem, Users, Scope, Data model, Interaction,
Milestones, Non-goals, Open questions.**

The **rendering engine** decision
([Milestone 0](#milestone-0-decide-the-rendering-engine-decided-option-b)) was
made on 2026-07-16: **Option B, Plotly-native**. Everything downstream builds
on it.

The feature set and interaction model below are informed by
[SURVEY.md](./SURVEY.md), a competitive survey of the existing UpSet ecosystem
(JavaScript/web, Python, R) and the technique's conceptual model. Read it for
the reasoning behind the scope choices, the feature-comparison matrix, and the
prioritized recommendations folded into the milestones here.

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
- **Intersection modes** (`distinct` / `intersect` / `union`), defaulting to
  `distinct` (the canonical exclusive intersection). The survey found this is
  the feature most quick ports omit and the concept users most often misread; it
  is compute-only and renders identically, so it is high-value and low-cost.
- **Sorting** of intersections (by size / cardinality, by degree, by
  **deviation**) and of sets (by size, by name), with deterministic
  leftmost-set tie-breaking.
- **Deviation** column: the signed "how surprising is this intersection given
  the set sizes" measure from the original paper (a low-cost analytic that
  differentiates us from UpSetR).
- **Filtering**: minimum/maximum intersection size, minimum/maximum degree,
  top-N intersections, hide-empty.
- **Interactivity**: hover tooltips, click-to-select an intersection (or set),
  and callback outputs that report the current selection so a dashboard can
  cross-filter. Component API shape follows UpSet.js's stateless
  controlled-component contract (selection as a prop, hover/click as events).
- **Per-intersection attribute subplots**: a curated vocabulary (box, violin,
  strip, scatter, histogram, stacked-bar) sharing the intersection axis, in the
  spirit of `upsetplot`'s `add_catplot` and ComplexUpset annotations. Requires
  the data model to carry per-element attributes.
- **Auto-generated text descriptions** (short alt-text + a structured long
  description), following the 2025 EuroVis accessibility work. Nearly free in
  Python and offered by no other Python library.
- **Theming**: honor Plotly templates and a light/dark story consistent with
  the `dash-seqviz` look; configurable colors.
- Familiar **data-input helpers** modeled on `upsetplot`
  (`from_memberships`, `from_contents`, `from_indicators`), plus a counts-only
  `from_counts` (our addition; prior art is UpSetR's `fromExpression`).

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
- **UpSet 2.0** (`visdesignlab/upset2`, the technique authors' own web
  reimplementation) is **BSD-3-Clause**, so unlike UpSet.js it *could* be
  wrapped. See the addendum below for what that does and does not change.
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

### Addendum (2026-07-16): UpSet 2.0 is BSD-3 and upgrades Option C

**UpSet 2.0** ([visdesignlab/upset2](https://github.com/visdesignlab/upset2)),
by the lab behind the original UpSet technique, is **BSD-3-Clause** and
publishes an embeddable renderer, `@visdesignlab/upset2-react`, plus
`@visdesignlab/upset2-core` for the data layer (data input: an array of
objects with boolean set-membership fields and optional attribute columns).
Unlike UpSet.js, it could legally be wrapped in this MIT library, so the "no
permissive mature JS implementation" premise above no longer holds in full.

This does not change the Option B decision, because the other B-vs-C factors
are unchanged. Wrapping upset2-react would still mean the npm/webpack
toolchain and dual-language maintenance that B avoids, Dash-only rendering (no
notebook figures, no kaleido static export), and a heavy embed: upset2-react
peer-depends on React 18/19, MUI (`material`, `icons-material`, `system`,
`x-data-grid`), Emotion, Recoil, Trrack (`core` + `vis-react`), and
Vega/Vega-Lite (`vega`, `vega-lite`, `vega-embed`, `react-vega`), which every
consuming Dash app would carry.

What it does change is the cost and shape of **Option C**: "build a React
UpSet renderer from scratch" becomes "wrap `upset2-react`", which would also
bring UpSet 2.0's advanced features (element and attribute views,
provenance/undo via Trrack, generated alt text for accessibility) within
reach. **If Plotly's interaction ceiling is hit (M5), evaluate wrapping
`upset2-react` before building anything custom.** Its alt-text work is also
worth borrowing ideas from for the M3 accessibility pass, independent of the
engine question.

### Addendum (2026-07-20): the component layer is a compiled React shim

The `UpSet` component originally shipped as a pure-Python All-in-One (AIO)
composite (`dcc.Graph` + `dcc.Store`s + a pattern-matching callback), whose
selection outputs had to be addressed as
`Input(UpSet.ids.selected_intersection("genes"), "data")`. That syntax is the
official pattern for composite components, but it is not the convention Dash
users expect from a real component (`Input("genes", "<property>")`), and a
pure-Python composite cannot declare new top-level properties.

**Decision: keep the figure Plotly-native (Option B unchanged), but back the
`UpSet` component with a minimal compiled React component** (`src/lib/`,
built into `dash_upset_component/`). The shim is ~150 lines: react-plotly.js
renders the Python-built figure (a trimmed plotly.js bundle: core + bar +
scatter), and a click handler maps the stable trace `meta` ids to two declared
properties, `selected_intersection` and `selected_sets`. All UpSet logic
(data model, modes, sorting, filtering, deviation, theming) stays in Python,
shared with `create_upset`.

Consequences:

- Callbacks use the standard convention:
  `Input("genes", "selected_intersection")`.
- The npm/webpack/`dash-generate-components` toolchain now exists in the repo,
  but **built artifacts are committed**, so installing, testing, packaging,
  and publishing need no Node; Node is needed only to change `src/lib/`.
- This is *not* the full Option C (no custom renderer was built; rendering is
  plotly.js exactly as before). Wrapping `upset2-react` remains the documented
  M5 fallback if Plotly's interaction ceiling is hit.

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
- **`from_indicators`** -- a boolean indicator table (rows = elements, columns
  = sets, `True` = member) from any narwhals-supported dataframe library
  (pandas, Polars, PyArrow, cuDF, Modin, ...) or a plain mapping of columns.
  Best when data already lives in a table. Dataframe access goes through
  **narwhals**, so `dash-upset` depends on no dataframe library itself.
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

## Architecture (Option B + compiled component shim)

```
dash_upset/
  __init__.py          # exports: UpSet (component), create_upset (figure factory), from_* helpers
  data.py              # input parsing + canonical model (from_memberships/contents/indicators)
  figure.py            # create_upset(model, ...) -> go.Figure (matrix + bars via subplots)
  component.py         # UpSet: builds the figure, subclasses the compiled DashUpset
dash_upset_component/  # compiled React shim (committed build artifacts + generated class)
src/lib/               # the shim's source: DashUpset.react.js (react-plotly.js + click mapping)
package.json           # npm build: webpack bundle + dash-generate-components
tests/                 # unit (data, figure structure, component props)
docs/                  # GitHub Pages site + live examples
```

Theming lives in `figure.py` (`theme=` resolves palettes + light/dark); a
separate `theming.py` was not needed. If the full **Option C** (custom
renderer / upset2-react wrap) is ever chosen, it extends `src/lib/` and the
Python API stays the same.

## Milestones

- **M0 -- Decision. DONE (2026-07-16):** Option B, Plotly-native, packaged as
  an AIO component.
- **M1 -- Data model + static figure. DONE (2026-07-16):** `from_memberships` /
  `from_contents` / `from_indicators` / `from_counts`, the canonical model
  (`UpSetData`), and `create_upset(...) -> go.Figure` with matrix + both bar
  tracks, sorting, and hover tooltips. Ships as `0.1.0`. Deliverable met:
  renders a correct UpSet figure in a notebook (or any `dcc.Graph`).
- **M2 -- Interactive component. DONE (2026-07-20):** `UpSet(...)` with
  click-select exposed as declared component properties
  (`Input(id, "selected_intersection")` / `Input(id, "selected_sets")`),
  backed by the compiled React shim (see the 2026-07-20 addendum; originally
  shipped as an AIO composite). Still open from the original M2 scope:
  drill-into-members element table + a cross-filtering example.
- **M3 -- Analysis semantics, filtering, theming, polish.** Intersection
  `mode=` (distinct/intersect/union); deviation column + sort-by-deviation;
  min/max size, min/max degree, top-N filtering; count/percentage labels;
  light/dark + Plotly templates; vertical orientation; auto text descriptions
  (short + long) and the rest of the accessibility pass. `0.3.0`.
- **M4 -- Docs site + examples.** GitHub Pages (mirroring dash-seqviz's `docs/`
  approach) with live examples; conda-forge feedstock; first `1.0.0` when the
  API is stable.
- **M5 -- Advanced views (post-1.0).** Per-intersection attribute subplots
  (box/violin/strip/scatter/histogram, needing an attribute-carrying data
  model), query/highlight DSL, aggregation by degree/sets/overlaps, and
  bookmarks + undo/redo (a light `dcc.Store` Trrack analog). This is where
  Option C may become worthwhile if Plotly's ceiling is reached (evaluate
  wrapping the BSD-3 `upset2-react` first; see the M0 addendum). Priorities and
  the full feature landscape are in [SURVEY.md](./SURVEY.md).

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

- [SURVEY.md](./SURVEY.md) -- our competitive survey of the UpSet ecosystem
  (JavaScript/web, Python, R), the feature-comparison matrix, and the
  prioritized recommendations folded into the milestones above.
- UpSet technique and interactive reference: https://upset.app
- UpSet 2.0 (BSD-3-Clause, React; the technique authors' implementation):
  https://github.com/visdesignlab/upset2
- UpSet.js (AGPLv3): https://upset.js.org
- `upsetplot` (BSD, matplotlib): https://upsetplot.readthedocs.io
- ComplexUpset (R, the feature-completeness benchmark):
  https://krassowski.github.io/complex-upset/
- Accessible text descriptions for UpSet (EuroVis 2025):
  https://vdl.sci.utah.edu/publications/2025_eurovis_text-descriptions/
- Dash All-in-One components: https://dash.plotly.com/all-in-one-components
- Community Plotly UpSet discussion:
  https://community.plotly.com/t/plotly-upset-plot/63858
