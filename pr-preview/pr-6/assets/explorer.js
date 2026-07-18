/* dash-upset Component Explorer wiring.
 *
 * Reads the controls, rebuilds the plot via DashUpset.buildFigure (see
 * assets/upset.js), updates the readouts, and regenerates the matching
 * create_upset(...) Python snippet on every change.
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
        showEmpty: document.getElementById("ctrl-showempty"),
        snippet: document.querySelector("#live-snippet code"),
        rSets: document.getElementById("readout-sets"),
        rSubsets: document.getElementById("readout-subsets"),
        rTotal: document.getElementById("readout-total"),
    };

    datasets.forEach(function (d, i) {
        var opt = document.createElement("option");
        opt.value = String(i);
        opt.textContent = d.title;
        el.dataset.appendChild(opt);
    });

    function num(input) {
        if (input.value === "" || input.value == null) return null;
        var v = Number(input.value);
        return isNaN(v) ? null : v;
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
            showEmpty: el.showEmpty.checked,
            height: 460,
        };
    }

    function pyValue(v) {
        if (typeof v === "boolean") return v ? "True" : "False";
        if (typeof v === "string") return '"' + v + '"';
        return String(v);
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
        if (!opts.showCounts) args.push("show_counts=False");
        if (opts.showEmpty) args.push("show_empty=True");
        args.push('title="' + dataset.title + '"');

        var argText = args.map(function (a) { return "    " + a + ","; }).join("\n");
        return (
            "from dash import Dash, dcc\n" +
            "from dash_upset import create_upset, from_counts\n\n" +
            "fig = create_upset(\n" +
            "    from_counts({\n" +
            lines.join(",\n") + ",\n" +
            "    }),\n" +
            argText + "\n" +
            ")\n\n" +
            "app = Dash(__name__)\n" +
            "app.layout = dcc.Graph(figure=fig)\n\n" +
            'if __name__ == "__main__":\n' +
            "    app.run(debug=True)\n"
        );
    }

    function render() {
        var dataset = datasets[Number(el.dataset.value) || 0];
        var opts = readOptions();
        var fig = window.DashUpset.buildFigure(dataset.model, opts);

        if (!fig) {
            Plotly.purge(root);
            root.innerHTML =
                '<p style="padding:24px;color:var(--color-text-muted);font-size:0.9rem;">' +
                "No subsets match these filters. Loosen a filter to see the plot.</p>";
            el.rSubsets.innerHTML = "subsets shown: <strong>0</strong>";
        } else {
            Plotly.react(root, fig.data, fig.layout, fig.config);
            var barTrace = fig.data[0];
            el.rSubsets.innerHTML = "subsets shown: <strong>" + barTrace.y.length + "</strong>";
        }
        el.rSets.innerHTML = "sets: <strong>" + dataset.model.setNames.length + "</strong>";
        el.rTotal.innerHTML = "total elements: <strong>" + dataset.model.total.toLocaleString() + "</strong>";
        el.snippet.textContent = buildSnippet(dataset, opts);
        if (window.DashUpsetSite && window.DashUpsetSite.wireCopy) {
            window.DashUpsetSite.wireCopy(document);
        }
    }

    Object.keys(el).forEach(function (k) {
        var node = el[k];
        if (node && (node.tagName === "SELECT" || node.tagName === "INPUT")) {
            node.addEventListener(node.type === "checkbox" || node.tagName === "SELECT" ? "change" : "input", render);
        }
    });

    render();
})();
