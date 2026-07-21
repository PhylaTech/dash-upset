/* dash-upset Component Explorer wiring.
 *
 * Reads the controls, rebuilds the plot via DashUpset.buildFigure (see
 * assets/upset.js), regenerates the matching UpSet(...) Python snippet, and
 * -- on click -- surfaces the component's real callback properties
 * (selected_intersection / selected_sets) via DashUpset.selectionFromClick.
 */
(function () {
    "use strict";

    var datasets = window.DASH_UPSET_DATASETS || [];
    var root = document.getElementById("upset-root");
    var fallback = document.getElementById("upset-fallback");
    if (!root || !datasets.length || !window.Plotly || !window.DashUpset) {
        if (fallback) fallback.hidden = false;
        if (root) root.hidden = true;
        return;
    }

    var el = {
        dataset: document.getElementById("ctrl-dataset"),
        mode: document.getElementById("ctrl-mode"),
        sortBy: document.getElementById("ctrl-sortby"),
        sortSetsBy: document.getElementById("ctrl-sortsets"),
        minSize: document.getElementById("ctrl-minsize"),
        maxSize: document.getElementById("ctrl-maxsize"),
        minDegree: document.getElementById("ctrl-mindegree"),
        maxDegree: document.getElementById("ctrl-maxdegree"),
        maxSubsets: document.getElementById("ctrl-maxsubsets"),
        showCounts: document.getElementById("ctrl-showcounts"),
        showPct: document.getElementById("ctrl-showpct"),
        showEmpty: document.getElementById("ctrl-showempty"),
        theme: document.getElementById("ctrl-theme"),
        color: document.getElementById("ctrl-color"),
        inactive: document.getElementById("ctrl-inactive"),
        title: document.getElementById("ctrl-title"),
        snippet: document.querySelector("#live-snippet code"),
        roIntersection: document.getElementById("ro-intersection"),
        roSets: document.getElementById("ro-sets"),
    };

    datasets.forEach(function (d, i) {
        var opt = document.createElement("option");
        opt.value = String(i);
        opt.textContent = d.title;
        el.dataset.appendChild(opt);
    });

    // Default to the model-errors dataset (a data-science framing that shows
    // the component's utility better than the movie-genre toy set).
    var defaultIdx = datasets.findIndex(function (d) { return d.id === "model-errors"; });
    if (defaultIdx >= 0) el.dataset.value = String(defaultIdx);

    function num(input) {
        if (input.value === "" || input.value == null) return null;
        var v = Number(input.value);
        return isNaN(v) ? null : v;
    }
    function str(input) {
        var v = (input.value || "").trim();
        return v === "" ? null : v;
    }

    function readOptions() {
        return {
            mode: el.mode.value,
            sortBy: el.sortBy.value,
            sortSetsBy: el.sortSetsBy.value,
            minSize: num(el.minSize),
            maxSize: num(el.maxSize),
            minDegree: num(el.minDegree),
            maxDegree: num(el.maxDegree),
            maxSubsets: num(el.maxSubsets),
            showCounts: el.showCounts.checked,
            showPercentages: el.showPct.checked,
            showEmpty: el.showEmpty.checked,
            theme: el.theme.value,
            color: str(el.color),
            inactiveColor: str(el.inactive),
            title: str(el.title),
            height: 460,
        };
    }

    function buildSnippet(dataset, opts) {
        var lines = Object.keys(dataset.counts).map(function (combo) {
            return '        "' + combo + '": ' + dataset.counts[combo];
        });
        // Only emit args that differ from create_upset's defaults.
        var args = [];
        if (opts.mode !== "distinct") args.push('mode="' + opts.mode + '"');
        if (opts.sortBy !== "cardinality") args.push('sort_by="' + opts.sortBy + '"');
        if (opts.sortSetsBy !== "cardinality") args.push('sort_sets_by="' + opts.sortSetsBy + '"');
        if (opts.minSize != null) args.push("min_subset_size=" + opts.minSize);
        if (opts.maxSize != null) args.push("max_subset_size=" + opts.maxSize);
        if (opts.minDegree != null) args.push("min_degree=" + opts.minDegree);
        if (opts.maxDegree != null) args.push("max_degree=" + opts.maxDegree);
        if (opts.maxSubsets != null) args.push("max_subsets=" + opts.maxSubsets);
        if (opts.showEmpty) args.push("show_empty=True");
        if (!opts.showCounts) args.push("show_counts=False");
        if (opts.showPercentages) args.push("show_percentages=True");
        if (opts.theme !== "light") args.push('theme="' + opts.theme + '"');
        if (opts.color) args.push('color="' + opts.color + '"');
        if (opts.inactiveColor) args.push('inactive_color="' + opts.inactiveColor + '"');
        if (opts.title) args.push('title="' + opts.title + '"');

        var argText = args.map(function (a) { return "    " + a + ","; }).join("\n");
        return (
            "from dash import Dash\n" +
            "from dash_upset import UpSet, from_counts\n\n" +
            "app = Dash(__name__)\n" +
            "app.layout = UpSet(\n" +
            '    id="upset",\n' +
            "    data=from_counts({\n" +
            lines.join(",\n") + ",\n" +
            "    }),\n" +
            argText + "\n" +
            ")\n\n" +
            'if __name__ == "__main__":\n' +
            "    app.run(debug=True)\n"
        );
    }

    function resetReadouts() {
        el.roIntersection.textContent = "None";
        el.roSets.textContent = "[]";
    }

    // Selection: mirror the compiled component. A click on a bar/dot updates
    // the property readout, just as it would drive a Dash callback.
    function onClick(data) {
        var point = data && data.points && data.points[0];
        var sel = window.DashUpset.selectionFromClick(point);
        if (!sel) return;
        if (sel.prop === "selected_intersection") {
            el.roIntersection.textContent = JSON.stringify(sel.value);
        } else if (sel.prop === "selected_sets") {
            el.roSets.textContent = JSON.stringify(sel.value);
        }
    }

    function render() {
        var dataset = datasets[Number(el.dataset.value) || 0];
        var opts = readOptions();
        var fig = window.DashUpset.buildFigure(dataset.model, opts);

        if (!fig) {
            window.Plotly.purge(root);
            root.innerHTML =
                '<p style="padding:24px;color:var(--color-text-muted);font-size:0.9rem;">' +
                "No subsets match these filters. Loosen a filter to see the plot.</p>";
        } else {
            window.Plotly.react(root, fig.data, fig.layout, fig.config);
            // Rebind after every (re)render: Plotly.purge on the no-subsets
            // path drops handlers, so re-attach fresh and de-dupe.
            if (root.removeAllListeners) root.removeAllListeners("plotly_click");
            root.on("plotly_click", onClick);
        }
        resetReadouts();
        el.snippet.textContent = buildSnippet(dataset, opts);
        if (window.DashUpsetSite && window.DashUpsetSite.wireCopy) {
            window.DashUpsetSite.wireCopy(document);
        }
    }

    Object.keys(el).forEach(function (k) {
        var node = el[k];
        if (node && (node.tagName === "SELECT" || node.tagName === "INPUT")) {
            var evt = node.type === "checkbox" || node.tagName === "SELECT" ? "change" : "input";
            node.addEventListener(evt, render);
        }
    });

    render();
})();
