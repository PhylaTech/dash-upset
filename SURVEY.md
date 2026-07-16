# UpSet tooling survey

A competitive survey of the existing UpSet-plot ecosystem (JavaScript/web,
Python, and R), plus the technique's conceptual model, done to guide the design
of `dash-upset`. It is a planning companion to [ROADMAP.md](./ROADMAP.md): the
ROADMAP says *what* we are building; this document surveys the field so our
feature set, API vocabulary, and interaction model are informed by what already
works (and what is missing) rather than invented from scratch.

Compiled 2026-07-16 from primary sources (papers, package docs, source code).
Where a fact could not be verified against a primary source it is marked
*(unverified)*.

## Contents

1. [Executive summary](#1-executive-summary)
2. [The landscape at a glance](#2-the-landscape-at-a-glance)
3. [Canonical vocabulary (adopt this)](#3-canonical-vocabulary-adopt-this)
4. [Intersection modes: the most important concept](#4-intersection-modes-the-most-important-concept)
5. [Feature comparison matrix](#5-feature-comparison-matrix)
6. [Dimension-by-dimension findings](#6-dimension-by-dimension-findings)
7. [Implementation patterns worth borrowing](#7-implementation-patterns-worth-borrowing)
8. [Gaps and opportunities](#8-gaps-and-opportunities)
9. [Recommendations for dash-upset](#9-recommendations-for-dash-upset)
10. [Sources](#10-sources)

---

## 1. Executive summary

**The Plotly-native approach is validated.** Every mature UpSet renderer builds
the same thing from primitive marks: a dot matrix with connecting lines, an
intersection-size bar chart aligned to one matrix axis, and a set-size bar chart
aligned to the other. The Vega-Lite community specs, the `plotly-upset` package,
and (conceptually) R's `ggupset` all compose exactly this from bars + points +
lines on shared axes. Our `go.Bar` + `go.Scatter` on shared subplot axes is the
same recipe: we are not fighting the tool.

**The interactive, Python/Dash-native niche is genuinely unfilled.** The
dominant Python library, `upsetplot`, is downloaded roughly 88k times/month but
is static matplotlib. Every existing Plotly attempt (`plotly-upset`,
`UpSetPlotly`, `upsetty`, `upset_plotly`) is thin, single-author, or dormant,
and none combines proper data loaders + attribute plots + interactivity. The
only best-in-class interactive implementations are `UpSet.js` (AGPLv3, which we
cannot wrap) and `UpSet 2` (BSD-3, a full React app, not a Python plotting API).
A polished, MIT-licensed, Plotly/Dash-native interactive UpSet does not exist.
That is our wedge.

**Five findings that should shape the roadmap:**

1. **Intersection modes (distinct / intersect / union) are the feature most
   quick ports omit** and the concept users most often misread. The mature R
   libraries treat the counting rule as a first-class parameter. We already
   compute the canonical *distinct* mode; we should expose `mode=` and add the
   other two. Compute-only, renders identically, high value. (See [§4](#4-intersection-modes-the-most-important-concept).)
2. **Auto-generated text descriptions are the highest-value, lowest-cost
   differentiator.** Only `UpSet 2` has them, and there is a 2025 EuroVis paper
   specifying exactly how (short alt-text + a six-section long description from a
   JSON plot spec). In pure Python this is deterministic string generation from
   a model we already build, and it delivers accessibility, notebook/publication
   captions, and an LLM-friendly surface at once.
3. **Per-intersection attribute subplots turn a bar chart into an analysis
   tool.** `upsetplot` (`add_catplot`), `UpSetR` (`attribute.plots`), and
   `ComplexUpset` (arbitrary annotations) all attach box/violin/strip/scatter/
   histogram panels per intersection. No Plotly tool does this well. It requires
   enriching our data model to carry per-element attributes.
4. **The right component architecture is `UpSet.js`'s stateless, fully-controlled
   contract:** selection is an input prop, hover/click are output events, no
   internal state. That maps perfectly onto a Dash All-in-One component
   (props in, `dcc.Store` + callbacks out). `UpSet 2` is our *feature* roadmap;
   `UpSet.js` is our *API-shape* template.
5. **Dataframe-agnostic input is now expected.** `altair-upset` accepts
   pandas and polars for free via Altair 5's internal narwhals layer. Our
   narwhals-based `from_indicators` already puts us on the right side of this.

---

## 2. The landscape at a glance

| Tool | Ecosystem | Stack | License | Interactive | Maintained | One-line |
|---|---|---|---|---|---|---|
| **upsetplot** | Python | matplotlib | BSD-3 | No | Yes | The de-facto Python standard; the data-model reference |
| **Marsilea** (`marsilea.upset`) | Python | matplotlib | MIT | No | Yes | Cleanest headless-data / renderer split |
| **plotly-upset** | Python | Plotly | MIT | Partial | Low (git-only) | Closest to our exact rendering recipe |
| **UpSetPlotly** | Python | Plotly | MIT | Partial | No (2021) | Plotly API + box/violin/swarm secondary plots |
| **upsetty** | Python | Plotly | MIT | Partial | Low (2024) | Minimal Plotly, boolean-df input |
| **altair-upset** | Python | Vega-Lite | MIT | Yes (bounded) | Yes | pandas+polars input; Vega selections |
| **pyUpSet** | Python | matplotlib | MIT | No | Abandoned | The design `upsetplot` replaced |
| **supervenn** | Python | matplotlib | MIT | No | Yes | UpSet-*adjacent* (proportional chunks, not a matrix) |
| **UpSetR** | R | grid/base | MIT | No | Feature-frozen | The classic; queries + attribute plots |
| **ComplexUpset** | R | ggplot2 | MIT | No | Yes | Feature-completeness benchmark |
| **ComplexHeatmap** (`UpSet`) | R | grid | MIT | No | Yes | Rigorous combination-matrix object + set algebra |
| **ggupset** | R | ggplot2 | GPL-3 | No | Yes | "The matrix is just the x-axis" pattern |
| **UpSet.js** | JS | React/Preact | **AGPLv3** + commercial | Yes | Low (since 2023) | Best-in-class interactivity; the one we cannot wrap |
| **UpSet 2** | JS | React + Recoil + Trrack | BSD-3 (npm says MIT) | Yes | Yes | The feature superset; provenance + text descriptions |
| **Original UpSet** | JS | D3 | permissive/academic | Yes | No | The 2014 technique reference (browser-based, not desktop) |
| **Vega-Lite / Observable** | JS | Vega-Lite | BSD-3 | Yes (bounded) | community | Bar+point+rule spec; validates the primitive-marks approach |

Notes: `Interactive = Partial` means the renderer inherits generic
pan/zoom/hover from Plotly or Vega but has no UpSet-specific interaction
(selection, cross-filter). The Venn/Euler family (`eulerr`, `venn`,
`ggVennDiagram`) is out of scope: those draw overlap regions and stop scaling
past ~5-7 sets, which is the exact problem UpSet exists to solve.

---

## 3. Canonical vocabulary (adopt this)

The 2014 paper (Lex, Gehlenborg, Strobelt, Vuillemot, Pfister, IEEE InfoVis;
Test-of-Time award 2024) defines terms the whole ecosystem inherits. We should
use them verbatim in our API and docs:

- **Set:** a named collection of elements. Rendered as a **set-size bar** (its
  cardinality) and a matrix column-or-row.
- **Combination matrix:** the grid of dots. One axis is sets, the other is
  intersections. A **filled dot** means the set participates in that
  intersection; a **light dot** means it does not; filled dots in a line are
  joined by a **connecting line** (Gestalt "connectedness") so a row reads as one
  relationship.
- **(Exclusive) intersection:** the atomic unit. For a membership code over the
  sets, the set of elements in exactly those sets and no others, e.g.
  `A and B and not C`. These partition the universe. The paper's term is
  *exclusive intersection*; ComplexHeatmap calls it *distinct*; UpSet.js calls it
  *distinctIntersection*. (See [§4](#4-intersection-modes-the-most-important-concept).)
- **Cardinality:** the size of an intersection (its element count), drawn as the
  **intersection-size bar**.
- **Degree:** the number of sets participating in an intersection (the number of
  filled dots in its row). Degree 0 = "in no set."
- **Aggregate:** a collection of exclusive intersections grouped by a rule
  (by degree, by set, by n-wise/pairwise overlap, or nested). Collapsible.
- **Deviation:** a signed measure of how *surprising* an intersection's size is
  versus what set sizes would predict under independence
  (`observed_probability - expected_probability`). Drawn as a signed bar column.
- **Query:** a selection. An **intersection query** specifies for each set
  *must include* / *may include* / *must not include* (fully Boolean with OR of
  clauses). An **element query** filters on element attributes (regex, numeric
  range). Queries link the **set view** and **element view** by color: this
  set-space/element-space linking is the technique's "duality."
- **Element view / attribute view:** a table of the underlying elements plus
  per-intersection attribute visualizations (box plots, scatter, histograms).

---

## 4. Intersection modes: the most important concept

This is the subtlest and most-misread part of UpSet, and the feature most quick
implementations skip. Read a combination as a code over sets, e.g. for sets
A, B, C the code **"110"** (A yes, B yes, C not-specified). Let **Q** be the
"yes" sets and **O** the others.

| Mode | Aliases | Set algebra for Q | "110" means | Cells overlap? |
|---|---|---|---|---|
| **Exclusive intersection** | `distinct` (default) | (intersect of Q) minus (union of O) | in A and B and **not** C | No: they **partition** the universe |
| **Inclusive intersection** | `intersect` | intersect of Q | in A and B, C ignored | Yes |
| **Inclusive union** | `union` | union of Q | in A **or** B, C ignored | Yes |
| **Exclusive union** | (ComplexUpset only) | (union of Q) minus (union of O) | in (A or B) and no other set | Partitions |

**Worked example.** A={1,2,3,4}, B={3,4,5}, C={4,6}; code "110":

- **intersect** = |A ∩ B| = |{3,4}| = **2**
- **distinct** = |A ∩ B \ C| = |{3}| = **1** (4 drops out, it is also in C)
- **union** = |A ∪ B| = |{1,2,3,4,5}| = **5**

The invariant is **distinct ≤ intersect ≤ union**. The consequence that trips
users up: in **distinct** mode the bars **partition** the data, so every element
is counted once and the intersection-size bars sum to the dataset size; in
**intersect**/**union** modes the cells **overlap**, an element is counted in
multiple bars, and the bars do **not** sum to the total, even though the matrix
and bars render identically.

**Who supports what:** `ComplexUpset` (all four), `ComplexHeatmap` and
`UpSet.js` (distinct/intersect/union), `UpSet 2` (distinct-centric).
`upsetplot`, `UpSetR`, `ggupset`, and every thin Plotly port are **distinct
only**. `UpSet.js`'s default is `intersect`, not distinct, which is a real
cross-tool inconsistency.

**For dash-upset:** we already compute distinct. Add a `mode=` parameter
defaulting to `"distinct"` (matches the canonical technique and `upsetplot`, and
is the only mode that partitions), accepting `{"distinct","intersect","union"}`
(and possibly `"exclusive_union"`). Surface the partition-vs-overlap fact in the
tooltip/labels so users do not misread overlapping bars.

---

## 5. Feature comparison matrix

Legend: `Y` full, `~` partial/limited, `N` none, `-` not applicable. Columns:
the tools most worth comparing against, plus dash-upset today and the target
state. Grouped by theme for readability; the tool columns are identical across
groups.

Column key: **uplt** = upsetplot, **p-up** = plotly-upset, **UpSetR** = UpSetR,
**CUp** = ComplexUpset, **UJS** = UpSet.js, **U2** = UpSet 2,
**du-now** = dash-upset today, **du-tgt** = dash-upset target.

### Ecosystem and I/O

| Capability | uplt | p-up | UpSetR | CUp | UJS | U2 | du-now | du-tgt |
|---|---|---|---|---|---|---|---|---|
| Interactive (UpSet-specific) | N | ~ | N | N | Y | Y | ~ | Y |
| Static export (PNG/SVG/PDF) | Y | Y | Y | Y | Y | ~ | Y | Y |
| Dataframe-agnostic input | N | N | N | N | - | - | Y | Y |
| `from_memberships`-style loader | Y | N | ~ | N | Y | ~ | Y | Y |
| `from_contents`-style loader | Y | N | Y | N | Y | ~ | Y | Y |
| `from_indicators` / boolean-df | Y | Y | Y | Y | ~ | Y | Y | Y |
| Counts / expression input | ~ | N | Y | N | N | N | Y | Y |
| Per-element attributes in model | Y | N | Y | Y | Y | Y | N | Y |

### Core grammar and layout

| Capability | uplt | p-up | UpSetR | CUp | UJS | U2 | du-now | du-tgt |
|---|---|---|---|---|---|---|---|---|
| Dot matrix + connectors | Y | Y | Y | Y | Y | Y | Y | Y |
| Set-size + intersection-size bars | Y | Y | Y | Y | Y | Y | Y | Y |
| Horizontal orientation | Y | Y | Y | Y | Y | ~ | Y | Y |
| Vertical orientation | Y | ~ | N | ~ | ~ | Y | N | Y |
| Count / percentage labels | Y | ~ | ~ | Y | ~ | ~ | ~ | Y |

### Analysis semantics

| Capability | uplt | p-up | UpSetR | CUp | UJS | U2 | du-now | du-tgt |
|---|---|---|---|---|---|---|---|---|
| Intersection modes (distinct/intersect/union) | N | N | N | Y | Y | ~ | N | Y |
| Sort by cardinality | Y | Y | Y | Y | Y | Y | Y | Y |
| Sort by degree | Y | N | Y | Y | Y | Y | Y | Y |
| Sort by deviation | N | N | N | ~ | N | Y | N | Y |
| Min/max size filter | Y | N | N | Y | ~ | ~ | N | Y |
| Min/max degree filter | Y | N | N | Y | Y | Y | N | Y |
| Top-N intersections | Y | N | Y | Y | Y | ~ | N | Y |
| Hide/show empty | Y | Y | Y | Y | Y | Y | Y | Y |
| Aggregation (by degree/set/overlap) | N | N | ~ | ~ | N | Y | N | ~ |
| Deviation column | N | N | N | ~ | N | Y | N | Y |

### Attribute/element and interaction

| Capability | uplt | p-up | UpSetR | CUp | UJS | U2 | du-now | du-tgt |
|---|---|---|---|---|---|---|---|---|
| Per-intersection attribute plots | Y | ~ | Y | Y | Y | Y | N | Y |
| Element / detail table | N | N | N | N | ~ | Y | N | Y |
| Query / highlight DSL | ~ | N | Y | Y | Y | Y | N | Y |
| Click-select / hover-select | N | ~ | N | N | Y | Y | ~ | Y |
| Cross-filter to linked views | N | N | N | N | Y | Y | N | Y |
| Provenance / undo-redo | N | N | N | N | N | Y | N | ~ |
| Bookmarks / shareable state | N | N | N | N | ~ | Y | N | ~ |

### Accessibility and theming

| Capability | uplt | p-up | UpSetR | CUp | UJS | U2 | du-now | du-tgt |
|---|---|---|---|---|---|---|---|---|
| Auto text descriptions / alt-text | N | N | N | N | N | Y | N | Y |
| Light/dark theming | ~ | ~ | ~ | Y | Y | ~ | ~ | Y |
| Set-level metadata annotations | N | N | Y | Y | N | ~ | N | ~ |

Reading the `du-now` vs `du-tgt` columns gives the gap analysis: today we have a
solid static core (grammar, both loaders, distinct mode, cardinality/degree
sort, hide-empty, static export, dataframe-agnostic input). The target column is
the roadmap that the rest of the ecosystem justifies.

---

## 6. Dimension-by-dimension findings

### Data input model

The ecosystem has converged on a canonical model: a boolean membership table
(one row per element, one column per set) plus optional per-element attribute
columns, fed by three loaders. `upsetplot` names them `from_memberships` (list
of category names per element), `from_contents` (mapping of set to member ids),
and `from_indicators` (boolean columns). `UpSetR` has the same triad
(`fromList`, indicator frame, `fromExpression`). We mirror these names, which
makes existing users' data drop straight in.

Two refinements from the survey:

- **`from_counts` is our own addition, not an upsetplot function.** Its real
  prior art is `UpSetR::fromExpression` (a named vector of pre-tabulated counts,
  e.g. `c(A=5, "A&B"=2)`). Important documented constraint to mirror: counts-only
  input carries no elements, so it *cannot* support attribute plots, element
  tables, or intersect/union modes. We should document `from_counts` as
  counts-only with those limitations.
- **The native internal representation should carry per-element attributes**
  (ComplexUpset's tidy "one row per element + covariate columns" model), because
  it is the only shape that enables attribute subplots and drill-down. Our
  current `UpSetData` keeps element ids but not arbitrary attributes; extending
  it to optionally carry an attribute frame is the enabler for the whole
  attribute-view feature line.

Marsilea and `upsetplot` both cleanly separate a **headless data model** (that
can be sorted, filtered, and queried without drawing) from the renderer, and
both **deep-copy** user data before mutating. We already have this separation
(`data.py` vs `figure.py`); keep it and add a headless `query()`-style transform
(as `upsetplot.query` does) so the future Dash component can recompute
subsets without touching the figure code.

### Sorting

The standard triad is **by cardinality**, **by degree**, and **by deviation**
(surprise). `UpSet 2` adds **by attribute-mean** and **by set** (pin a set).
`ComplexUpset` supports **composite keys** (e.g. degree then cardinality) and a
**ratio** sort. Deterministic tie-breaking matters: the paper breaks ties by
"the leftmost set," producing a legible left-to-right staircase. We implement
cardinality/degree with reverse; we should add deviation and keep our
deterministic tie-break.

### Filtering and scalability

Everyone needs **hide-empty**, **min/max subset size**, **min/max degree**, and
**top-N**, because the number of possible intersections is `2^k` and only
non-empty ones are worth drawing. The practical envelope for the technique is
~20-30 sets comfortably, ~40-50 as a hard ceiling, with element counts to ~50k
fine. `ComplexUpset` has the richest filter set (`min_size`, `max_size`,
`min_degree`, `max_degree`, `n_intersections`, `keep_empty_groups`). We have
hide-empty today; the rest is our M3 work and is cheap in pandas/narwhals.

### Aggregation

`UpSet 2` is the only tool with full interactive aggregation: **by degree**, **by
set**, **by deviation**, **by overlaps** (pairwise at a chosen degree), and
**nested** (e.g. sets then overlaps), all collapsible. The static libraries
mostly lack it (`UpSetR`'s `group.by` and `ComplexUpset`'s `group_by` are layout
grouping, not the full model). Aggregation is genuinely useful at scale but is
the most involved feature; it fits best in the interactive component, likely
post-1.0.

### Attribute and element views

This is what separates a bar chart from an analysis tool, and it is a clear
Plotly opportunity because no Plotly tool does it well:

- `upsetplot.add_catplot(kind=...)` dispatches to seaborn for
  point/bar/strip/swarm/box/violin/boxen per intersection; `add_stacked_bars`
  turns the size bar into a categorical composition.
- `UpSetR` has `boxplot.summary` (quick) and `attribute.plots` (general
  histogram/scatter, with query overlays).
- `ComplexUpset` is the benchmark: `aes(x=intersection, y=covariate)` + any
  ggplot geom, with per-annotation mode overrides. Because Plotly has no layered
  grammar, we should ship a **curated vocabulary** (box, violin, strip, scatter,
  histogram, stacked-bar) as extra subplot rows sharing the intersection axis,
  rather than "pass any expression."
- `ComplexHeatmap.extract_comb(m, code)` returns the elements of a combination:
  exactly the hook we need to power both attribute subplots and Dash
  click-to-drill-down.

### Queries, selection, interaction

Two poles. `UpSet.js` is a **stateless controlled component**: `selection` is an
input prop; `onHover`/`onClick` emit the hovered/clicked set-like back to the
host; `queries: {name, color, elems}[]` are named highlights. `UpSet 2` is a
**stateful app**: three-state Query-By-Sets (must/may/must-not) with a live
element-count preview, selections as chips, bookmarks, and cross-filtering to
the element table and plots. For a Dash component the `UpSet.js` model is the
right shape (Dash is props-in/callbacks-out); the `UpSet 2` feature set is what
to grow toward. In Plotly, clicking a bar or matrix row is `clickData`; the
"active query = solid bars, other queries = thin markers" idea from the paper
maps to overlaid `go.Bar` traces and per-dot marker color arrays.

### Provenance, bookmarking, sharing

Only `UpSet 2` has real provenance: Trrack tracks aggregations, sorts, set
add/remove, selections, and queries with full undo/redo, downloadable and
shareable. `UpSet.js`'s app serializes state to a compressed URL (`lz-string`).
For us this is post-1.0; a lightweight `dcc.Store` history stack is a reasonable
partial substitute.

### Accessibility

A distinct, well-developed line of work, and the standout cheap win. The 2025
EuroVis paper "Accessible Text Descriptions for UpSet Plots" (VDL) specifies a
**Short Description** (alt text: the single most salient pattern) and a
**Long Description** in six sections (introduction, dataset properties, set
properties, intersection properties, statistical information, trend analysis),
generated from a **JSON plot spec** via **templates**, grounded in Lundgard &
Satyanarayan's semantic levels 1-3 (chart structure, statistics, trends; level 4
domain interpretation left to humans). It also prescribes heading-based
screen-reader navigation, an inline glossary (degree, cardinality, deviation),
editable output, and a data-table alternative. `UpSet 2` ships this; nobody else
does. In Python it is deterministic string generation from the model we already
build: accessibility + notebook/publication captions + an LLM-friendly surface,
essentially for free.

### Theming and export

`UpSet.js` has the most complete theming (light/dark/Vega themes + a full color
prop set). `ComplexUpset` inherits all of ggplot2 theming plus stripes keyed to
set metadata. Static publication export is a strength of the R/Python static
libraries and, for us, a free win over every JS tool via kaleido (PNG/SVG/PDF).

---

## 7. Implementation patterns worth borrowing

1. **Stateless, fully-controlled component (UpSet.js).** No internal state;
   selection is a prop, interactions are events. This is the exact shape of a
   well-behaved Dash All-in-One component. Adopt it for our M2 component:
   `selected_intersection` / `selected_sets` as props, `clickData`/`hoverData`
   wired to callbacks.
2. **Core/view split (UpSet 2, Marsilea).** A framework-agnostic data/logic
   layer separate from the renderer. We already have `data.py` vs `figure.py`;
   the component layer should depend only on the data layer, never reach into
   figure internals.
3. **Headless, queryable data model (upsetplot `query()`, Marsilea `UpsetData`).**
   Sort/filter/aggregate/extract-members without drawing. Add a `query()`-style
   transform so the component recomputes subsets independently of rendering.
4. **The matrix is a shared categorical axis (ggupset, Vega-Lite specs).** Do
   not think of the matrix as a separate widget: it is the shared intersection
   axis that the size bars and every attribute subplot hang off. This is exactly
   how our `make_subplots` shared-x layout should be organized, and it makes
   adding attribute rows trivial.
5. **Tidy per-element + covariates as the native model (ComplexUpset).** Carry
   attributes on the elements so `x=intersection, y=covariate` attribute plots
   and drill-down come "for free."
6. **Precompute a stable intersection key (Vega-Lite specs).** Identify each
   intersection by a canonical key (sorted member names) so traces, selection,
   and callbacks address intersections unambiguously. We already give traces
   stable `meta` ids; extend that discipline to intersection identity.
7. **Deep-copy user data before mutating (Marsilea).** Cheap hygiene that avoids
   surprising callers.

---

## 8. Gaps and opportunities

Where the whole ecosystem is thin, and where dash-upset can lead:

- **Interactive + Python-native + permissively licensed does not exist.** Static
  matplotlib dominates; the interactive options are AGPL (`UpSet.js`) or a React
  app (`UpSet 2`). An MIT Plotly/Dash tool with hover-highlight, click-select,
  and drill-into-members is the open niche.
- **Attribute/element views in Plotly.** Rich in matplotlib/R, absent in Plotly.
  Plotly's native `box`/`violin`/`strip` traces make this natural for us.
- **Auto text descriptions outside UpSet 2.** A papered, expected accessibility
  feature that is nearly free in Python and that no Python library offers.
- **Dataframe-agnostic input.** Only `altair-upset` does it (via Altair's
  narwhals layer); `upsetplot` is pandas-locked. Our narwhals approach is
  current best practice.
- **Auto-layout polish.** The recurring pain in hand-rolled Plotly UpSets
  (a rejected `plotly.figure_factory` PR, forum threads) is label placement,
  margins, alignment, and shading, with a practical ~5-set ceiling. Solving this
  cleanly is table stakes for looking professional and is most of what our
  figure factory already does.

Two cautions the survey surfaced:

- **The exclusive/distinct default surprises people.** Whatever mode is active,
  make the counting rule visible so overlapping-mode bars are not misread as a
  partition.
- **Combinatorial blow-up is real.** Never materialize all `2^k` intersections;
  generate only non-empty (and degree-bounded) ones, and expose top-N/degree
  filters. `ComplexUpset` even has a guard parameter for this.

---

## 9. Recommendations for dash-upset

Mapped onto the existing milestones. "Cost" is rough implementation effort in
our Plotly/Python setting.

### Must-have (adopt; all feasible in pure Plotly/Python)

| Feature | Milestone | Cost | Why |
|---|---|---|---|
| `mode=` distinct/intersect/union | M1/M3 | Low | The #1 omitted feature; compute-only; we already do distinct |
| Deviation column + sort-by-deviation | M3 | Low | Closed-form; the paper's headline analytic; differentiates from UpSetR |
| Filtering: min/max size, min/max degree, top-N | M3 | Low | Expected by anyone from ComplexUpset; cheap in narwhals |
| Vertical orientation | M3 | Low | Standard; we have horizontal |
| Count + percentage labels | M3 | Low | Standard |
| Auto text description (short + long) | M3/M4 | Low-Med | Highest value/cost ratio; accessibility + captions + LLM surface |
| Per-intersection attribute subplots (box/violin/strip/scatter/hist) | M2/M3 | Med | Turns the plot into an analysis tool; needs attribute-carrying data model |
| Stateless controlled component (selection prop + click/hover events) | M2 | Med | The correct Dash AIO shape (UpSet.js pattern) |
| Element/detail table + drill-into-members | M2 | Med | `extract_comb`-style member access + `dash_table` |
| Query/highlight (highlight a set or an intersection) | M2/M3 | Med | `upset_query`-style DSL over overlaid traces |

### Nice-to-have (Dash plumbing; consider around/after 1.0)

- Cross-filtering the selection into linked Dash components (the core Dash
  selling point).
- Aggregation by degree/set/overlap (interactive; the involved one).
- Bookmarks + undo/redo via a `dcc.Store` history stack (a light Trrack analog).
- Download-selection and config/state (de)serialization; compressed-URL sharing.
- Set-level metadata annotations beside the set-size bars (UpSetR `set.metadata`).
- Composite and ratio sort keys (ComplexUpset).

### Defer / out of scope (low ROI in Plotly, or the Option-C territory)

- Drag-to-reorder sets (use dropdowns/relayout instead).
- Horizon bars and a dual adjustable scale (niche; hard in Plotly).
- Venn/Euler/Karnaugh alternate renderings.
- Full Trrack-grade non-linear provenance and live iframe sharing.
- Pixel-perfect custom hit-targets and matrix brushing: this is exactly the
  interaction ceiling the ROADMAP's "React renderer later" escape hatch (wrapping
  the BSD-3 `upset2-react`) is reserved for.

### API vocabulary guidance

Use the canonical terms so users transfer knowledge: `mode` in
`{"distinct","intersect","union"}` (default `"distinct"`, documented synonym
"exclusive intersection"); `degree`, `cardinality`, `deviation`;
`sort_by` in `{"cardinality","-cardinality","degree","-degree","deviation"}`;
`sort_sets_by`; `min_subset_size`/`max_subset_size`, `min_degree`/`max_degree`,
`max_subsets` (top-N); `show_counts`, `show_percentages`; `orientation`; and the
constructors `from_memberships`/`from_contents`/`from_indicators` (+ our
counts-only `from_counts`, documented with its limitations).

---

## 10. Sources

Primary sources consulted (papers, docs, source):

**Technique**
- Lex, Gehlenborg, Strobelt, Vuillemot, Pfister. "UpSet: Visualization of
  Intersecting Sets." IEEE InfoVis 2014. https://vdl.sci.utah.edu/publications/2014_infovis_upset/
  (PDF: https://sci.utah.edu/~vdl/papers/2014_infovis_upset.pdf)
- Gadhave, Strobelt, Gehlenborg, Lex. "UpSet 2: From Prototype to Tool." IEEE
  InfoVis Posters 2019. https://vdl.sci.utah.edu/publications/2019_infovis_upset/
- McNutt et al. "Accessible Text Descriptions for UpSet Plots." CGF (EuroVis)
  2025. https://vdl.sci.utah.edu/publications/2025_eurovis_text-descriptions/
  (arXiv: https://arxiv.org/abs/2503.17517)
- upset.app (technique overview + implementation list): https://upset.app/

**JavaScript / web**
- UpSet.js: https://github.com/upsetjs/upsetjs, https://upset.js.org (modes:
  https://upset.js.org/docs/components/modes/)
- UpSet 2: https://github.com/visdesignlab/upset2, https://upset.multinet.app,
  docs https://vdl.sci.utah.edu/upset2/
- Original UpSet: https://github.com/VCG/upset
- Vega-Lite / Observable UpSet: https://observablehq.com/@mdeagen/interactive-upset-plot-vega-lite

**Python**
- upsetplot: https://upsetplot.readthedocs.io, https://github.com/jnothman/UpSetPlot
- Marsilea: https://marsilea.readthedocs.io/en/stable/tutorial/upset.html
- plotly-upset: https://github.com/hshhrr/plotly-upset
- UpSetPlotly: https://github.com/kevinkovalchik/UpSetPlotly
- upsetty: https://github.com/eskin22/upsetty
- altair-upset: https://github.com/edmundmiller/altair-upset
- Plotly community thread + rejected figure_factory PR:
  https://community.plotly.com/t/plotly-upset-plot/63858

**R**
- UpSetR: https://github.com/hms-dbmi/UpSetR (paper: Conway, Lex, Gehlenborg,
  Bioinformatics 2017, https://www.ncbi.nlm.nih.gov/pmc/articles/PMC5870712/)
- ComplexUpset: https://krassowski.github.io/complex-upset/,
  https://github.com/krassowski/complex-upset
- ComplexHeatmap UpSet chapter:
  https://jokergoo.github.io/ComplexHeatmap-reference/book/upset-plot.html
- ggupset: https://github.com/const-ae/ggupset

**Flagged as unverified in the underlying research:** ComplexUpset's
`exclusive_union` set algebra (triangulated across four sources, no single
verbatim table); UpSet.js full-transpose orientation and its accessibility
(absence-based); UpSet 2's exact static-image export mechanism; the
`@visdesignlab/upset2-react` npm-MIT vs repo-BSD-3 discrepancy (both confirmed;
canonical = BSD-3).
