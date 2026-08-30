# conda-forge staged-recipes submission checklist

This document describes how to submit the `dash-upset` recipe to conda-forge
so that `conda install -c conda-forge dash-upset` works.

## Pre-flight

- [x] PyPI has a published sdist (`dash_upset-0.1.0.tar.gz`).
- [x] The sdist includes `dash_upset_component/` with the compiled JS bundle,
      so no Node toolchain is needed at build time.
- [x] `recipe.yaml` (v1 / rattler-build) lives in `conda-recipe/` in this repo
      and has been reviewed.  A `meta.yaml` (v0 / conda-build) fallback is also
      provided.
- [x] Recipe sha256 matches the PyPI sdist.
- [x] `noarch: python` -- no compiled extensions, platform-independent.
- [x] License is MIT; `LICENSE` file is included.
- [x] Runtime deps: `dash >=3.0.0`, `plotly >=5.20`, `narwhals >=2` -- all
      already on conda-forge.
- [x] Import smoke test covers `dash_upset`, `dash_upset.data`,
      `dash_upset.figure`, and `dash_upset_component`.

## Steps to open the staged-recipes PR

1. **Fork** [conda-forge/staged-recipes](https://github.com/conda-forge/staged-recipes).

2. **Create a branch** off `main`, e.g. `add-dash-upset`.

3. **Copy** `conda-recipe/recipe.yaml` from this repo into
   `recipes/dash-upset/recipe.yaml` in the staged-recipes fork.
   Only `recipe.yaml` is needed (do not copy `meta.yaml`; the v1 format is
   preferred for new submissions).

4. **Update `extra.recipe-maintainers`** to list the GitHub username(s) of
   whoever will maintain the feedstock.  The placeholder is `evanroyrees`.

5. **Push and open a PR** against `conda-forge/staged-recipes:main`.

6. **Expected CI lint notes** (non-blocking):
   - `recipe_maintainer_is_not_a_cf_member` -- normal for first-time
     submissions; a conda-forge member will approve.
   - Verify the CI build passes on the `noarch` job (Linux only for `noarch:
     python`).

7. **Wait for review.**  A conda-forge reviewer will merge the PR, which
   creates the `conda-forge/dash-upset-feedstock` repo automatically.

## After the feedstock exists

- Verify `conda install -c conda-forge dash-upset` works.
- Re-enable conda/mamba install instructions in `README.md` and the docs site
  (`docs/index.html`, `docs/explorer.html`).
- Delete `STAGED_RECIPES.md` from this repo if desired.

## Version bumps

The recipe currently targets **0.1.0** (the latest version on PyPI at the time
of writing).  If a newer version (e.g. 0.1.1) is published to PyPI before the
staged-recipes PR is merged:

1. Update `context.version` in `recipe.yaml` to the new version.
2. Update the `sha256` to match the new sdist.  Get it with:
   ```
   curl -sL https://pypi.org/packages/source/d/dash-upset/dash_upset-<VERSION>.tar.gz | sha256sum
   ```
3. Set `build.number` back to `0` (it resets on every new upstream version).
