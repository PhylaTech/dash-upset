/* dash-upset -- docs-only client-side UpSet renderer.
 *
 * This is a lightweight JavaScript preview of `create_upset`, used by the
 * Component Explorer so every control updates the plot live in the browser.
 * The PYTHON library (dash_upset) is authoritative; this mirrors its display
 * math (subset modes, deviation, sorting, filtering) and Plotly trace/layout
 * construction closely enough for an interactive preview. The hard part --
 * parsing raw data into the canonical exclusive-intersection model -- is done
 * in Python and embedded as `window.DASH_UPSET_DATASETS`, so only the small,
 * stable display layer lives here.
 *
 * Keep in sync with dash_upset/figure.py and dash_upset/data.py.
 */
(function (global) {
    "use strict";

    var INK = "#0b0b0b";
    var SECONDARY = "#52514e";
    var MUTED = "#898781";
    var INACTIVE = "#d8d7d1";
    var GRID = "#e1e0d9";
    var BASELINE = "#c3c2b7";
    var BAND = "rgba(11,11,11,0.04)";

    function comboKey(sets) {
        return sets.slice().sort().join("");
    }
    function labelOf(sets) {
        return sets.length ? sets.join(" & ") : "(no sets)";
    }
    function percent(part, total) {
        return total > 0 ? ((100 * part) / total).toFixed(1) : "0.0";
    }
    function isSubset(a, b) {
        // every element of a is in b
        for (var i = 0; i < a.length; i++) if (b.indexOf(a[i]) === -1) return false;
        return true;
    }
    function overlaps(a, b) {
        for (var i = 0; i < a.length; i++) if (b.indexOf(a[i]) !== -1) return true;
        return false;
    }

    // deviation() / deviations(): observed minus expected-under-independence.
    function deviations(model) {
        var map = {};
        var total = model.total;
        model.intersections.forEach(function (entry) {
            if (total <= 0) {
                map[comboKey(entry.sets)] = 0;
                return;
            }
            var observed = entry.size / total;
            var expected = 1.0;
            model.setNames.forEach(function (name, i) {
                var p = model.setSizes[i] / total;
                expected *= entry.sets.indexOf(name) !== -1 ? p : 1 - p;
            });
            map[comboKey(entry.sets)] = observed - expected;
        });
        return map;
    }

    // subset_sizes(data, mode)
    function subsetSizes(model, mode) {
        if (mode === "distinct") {
            return model.intersections.map(function (e) {
                return { sets: e.sets, size: e.size };
            });
        }
        var excl = model.intersections;
        return excl.map(function (entry) {
            if (!entry.sets.length) return { sets: entry.sets, size: entry.size };
            var size = 0;
            excl.forEach(function (other) {
                if (!other.sets.length) return;
                var hit =
                    mode === "intersect"
                        ? isSubset(entry.sets, other.sets)
                        : overlaps(entry.sets, other.sets);
                if (hit) size += other.size;
            });
            return { sets: entry.sets, size: size };
        });
    }

    // filter_subsets(...)
    function filterSubsets(subsets, opts) {
        var result = subsets.slice();
        if (opts.minSize != null) result = result.filter(function (e) { return e.size >= opts.minSize; });
        if (opts.maxSize != null) result = result.filter(function (e) { return e.size <= opts.maxSize; });
        if (opts.minDegree != null) result = result.filter(function (e) { return e.sets.length >= opts.minDegree; });
        if (opts.maxDegree != null) result = result.filter(function (e) { return e.sets.length <= opts.maxDegree; });
        if (opts.maxSubsets != null && result.length > opts.maxSubsets) {
            var sizes = result.map(function (e) { return e.size; }).sort(function (a, b) { return b - a; });
            var cutoff = sizes[opts.maxSubsets - 1];
            result = result.filter(function (e) { return e.size >= cutoff; });
        }
        return result;
    }

    // sort_intersections(...)
    function sortIntersections(subsets, setNames, sortBy, devMap) {
        var reverse = sortBy.charAt(0) === "-";
        var key = reverse ? sortBy.slice(1) : sortBy;
        var index = {};
        setNames.forEach(function (n, i) { index[n] = i; });
        function ck(e) { return e.sets.map(function (n) { return index[n]; }).sort(function (a, b) { return a - b; }); }
        function cmpArr(a, b) {
            for (var i = 0; i < Math.min(a.length, b.length); i++) if (a[i] !== b[i]) return a[i] - b[i];
            return a.length - b.length;
        }
        var out = subsets.slice();
        if (key === "cardinality") {
            out.sort(function (a, b) { return b.size - a.size || a.sets.length - b.sets.length || cmpArr(ck(a), ck(b)); });
        } else if (key === "degree") {
            out.sort(function (a, b) { return a.sets.length - b.sets.length || b.size - a.size || cmpArr(ck(a), ck(b)); });
        } else if (key === "deviation") {
            out.sort(function (a, b) {
                return (devMap[comboKey(b.sets)] - devMap[comboKey(a.sets)]) || a.sets.length - b.sets.length || cmpArr(ck(a), ck(b));
            });
        }
        if (reverse) out.reverse();
        return out;
    }

    // sort_sets(...)
    function sortSets(setNames, setSizes, sortBy) {
        var reverse = sortBy.charAt(0) === "-";
        var key = reverse ? sortBy.slice(1) : sortBy;
        var pairs = setNames.map(function (n, i) { return [n, setSizes[i]]; });
        if (key === "cardinality") pairs.sort(function (a, b) { return b[1] - a[1]; });
        else if (key === "name") pairs.sort(function (a, b) { return a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0; });
        var names = pairs.map(function (p) { return p[0]; });
        if (reverse) names.reverse();
        return names;
    }

    function buildFigure(model, options) {
        var opts = options || {};
        var mode = opts.mode || "distinct";
        var showEmpty = !!opts.showEmpty;
        var showCounts = opts.showCounts !== false;

        var moded = subsetSizes(model, mode).filter(function (e) {
            return showEmpty || e.sets.length > 0;
        });
        moded = filterSubsets(moded, opts);
        if (!moded.length) return null;

        var setOrder = sortSets(model.setNames, model.setSizes, opts.sortSetsBy || "cardinality");
        var devMap = deviations(model);
        var subsets = sortIntersections(moded, setOrder, opts.sortBy || "cardinality", devMap);

        var sizeOfSet = {};
        model.setNames.forEach(function (n, i) { sizeOfSet[n] = model.setSizes[i]; });
        var rowOfSet = {};
        setOrder.forEach(function (n, r) { rowOfSet[n] = r; });
        var nSets = setOrder.length;
        var nInt = subsets.length;
        var total = model.total;

        var labels = subsets.map(function (e) { return labelOf(e.sets); });
        var sizes = subsets.map(function (e) { return e.size; });
        var maxSize = Math.max.apply(null, sizes);

        var dotPx = 13;
        var modeTitle = mode === "union" ? "Union size" : mode === "intersect" ? "Intersection size (intersect)" : "Intersection size";

        var traces = [];

        // Intersection-size bars (top right)
        traces.push({
            type: "bar",
            x: subsets.map(function (_, i) { return i; }),
            y: sizes,
            width: 0.6,
            marker: { color: INK, cornerradius: 4, line: { width: 0 } },
            customdata: subsets.map(function (e) {
                return [labelOf(e.sets), e.sets.length, percent(e.size, total), (100 * devMap[comboKey(e.sets)] >= 0 ? "+" : "") + (100 * devMap[comboKey(e.sets)]).toFixed(1)];
            }),
            hovertemplate: "<b>%{customdata[0]}</b><br>Size: %{y:,} (%{customdata[2]}% of total)<br>Degree: %{customdata[1]}<br>Deviation: %{customdata[3]}%<extra></extra>",
            text: showCounts ? sizes.map(function (s) { return s.toLocaleString(); }) : null,
            textposition: "outside",
            textfont: { size: 11, color: SECONDARY },
            cliponaxis: false,
            xaxis: "x",
            yaxis: "y",
        });

        // Set-size bars (bottom left, growing leftward)
        traces.push({
            type: "bar",
            orientation: "h",
            y: setOrder.map(function (_, r) { return r; }),
            x: setOrder.map(function (n) { return sizeOfSet[n]; }),
            width: 0.6,
            marker: { color: INK, cornerradius: 4, line: { width: 0 } },
            customdata: setOrder.map(function (n) { return [n, percent(sizeOfSet[n], total)]; }),
            hovertemplate: "<b>%{customdata[0]}</b><br>Size: %{x:,} (%{customdata[1]}% of total)<extra></extra>",
            xaxis: "x2",
            yaxis: "y2",
        });

        // Matrix background dots (every set x every intersection)
        var bgX = [], bgY = [];
        for (var c = 0; c < nInt; c++) for (var r = 0; r < nSets; r++) { bgX.push(c); bgY.push(r); }
        traces.push({
            type: "scatter", mode: "markers", x: bgX, y: bgY,
            marker: { color: INACTIVE, size: dotPx }, hoverinfo: "skip",
            xaxis: "x3", yaxis: "y3",
        });

        // Connector lines for multi-set intersections
        var connX = [], connY = [];
        subsets.forEach(function (e, c) {
            if (e.sets.length < 2) return;
            var rows = e.sets.map(function (n) { return rowOfSet[n]; });
            connX.push(c, c, null);
            connY.push(Math.min.apply(null, rows), Math.max.apply(null, rows), null);
        });
        if (connX.length) {
            traces.push({
                type: "scatter", mode: "lines", x: connX, y: connY,
                line: { color: INK, width: 2.5 }, hoverinfo: "skip",
                xaxis: "x3", yaxis: "y3",
            });
        }

        // Active member dots
        var dotX = [], dotY = [], dotCd = [];
        subsets.forEach(function (e, c) {
            e.sets.forEach(function (n) {
                dotX.push(c); dotY.push(rowOfSet[n]);
                dotCd.push([n, labelOf(e.sets) + " (" + e.size.toLocaleString() + ")"]);
            });
        });
        if (dotX.length) {
            traces.push({
                type: "scatter", mode: "markers", x: dotX, y: dotY, customdata: dotCd,
                marker: { color: INK, size: dotPx },
                hovertemplate: "<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>",
                xaxis: "x3", yaxis: "y3",
            });
        }

        var colRange = [-0.5, nInt - 0.5];
        var rowRange = [nSets - 0.5, -0.5];
        var headroom = showCounts ? 1.18 : 1.05;
        var shapes = [];
        for (var rr = 0; rr < nSets; rr += 2) {
            shapes.push({
                type: "rect", xref: "x3 domain", yref: "y3", x0: 0, x1: 1,
                y0: rr - 0.5, y1: rr + 0.5, fillcolor: BAND, line: { width: 0 }, layer: "below",
            });
        }

        var longestName = setOrder.reduce(function (m, n) { return Math.max(m, n.length); }, 0);
        var leftMargin = Math.max(56, longestName * 7 + 18);

        var layout = {
            showlegend: false,
            height: opts.height || 460,
            margin: { l: leftMargin, r: 16, t: 16, b: 12 },
            font: { size: 12, color: SECONDARY },
            paper_bgcolor: "white",
            plot_bgcolor: "white",
            hoverlabel: { font: { size: 12 } },
            bargap: 0.3,
            shapes: shapes,
            xaxis: { domain: [0.26, 1], anchor: "y", range: colRange, showticklabels: false, ticks: "", showgrid: false, zeroline: false },
            yaxis: { domain: [0.63, 1], anchor: "x", range: [0, maxSize > 0 ? maxSize * headroom : 1], title: { text: modeTitle, font: { size: 12, color: SECONDARY } }, tickfont: { size: 11, color: MUTED }, gridcolor: GRID, zeroline: true, zerolinecolor: BASELINE, nticks: 5 },
            xaxis2: { domain: [0, 0.23], anchor: "y2", autorange: "reversed", title: { text: "Set size", font: { size: 12, color: SECONDARY } }, tickfont: { size: 11, color: MUTED }, gridcolor: GRID, zeroline: false, nticks: 3 },
            yaxis2: { domain: [0, 0.57], anchor: "x2", range: rowRange, tickvals: setOrder.map(function (_, r) { return r; }), ticktext: setOrder, tickfont: { size: 12, color: SECONDARY }, ticks: "", showgrid: false, zeroline: false },
            xaxis3: { domain: [0.26, 1], anchor: "y3", matches: "x", range: colRange, showticklabels: false, ticks: "", showgrid: false, zeroline: false },
            yaxis3: { domain: [0, 0.57], anchor: "x3", matches: "y2", range: rowRange, showticklabels: false, ticks: "", showgrid: false, zeroline: false },
        };

        return { data: traces, layout: layout, config: { responsive: true, displayModeBar: false } };
    }

    global.DashUpset = { buildFigure: buildFigure };
})(window);
