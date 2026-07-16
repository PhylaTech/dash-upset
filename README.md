# dash-upset

Interactive [UpSet plots](https://upset.app) for [Plotly Dash](https://dash.plotly.com).

> **Status: early development (pre-1.0).** The data model and the static
> figure factory (`create_upset`, roadmap milestone M1) are implemented and
> tested. The self-wiring `UpSet(...)` Dash component with click-selection
> callbacks is next (M2); see the [roadmap](./ROADMAP.md). Not yet published
> to PyPI or conda-forge.

## What is an UpSet plot?

An UpSet plot visualizes the intersections of many sets. Venn and Euler
diagrams become unreadable past three or four sets; UpSet replaces the
overlapping circles with:

- a **matrix** whose columns are sets and whose rows are intersections (filled,
  connected dots show which sets participate in each intersection),
- **set-size bars** giving the cardinality of each individual set, and
- **intersection-size bars** giving the size of each intersection.

This scales to dozens of sets and makes the large intersections obvious at a
glance. `dash-upset` aims to bring this to Dash as a reusable, themeable,
callback-friendly component.

## Why this exists

There is no first-class UpSet component for Dash, and wrapping the existing
JavaScript implementations has real costs: [UpSet.js](https://upset.js.org) is
**AGPLv3** (unsuitable for a permissively licensed library), and while
[UpSet 2.0](https://github.com/visdesignlab/upset2) is BSD-3-Clause, embedding
its React stack would drag a JavaScript build toolchain and a heavy dependency
tree into every app, and would give up notebook rendering and static export.
`dash-upset` therefore composes the figure from Plotly primitives in pure
Python: MIT-clean, notebook-friendly, no JavaScript build step, with
`upset2-react` documented as the fallback engine if Plotly's interaction
ceiling is ever reached. See the [roadmap](./ROADMAP.md) for the full analysis
and the decision record.

## Installation

`dash-upset` is not published yet. Once released:

```bash
# conda-forge (preferred)
conda install -c conda-forge dash-upset

# or pip
pip install dash-upset
```

## Quick start

Build a data model with one of the `from_*` constructors, then render it with
`create_upset`. For pre-aggregated intersection counts:

```python
from dash_upset import create_upset, from_counts

fig = create_upset(
    from_counts({
        "Action": 320, "Comedy": 290, "Drama": 410,
        "Action&Comedy": 84, "Action&Drama": 120, "Comedy&Drama": 96,
        "Action&Comedy&Drama": 40,
    }),
    title="Movie genres",
)
fig.show()  # a plain plotly Figure: notebooks, scripts, static export
```

Element-level data uses the familiar
[`upsetplot`](https://upsetplot.readthedocs.io) conventions:

```python
from dash_upset import from_contents, from_indicators, from_memberships

from_memberships([("A",), ("A", "B"), ()])          # per-element set names
from_contents({"A": ["x", "y"], "B": ["y", "z"]})   # per-set element ids
from_indicators(boolean_dataframe)                  # rows = elements, columns = sets
```

`from_indicators` is dataframe-agnostic via
[narwhals](https://github.com/narwhals-dev/narwhals): pandas, Polars, PyArrow,
cuDF, and Modin frames (or a plain dict of boolean columns) all work, and
`dash-upset` itself depends on none of those libraries.

Sorting and display are controlled per figure, e.g.
`create_upset(data, sort_by="degree", sort_sets_by="name", show_counts=False)`.

In a Dash app today, embed the figure in a `dcc.Graph`:

```python
from dash import Dash, dcc
from dash_upset import create_upset, from_contents

app = Dash(__name__)
app.layout = dcc.Graph(figure=create_upset(from_contents({...})))

if __name__ == "__main__":
    app.run(debug=True)
```

The self-wiring `UpSet(...)` component (hover/click selection exposed as
callback outputs) is roadmap milestone M2.

## Development

This project uses [pixi](https://pixi.sh) for environment and task management.

```bash
pixi install          # create the environment (deps from conda-forge)
pixi run test         # run the test suite
pixi run lint         # ruff lint
pixi run format       # ruff format
```

See [CONTRIBUTING.md](./CONTRIBUTING.md) for the commit conventions that drive
releases.

## Prior art and credits

- [UpSet](https://upset.app) and the original research by Lex, Gehlenborg,
  et al. define the technique.
- [UpSet 2.0](https://github.com/visdesignlab/upset2) by the Visualization
  Design Lab (BSD-3-Clause) is the technique authors' interactive
  reimplementation and the documented candidate engine should this library
  ever add a JavaScript renderer (see the roadmap).
- [UpSet.js](https://upset.js.org) by Samuel Gratzl is an interactive JS
  implementation (AGPLv3 / commercial).
- [`upsetplot`](https://upsetplot.readthedocs.io) by Joel Nothman (BSD-3-Clause)
  is the established matplotlib-based Python package; `dash-upset` mirrors its
  familiar data-input conventions.

## License

[MIT](./LICENSE) © Evan Roy Rees
