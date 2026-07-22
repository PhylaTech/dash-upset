import React from 'react';
import PropTypes from 'prop-types';
import createPlotlyComponent from 'react-plotly.js/factory';
import Plotly from 'plotly.js/lib/core';
import bar from 'plotly.js/lib/bar';
import scatter from 'plotly.js/lib/scatter';

// Trimmed plotly.js bundle: an UpSet figure is only bar traces (the size
// bars) and scatter traces (the dot matrix and connectors), so we register
// just those two trace types instead of shipping the full ~3.5 MB build.
Plotly.register([bar, scatter]);
const Plot = createPlotlyComponent(Plotly);

// Recover the intersection label from a matrix-dot's customdata, whose second
// field looks like "A & B (2)". Mirror of the Python figure's encoding.
function labelFromDot(raw) {
    if (typeof raw !== 'string') {
        return null;
    }
    const cut = raw.lastIndexOf(' (');
    return cut >= 0 ? raw.slice(0, cut) : raw;
}

function setsFromLabel(label) {
    return label && label !== '(no sets)' ? label.split(' & ') : [];
}

function traceIndex(data, meta) {
    return (data || []).findIndex((t) => t.meta === meta);
}

// A trace's marker.color is either a single string or a per-point array;
// normalize to a fresh length-n array we can overwrite at selected indices.
function colorArray(color, n) {
    if (Array.isArray(color)) {
        return color.slice();
    }
    const out = [];
    for (let i = 0; i < n; i += 1) {
        out.push(color);
    }
    return out;
}

/**
 * DashUpset renders an UpSet figure (built in Python by create_upset) with
 * plotly.js and turns clicks into two declared, callback-addressable props:
 * selected_intersection and selected_sets. It is the compiled component behind
 * dash_upset.UpSet; application code should construct it through UpSet(...),
 * which builds the figure for you.
 *
 * The clicked trace is identified by its stable meta id:
 * "upset:intersection-bars" and "upset:matrix-dots" update selected_intersection;
 * "upset:set-bars" updates selected_sets. Clicks elsewhere are ignored. When
 * highlight_selection is on, the clicked column (bar + its member dots) or set
 * (bar + its dots) is recolored to selection_color.
 */
