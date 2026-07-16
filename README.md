# dash-upset

Interactive [UpSet plots](https://upset.app) for [Plotly Dash](https://dash.plotly.com).

> **Status: early development (pre-1.0).** This repository currently contains
> the project scaffolding (packaging, environment, release automation, CI) and
> a [roadmap](./ROADMAP.md). The rendering approach is an open decision that is
> documented in the roadmap. The public API has not landed yet.

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

There is no first-class UpSet component for Dash. The most capable JavaScript
implementation, [UpSet.js](https://upset.js.org), is licensed **AGPLv3** (a
commercial license is required otherwise), which makes it unsuitable to wrap in
a permissively licensed, publicly published library. `dash-upset` therefore
builds an UpSet renderer on a clean, MIT-compatible foundation. See the
[roadmap](./ROADMAP.md) for the full analysis and the options under
consideration.

## Installation

`dash-upset` is not published yet. Once released:

```bash
# conda-forge (preferred)
conda install -c conda-forge dash-upset

# or pip
pip install dash-upset
```

## Quick start

The component API is defined in the [roadmap](./ROADMAP.md) and will be filled
in during the implementation phase. The intended shape is a drop-in Dash
component fed a set-membership data structure:

```python
# Planned API (not yet implemented; see ROADMAP.md)
from dash import Dash
from dash_upset import UpSet

app = Dash(__name__)
app.layout = UpSet(
    id="movies",
    memberships={
        "Action": 320, "Comedy": 290, "Drama": 410,
        "Action&Comedy": 84, "Action&Drama": 120, "Comedy&Drama": 96,
        "Action&Comedy&Drama": 40,
    },
)

if __name__ == "__main__":
    app.run(debug=True)
```

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
- [UpSet.js](https://upset.js.org) by Samuel Gratzl is the reference
  interactive JS implementation (AGPLv3 / commercial).
- [`upsetplot`](https://upsetplot.readthedocs.io) by Joel Nothman (BSD-3-Clause)
  is the established matplotlib-based Python package; `dash-upset` mirrors its
  familiar data-input conventions.

## License

[MIT](./LICENSE) © Evan Roy Rees
