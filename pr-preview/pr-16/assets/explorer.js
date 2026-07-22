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
        orientation: document.getElementById("ctrl-orientation"),
        color: document.getElementById("ctrl-color"),
        inactiveOn: document.getElementById("ctrl-inactive-on"),
        inactive: document.getElementById("ctrl-inactive"),
        title: document.getElementById("ctrl-title"),
        showIntTitle: document.getElementById("ctrl-show-inttitle"),
        intTitle: document.getElementById("ctrl-inttitle"),
        showSetTitle: document.getElementById("ctrl-show-settitle"),
        setTitle: document.getElementById("ctrl-settitle"),
        intTicks: document.getElementById("ctrl-intticks"),
        setTicks: document.getElementById("ctrl-setticks"),
        highlight: document.getElementById("ctrl-highlight"),
        selColor: document.getElementById("ctrl-selcolor"),
        description: document.getElementById("ctrl-desc"),
        snippet: document.querySelector("#live-snippet code"),
        roIntersection: document.getElementById("ro-intersection"),
        roSets: document.getElementById("ro-sets"),
    };

    var baseColors = {};

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
            orientation: el.orientation.value,
            color: str(el.color),
            // Color pickers always carry a value; inactive applies only when
            // its override checkbox is ticked (else the theme default stands).
            inactiveColor: el.inactiveOn.checked ? el.inactive.value : null,
            title: str(el.title),
            description: str(el.description),
            // Axis titles: unchecked -> hide (null); checked + blank -> auto
            // (undefined); checked + text -> override.
            intersectionTitle: !el.showIntTitle.checked ? null : (str(el.intTitle) || undefined),
            setSizeTitle: !el.showSetTitle.checked ? null : (str(el.setTitle) || undefined),
            showIntersectionTicks: el.intTicks.checked,
            showSetSizeTicks: el.setTicks.checked,
            // Component (interaction) props, not figure args:
            highlightSelection: el.highlight.checked,
            selectionColor: el.selColor.value || "#9c5a3c",
            // No fixed height: the plot autosizes to fill the canvas (which is
            // sized by the no-scroll viewport lock).
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
        if (opts.orientation && opts.orientation !== "horizontal") args.push('orientation="' + opts.orientation + '"');
        if (opts.theme !== "light") args.push('theme="' + opts.theme + '"');
        if (opts.color) args.push('color="' + opts.color + '"');
        if (opts.inactiveColor) args.push('inactive_color="' + opts.inactiveColor + '"');
        if (opts.title) args.push('title="' + opts.title + '"');
        if (opts.description) args.push('description="' + opts.description.replace(/"/g, '\\"') + '"');
        if (opts.intersectionTitle === null) args.push("intersection_title=None");
        else if (opts.intersectionTitle) args.push('intersection_title="' + opts.intersectionTitle + '"');
        if (opts.setSizeTitle === null) args.push("set_size_title=None");
        else if (opts.setSizeTitle) args.push('set_size_title="' + opts.setSizeTitle + '"');
        if (!opts.showIntersectionTicks) args.push("show_intersection_ticks=False");
        if (!opts.showSetSizeTicks) args.push("show_set_size_ticks=False");
        if (!opts.highlightSelection) args.push("highlight_selection=False");
        if (opts.selectionColor !== "#9c5a3c") args.push('selection_color="' + opts.selectionColor + '"');

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
    // the property readout (as it would drive a Dash callback) and, when
    // highlight_selection is on, recolors the selected marks.
    function onClick(data) {
        var point = data && data.points && data.points[0];
        var sel = window.DashUpset.selectionFromClick(point);
        if (!sel) return;
        if (sel.prop === "selected_intersection") {
            el.roIntersection.textContent = JSON.stringify(sel.value);
        } else if (sel.prop === "selected_sets") {
            el.roSets.textContent = JSON.stringify(sel.value);
        }
        if (el.highlight.checked && sel.target) {
            var color = (el.selColor.value || "").trim() || "#9c5a3c";
            window.DashUpset.applyHighlight(root, baseColors, sel.target, color);
        }
    }

    function render() {
        var dataset = datasets[Number(el.dataset.value) || 0];
        var opts = readOptions();
        var fig = window.DashUpset.buildFigure(dataset.model, opts);

        // The inactive-color picker is live only when its override is ticked.
        el.inactive.disabled = !el.inactiveOn.checked;

        if (!fig) {
            window.Plotly.purge(root);
            root.innerHTML =
                '<p style="padding:24px;color:var(--color-text-muted);font-size:0.9rem;">' +
                "No subsets match these filters. Loosen a filter to see the plot.</p>";
        } else {
            window.Plotly.react(root, fig.data, fig.layout, fig.config);
            // Autosized figure: fit it to the (viewport-locked) canvas.
            window.Plotly.Plots.resize(root);
            // Accessibility: expose the figure's description as the graph's
            // aria-label, exactly as the compiled component does.
            var desc = fig.layout && fig.layout.meta && fig.layout.meta.description;
            if (desc) { root.setAttribute("role", "img"); root.setAttribute("aria-label", desc); }
            // Snapshot the base colors so click-highlight paints over them.
            baseColors = window.DashUpset.baseColorsOf(fig);
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

    // Export the current (customized) figure as a static image.
    function exportImage(format) {
        if (!root.classList.contains("js-plotly-plot")) return;
        var box = root.getBoundingClientRect();
        window.Plotly.downloadImage(root, {
            format: format,
            filename: "upset",
            width: Math.round(box.width) || 900,
            height: Math.round(box.height) || 520,
            scale: format === "png" ? 2 : 1,
        });
    }
    var pngBtn = document.getElementById("btn-export-png");
    var svgBtn = document.getElementById("btn-export-svg");
    if (pngBtn) pngBtn.addEventListener("click", function () { exportImage("png"); });
    if (svgBtn) svgBtn.addEventListener("click", function () { exportImage("svg"); });

    Object.keys(el).forEach(function (k) {
        var node = el[k];
        if (node && (node.tagName === "SELECT" || node.tagName === "INPUT" || node.tagName === "TEXTAREA")) {
            var evt = node.type === "checkbox" || node.tagName === "SELECT" ? "change" : "input";
            node.addEventListener(evt, render);
        }
    });

    // Keep the autosized plot fitted when the viewport changes.
    window.addEventListener("resize", function () {
        if (root.classList.contains("js-plotly-plot")) window.Plotly.Plots.resize(root);
    });

    render();
})();