const DashUpset = (props) => {
    const {
        id,
        figure,
        config,
        highlight_selection,
        selection_color,
        style,
        className,
        setProps,
    } = props;

    const gdRef = React.useRef(null);

    // Accessibility: create_upset stashes a screen-reader description on the
    // figure (layout.meta.description); expose it as the graph's aria-label.
    const description =
        (figure && figure.layout && figure.layout.meta && figure.layout.meta.description) || null;

    // Repaint the selected marks over the figure's base colors. Base colors are
    // read from the (immutable) figure prop, never from the graph div, so a
    // prior highlight never leaks into the next one.
    const applyHighlight = React.useCallback(
        (target) => {
            const gd = gdRef.current;
            if (!gd || !figure || !figure.data) {
                return;
            }
            const base = figure.data;

            const barIdx = traceIndex(gd.data, 'upset:intersection-bars');
            if (barIdx >= 0) {
                const n = (gd.data[barIdx].y || []).length;
                const colors = colorArray(base[barIdx] && base[barIdx].marker && base[barIdx].marker.color, n);
                if (target && target.type === 'intersection' && target.column != null) {
                    colors[target.column] = selection_color;
                }
                Plotly.restyle(gd, {'marker.color': [colors]}, [barIdx]);
            }

            const setIdx = traceIndex(gd.data, 'upset:set-bars');
            if (setIdx >= 0) {
                const n = (gd.data[setIdx].y || []).length;
                const colors = colorArray(base[setIdx] && base[setIdx].marker && base[setIdx].marker.color, n);
                if (target && target.type === 'sets' && target.row != null) {
                    colors[target.row] = selection_color;
                }
                Plotly.restyle(gd, {'marker.color': [colors]}, [setIdx]);
            }

            const dotIdx = traceIndex(gd.data, 'upset:matrix-dots');
            if (dotIdx >= 0) {
                const xs = gd.data[dotIdx].x || [];
                const ys = gd.data[dotIdx].y || [];
                const colors = colorArray(base[dotIdx] && base[dotIdx].marker && base[dotIdx].marker.color, xs.length);
                for (let i = 0; i < xs.length; i += 1) {
                    const hitColumn = target && target.type === 'intersection' && xs[i] === target.column;
                    const hitRow = target && target.type === 'sets' && ys[i] === target.row;
                    if (hitColumn || hitRow) {
                        colors[i] = selection_color;
                    }
                }
                Plotly.restyle(gd, {'marker.color': [colors]}, [dotIdx]);
            }
        },
        [figure, selection_color]
    );

    const handleClick = (event) => {
        if (!event || !event.points || !event.points.length) {
            return;
        }
        const point = event.points[0];
        const trace = point.data || {};
        const meta = trace.meta;
        const customdata = point.customdata || [];
        let target = null;

        if (meta === 'upset:intersection-bars') {
            const label = customdata.length ? customdata[0] : null;
            if (setProps) {
                setProps({
                    selected_intersection: {label, sets: setsFromLabel(label), size: point.y},
                });
            }
            target = {type: 'intersection', column: point.pointNumber};
        } else if (meta === 'upset:matrix-dots') {
            const label = customdata.length > 1 ? labelFromDot(customdata[1]) : null;
            if (setProps) {
                setProps({selected_intersection: {label, sets: setsFromLabel(label)}});
            }
            target = {type: 'intersection', column: point.x};
        } else if (meta === 'upset:set-bars') {
            const name = customdata.length ? customdata[0] : null;
            if (name && setProps) {
                setProps({selected_sets: [name]});
            }
            target = name ? {type: 'sets', row: point.pointNumber} : null;
        }

        if (highlight_selection && target) {
            applyHighlight(target);
        }
    };

    return (
        <div
            id={id}
            style={style}
            className={className}
            role={description ? 'img' : undefined}
            aria-label={description || undefined}
        >
            <Plot
                data={(figure && figure.data) || []}
                layout={(figure && figure.layout) || {}}
                frames={(figure && figure.frames) || undefined}
                config={config}
                onClick={handleClick}
                onInitialized={(fig, graphDiv) => {
                    gdRef.current = graphDiv;
                }}
                onUpdate={(fig, graphDiv) => {
                    gdRef.current = graphDiv;
                }}
                useResizeHandler
                style={{width: '100%', height: '100%'}}
            />
        </div>
    );
};

DashUpset.defaultProps = {
    figure: {data: [], layout: {}},
    config: {displayModeBar: false, responsive: true},
    selected_sets: [],
    highlight_selection: true,
    selection_color: '#9c5a3c',
};

DashUpset.propTypes = {
    /**
     * The ID used to identify this component in Dash callbacks.
     */
    id: PropTypes.string,

    /**
     * The Plotly figure to render, as produced by dash_upset.create_upset
     * (a dict with "data" and "layout"). UpSet(...) sets this for you.
     */
    figure: PropTypes.object,

    /**
     * The plotly.js config object for the graph (mode bar, responsiveness, ...).
     */
    config: PropTypes.object,

    /**
     * The currently selected intersection, set when an intersection-size bar or
     * a matrix dot is clicked. An object {label, sets, size} (size is present
     * only for bar clicks); null before any click. Read-only from callbacks.
     */
    selected_intersection: PropTypes.object,

    /**
     * The currently selected set(s), set when a set-size bar is clicked: a list
     * of set names. Read-only from callbacks.
     */
    selected_sets: PropTypes.array,

    /**
     * When true (default), clicking recolors the selected marks (the clicked
     * intersection's bar and member dots, or the clicked set's bar and dots) to
     * selection_color, as a visible selection cue. Set false to leave the plot
     * unchanged on click (selection is still reported to callbacks).
     */
    highlight_selection: PropTypes.bool,

    /**
     * The color applied to the selected marks when highlight_selection is on.
     * Any CSS color string.
     */
    selection_color: PropTypes.string,

    /**
     * CSS styles for the outer container div.
     */
    style: PropTypes.object,

    /**
     * CSS class name for the outer container div.
     */
    className: PropTypes.string,

    /**
     * Dash-assigned callback that reports property changes back to Dash, to
     * make them available to callbacks.
     */
    setProps: PropTypes.func,
};

export default DashUpset;

export const defaultProps = DashUpset.defaultProps;
export const propTypes = DashUpset.propTypes;
