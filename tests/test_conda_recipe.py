"""Smoke tests for the conda-forge recipe files.

These validate that the recipe YAML is well-formed and contains the expected
package metadata, deps, and test imports -- without needing rattler-build or
conda-build installed.
"""

from pathlib import Path

import yaml

RECIPE_DIR = Path(__file__).resolve().parent.parent / "conda-recipe"


class TestRecipeYaml:
    """Tests for the v1 recipe.yaml (rattler-build format)."""

    def _load(self):
        import re

        text = (RECIPE_DIR / "recipe.yaml").read_text()
        # Replace ${{ expr }} with the expression text, then quote any
        # unquoted values that still look broken after substitution.
        cleaned = re.sub(r"\$\{\{\s*(.*?)\s*\}\}", r"PLACEHOLDER", text)
        return yaml.safe_load(cleaned)

    def test_file_exists(self):
        assert (RECIPE_DIR / "recipe.yaml").exists()

    def test_schema_version(self):
        data = self._load()
        assert data["schema_version"] == 1

    def test_package_name(self):
        data = self._load()
        assert data["package"]["name"] == "dash-upset"

    def test_noarch_python(self):
        data = self._load()
        assert data["build"]["noarch"] == "python"

    def test_build_number_zero(self):
        data = self._load()
        assert data["build"]["number"] == 0

    def test_runtime_deps(self):
        data = self._load()
        run_deps = data["requirements"]["run"]
        dep_names = [d.split()[0] for d in run_deps]
        assert "dash" in dep_names
        assert "plotly" in dep_names
        assert "narwhals" in dep_names

    def test_host_has_hatchling(self):
        data = self._load()
        host_deps = data["requirements"]["host"]
        dep_names = [d.split()[0] for d in host_deps]
        assert "hatchling" in dep_names

    def test_imports_include_component(self):
        data = self._load()
        imports = data["tests"][0]["python"]["imports"]
        assert "dash_upset" in imports
        assert "dash_upset_component" in imports

    def test_license_is_mit(self):
        data = self._load()
        assert data["about"]["license"] == "MIT"

    def test_source_url_points_to_pypi(self):
        data = self._load()
        url = data["source"]["url"]
        assert "pypi.org" in url
        assert "dash-upset" in url or "dash_upset" in url

    def test_sha256_present(self):
        data = self._load()
        sha = data["source"]["sha256"]
        assert isinstance(sha, str)
        assert len(sha) == 64


class TestMetaYaml:
    """Tests for the v0 meta.yaml (conda-build format)."""

    def _load(self):
        import re

        text = (RECIPE_DIR / "meta.yaml").read_text()
        # Strip Jinja2 set-blocks and replace {{ var }} with a plain word
        # so PyYAML can parse the structure.
        text = re.sub(r"\{%.*?%\}", "", text)
        text = re.sub(r"\{\{\s*(.*?)\s*\}\}", "PLACEHOLDER", text)
        return yaml.safe_load(text)

    def test_file_exists(self):
        assert (RECIPE_DIR / "meta.yaml").exists()

    def test_package_name(self):
        data = self._load()
        assert data["package"]["name"] == "dash-upset"

    def test_noarch_python(self):
        data = self._load()
        assert data["build"]["noarch"] == "python"

    def test_runtime_deps(self):
        data = self._load()
        run_deps = data["requirements"]["run"]
        dep_names = [d.split()[0] for d in run_deps if d != "PLACEHOLDER"]
        assert "dash" in dep_names
        assert "plotly" in dep_names
        assert "narwhals" in dep_names

    def test_test_imports(self):
        data = self._load()
        imports = data["test"]["imports"]
        assert "dash_upset" in imports
        assert "dash_upset_component" in imports

    def test_license_is_mit(self):
        data = self._load()
        assert data["about"]["license"] == "MIT"
