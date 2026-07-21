/* dash-upset -- docs-only client-side UpSet renderer.
 *
 * This is a lightweight JavaScript preview of `create_upset`, used by the
 * Component Explorer so every control updates the plot live in the browser.
 * The PYTHON library (dash_upset) is authoritative; this mirrors its display
 * math (subset modes, deviation, sorting, filtering), the theme system, and
 * Plotly trace/layout construction closely enough for an interactive preview.
 * The hard part -- parsing raw data into the canonical exclusive-intersection
 * model -- is done in Python and embedded as `window.DASH_UPSET_DATASETS`.
 *
 * Keep in sync with dash_upset/figure.py and dash_upset/data.py.
 */
(function (global) {
    "use strict";

    // Theme chrome + CVD-safe colorways -- mirror of figure.py's _LIGHT /
    // _DARK / _PALETTES / _resolve_theme.
    var LIGHT = {
        ink: "#0b0b0b", paper: "#ffffff", secondary: "#52514e", muted: "#898781",
        inactive: "#d8d7d1", grid: "#e1e0d9", baseline: "#c3c2b7", band: "rgba(11,11,11,0.04)",
    };
    var DARK = {
        ink: "#e8e6e1", paper: "#1a1a19", secondary: "#c3c2b7", muted: "#8f8d86",
        inactive: "#3d3d3a", grid: "#2c2c2a", baseline: "#45443e", band: "rgba(255,255,255,0.05)",
    };
    var OKABE_ITO = ["#E69F00", "#56B4E9", "#009E73", "#F0E442", "#0072B2", "#D55E00", "#CC79A7"];
    var PALETTES = {
        "okabe-ito": [OKABE_ITO, OKABE_ITO],
        colorbrewer: [
            ["#66C2A5", "#FC8D62", "#8DA0CB", "#E78AC3", "#A6D854", "#FFD92F", "#E5C494"],
            ["#1B9E77", "#D95F02", "#7570B3", "#E7298A", "#66A61E", "#E6AB02", "#A6761D"],
        ],
        tol: [
            ["#4477AA", "#EE6677", "#228833", "#CCBB44", "#66CCEE", "#AA3377", "#BBBBBB"],
            ["#4477AA", "#EE6677", "#228833", "#CCBB44", "#66CCEE", "#AA3377", "#BBBBBB"],
        ],
    };

    function assign(base, extra) {
        var out = {};
        for (var k in base) if (base.hasOwnProperty(k)) out[k] = base[k];
        for (var j in extra) if (extra.hasOwnProperty(j)) out[j] = extra[j];
        return out;
    }

    // resolve_theme(name) -> chrome dict + colorway. "auto" resolves to light
    // in this static preview (the Dash component makes it live).
    function resolveTheme(theme) {
        var name = theme === "auto" || !theme ? "light" : theme;
        var palettes = Object.keys(PALETTES);
        for (var i = 0; i < palettes.length; i++) {
            var p = palettes[i];
            var cw = PALETTES[p];
            if (name === p || name === p + "-light") return assign(LIGHT, { colorway: cw[0] });
            if (name === p + "-dark") return assign(DARK, { colorway: cw[1] });
        }
        if (name === "light") return assign(LIGHT, { colorway: null });
        if (name === "dark") return assign(DARK, { colorway: null });
        return assign(LIGHT, { colorway: null }); // unknown -> light (Python raises)
    }

    function comboKey(sets) {
        return sets.slice().sort().join("");
    }
    function labelOf(sets) {
        return sets.length ? sets.join(" & ") : "(no sets)";
    }
    function percent(part, total) {
        return total > 0 ? ((100 * part) / total).toFixed(1) : "0.0";
    }
    function isSubset(a, b) {
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
        var showPct = !!opts.showPercentages;

        var th = resolveTheme(opts.theme);
        var ink = opts.color || th.ink;
        var inactive = opts.inactiveColor || th.inactive;

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

        // Per-set colors: a palette colorway colors each set (its bar + dots);
        // plain light/dark stays ink. Explicit color= wins. Mirror of figure.py.
        var colorway = th.colorway;
        var setColors = setOrder.map(function (_, i) {
            return (!opts.color && colorway) ? colorway[i % colorway.length] : ink;
        });
        var nSets = setOrder.length;
        var nInt = subsets.length;
        var total = model.total;

        var sizes = subsets.map(function (e) { return e.size; });
        var maxSize = Math.max.apply(null, sizes);

        var dotPx = 13;
        var modeTitle = mode === "union" ? "Union size" : mode === "intersect" ? "Intersection size (intersect)" : "Intersection size";

        // Bar labels: mirror figure.py's texttemplate choice.
        var barText = null;
        if (showCounts && showPct) barText = "%{y:,} (%{customdata[2]}%)";
        else if (showCounts) barText = "%{y:,}";
        else if (showPct) barText = "%{customdata[2]}%";

        var traces = [];

        // Intersection-size bars (top right)
        traces.push({
            type: "bar", meta: "upset:intersection-bars",
            x: subsets.map(function (_, i) { return i; }),
            y: sizes,
            width: 0.6,
            marker: { color: ink, cornerradius: 4, line: { width: 0 } },
            customdata: subsets.map(function (e) {
                var dev = 100 * devMap[comboKey(e.sets)];
                return [labelOf(e.sets), e.sets.length, percent(e.size, total), (dev >= 0 ? "+" : "") + dev.toFixed(1)];
            }),
            hovertemplate: "<b>%{customdata[0]}</b><br>Size: %{y:,} (%{customdata[2]}% of total)<br>Degree: %{customdata[1]}<br>Deviation: %{customdata[3]}%<extra></extra>",
            texttemplate: barText,
            textposition: "outside",
            textfont: { size: 11, color: th.secondary },
            cliponaxis: false,
            xaxis: "x", yaxis: "y",
        });

        // Set-size bars (bottom left, growing leftward)
        traces.push({
            type: "bar", meta: "upset:set-bars",
            orientation: "h",
            y: setOrder.map(function (_, r) { return r; }),
            x: setOrder.map(function (n) { return sizeOfSet[n]; }),
            width: 0.6,
            marker: { color: setColors, cornerradius: 4, line: { width: 0 } },
            customdata: setOrder.map(function (n) { return [n, percent(sizeOfSet[n], total)]; }),
            hovertemplate: "<b>%{customdata[0]}</b><br>Size: %{x:,} (%{customdata[1]}% of total)<extra></extra>",
            xaxis: "x2", yaxis: "y2",
        });

        // Matrix background dots (every set x every intersection)
        var bgX = [], bgY = [];
        for (var c = 0; c < nInt; c++) for (var r = 0; r < nSets; r++) { bgX.push(c); bgY.push(r); }
        traces.push({
            type: "scatter", mode: "markers", meta: "upset:matrix-background", x: bgX, y: bgY,
            marker: { color: inactive, size: dotPx }, hoverinfo: "skip",
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
                type: "scatter", mode: "lines", meta: "upset:matrix-connectors", x: connX, y: connY,
                line: { color: ink, width: 2.5 }, hoverinfo: "skip",
                xaxis: "x3", yaxis: "y3",
            });
        }

        // Active member dots (each colored by its set)
        var dotX = [], dotY = [], dotCd = [], dotColors = [];
        subsets.forEach(function (e, c) {
            e.sets.forEach(function (n) {
                dotX.push(c); dotY.push(rowOfSet[n]);
                dotColors.push(setColors[rowOfSet[n]]);
                dotCd.push([n, labelOf(e.sets) + " (" + e.size.toLocaleString() + ")"]);
            });
        });
        if (dotX.length) {
            traces.push({
                type: "scatter", mode: "markers", meta: "upset:matrix-dots", x: dotX, y: dotY, customdata: dotCd,
                marker: { color: dotColors, size: dotPx },
                hovertemplate: "<b>%{customdata[0]}</b><br>%{customdata[1]}<extra></extra>",
                xaxis: "x3", yaxis: "y3",
            });
        }

        var colRange = [-0.5, nInt - 0.5];
        var rowRange = [nSets - 0.5, -0.5];
        var headroom = showCounts || showPct ? 1.18 : 1.05;
        var shapes = [];
        for (var rr = 0; rr < nSets; rr += 2) {
            shapes.push({
                type: "rect", xref: "x3 domain", yref: "y3", x0: 0, x1: 1,
                y0: rr - 0.5, y1: rr + 0.5, fillcolor: th.band, line: { width: 0 }, layer: "below",
            });
        }

        // Axis titles: undefined -> automatic; a string overrides; null/"" hides.
        var intersectionTitle = opts.intersectionTitle === undefined ? modeTitle : opts.intersectionTitle;
        var setSizeTitle = opts.setSizeTitle === undefined ? "Set size" : opts.setSizeTitle;
        var showIntTicks = opts.showIntersectionTicks !== false;
        var showSetTicks = opts.showSetSizeTicks !== false;
        var titleFont = { size: 12, color: th.secondary };

        var hasTitle = !!opts.title;
        var layout = {
            showlegend: false,
            margin: { l: 12, r: 16, t: hasTitle ? 52 : 16, b: 12 },
            font: { size: 12, color: th.secondary },
            paper_bgcolor: th.paper,
            plot_bgcolor: th.paper,
            colorway: th.colorway || undefined,
            hoverlabel: { font: { size: 12 } },
            bargap: 0.3,
            shapes: shapes,
            xaxis: { domain: [0.26, 1], anchor: "y", range: colRange, showticklabels: false, ticks: "", showgrid: false, zeroline: false },
            yaxis: { domain: [0.63, 1], anchor: "x", range: [0, maxSize > 0 ? maxSize * headroom : 1], title: intersectionTitle ? { text: intersectionTitle, font: titleFont, standoff: 8 } : undefined, showticklabels: showIntTicks, tickfont: { size: 11, color: th.muted }, gridcolor: th.grid, zeroline: true, zerolinecolor: th.baseline, nticks: 5, automargin: true },
            xaxis2: { domain: [0, 0.23], anchor: "y2", autorange: "reversed", title: setSizeTitle ? { text: setSizeTitle, font: titleFont, standoff: 8 } : undefined, showticklabels: showSetTicks, tickfont: { size: 11, color: th.muted }, gridcolor: th.grid, zeroline: false, nticks: 3, automargin: true },
            yaxis2: { domain: [0, 0.57], anchor: "x2", range: rowRange, tickvals: setOrder.map(function (_, r) { return r; }), ticktext: setOrder, tickfont: { size: 12, color: th.secondary }, ticks: "", showgrid: false, zeroline: false, automargin: true },
            xaxis3: { domain: [0.26, 1], anchor: "y3", matches: "x", range: colRange, showticklabels: false, ticks: "", showgrid: false, zeroline: false },
            yaxis3: { domain: [0, 0.57], anchor: "x3", matches: "y2", range: rowRange, showticklabels: false, ticks: "", showgrid: false, zeroline: false },
        };
        if (hasTitle) {
            layout.title = { text: opts.title, x: 0, xref: "paper", xanchor: "left", font: { size: 15, color: th.ink } };
        }
        // A fixed height is optional: without it the plot autosizes to its
        // container (the explorer's viewport-locked canvas).
        if (opts.height) layout.height = opts.height;

        // Accessibility: a screen-reader description, auto-generated when the
        // caller doesn't supply one (mirror of figure.py). Stored on the figure
        // so the component/explorer can apply it as an aria-label.
        var description = opts.description;
        if (!description) {
            var bIdx = 0;
            for (var k = 1; k < sizes.length; k++) if (sizes[k] > sizes[bIdx]) bIdx = k;
            var bLabel = subsets.length ? labelOf(subsets[bIdx].sets) : "";
            description = "UpSet plot of " + nSets + " sets (" + setOrder.join(", ") +
                ") across " + nInt + " intersections. The largest shown intersection is " +
                bLabel + " with " + (sizes[bIdx] || 0).toLocaleString() + " elements.";
        }
        layout.meta = { description: description };

        return { data: traces, layout: layout, config: { responsive: true, displayModeBar: false } };
    }

    // Map a plotly click event to the component's selection properties, exactly
    // as the compiled DashUpset React component does (keyed on trace meta).
    // Also returns `target` (which marks to highlight) for applyHighlight.
    function selectionFromClick(point) {
        if (!point) return null;
        var meta = point.data && point.data.meta;
        var cd = point.customdata || [];
        function setsFromLabel(label) {
            return label && label !== "(no sets)" ? label.split(" & ") : [];
        }
        if (meta === "upset:intersection-bars") {
            var label = cd.length ? cd[0] : null;
            return {
                prop: "selected_intersection",
                value: { label: label, sets: setsFromLabel(label), size: point.y },
                target: { type: "intersection", column: point.pointNumber },
            };
        }
        if (meta === "upset:matrix-dots") {
            var raw = cd.length > 1 ? cd[1] : null;
            var cut = typeof raw === "string" ? raw.lastIndexOf(" (") : -1;
            var lbl = cut >= 0 ? raw.slice(0, cut) : raw;
            return {
                prop: "selected_intersection",
                value: { label: lbl, sets: setsFromLabel(lbl) },
                target: { type: "intersection", column: point.x },
            };
        }
        if (meta === "upset:set-bars") {
            var name = cd.length ? cd[0] : null;
            return name
                ? { prop: "selected_sets", value: [name], target: { type: "sets", row: point.pointNumber } }
                : null;
        }
        return null;
    }

    // Recolor the selected marks over base colors (a {meta: colorOrArray} map
    // captured at render). Mirrors the compiled component's highlight.
    function applyHighlight(gd, baseColors, target, color) {
        if (!gd || !gd.data || !global.Plotly) return;
        function idx(meta) { return gd.data.findIndex(function (t) { return t.meta === meta; }); }
        function arr(c, n) {
            if (Array.isArray(c)) return c.slice();
            var out = []; for (var i = 0; i < n; i++) out.push(c); return out;
        }
        var bi = idx("upset:intersection-bars");
        if (bi >= 0) {
            var c1 = arr(baseColors["upset:intersection-bars"], gd.data[bi].y.length);
            if (target && target.type === "intersection" && target.column != null) c1[target.column] = color;
            global.Plotly.restyle(gd, { "marker.color": [c1] }, [bi]);
        }
        var si = idx("upset:set-bars");
        if (si >= 0) {
            var c2 = arr(baseColors["upset:set-bars"], gd.data[si].y.length);
            if (target && target.type === "sets" && target.row != null) c2[target.row] = color;
            global.Plotly.restyle(gd, { "marker.color": [c2] }, [si]);
        }
        var di = idx("upset:matrix-dots");
        if (di >= 0) {
            var xs = gd.data[di].x, ys = gd.data[di].y;
            var c3 = arr(baseColors["upset:matrix-dots"], xs.length);
            for (var i = 0; i < xs.length; i++) {
                var hitCol = target && target.type === "intersection" && xs[i] === target.column;
                var hitRow = target && target.type === "sets" && ys[i] === target.row;
                if (hitCol || hitRow) c3[i] = color;
            }
            global.Plotly.restyle(gd, { "marker.color": [c3] }, [di]);
        }
    }

    // Snapshot the base marker colors for the highlightable traces.
    function baseColorsOf(figure) {
        var map = {};
        (figure.data || []).forEach(function (t) {
            if (t.meta === "upset:intersection-bars" || t.meta === "upset:set-bars" || t.meta === "upset:matrix-dots") {
                var c = t.marker && t.marker.color;
                map[t.meta] = Array.isArray(c) ? c.slice() : c;
            }
        });
        return map;
    }

    global.DashUpset = {
        buildFigure: buildFigure,
        selectionFromClick: selectionFromClick,
        applyHighlight: applyHighlight,
        baseColorsOf: baseColorsOf,
    };
})(window);
