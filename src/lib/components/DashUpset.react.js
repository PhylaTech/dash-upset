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

/**
 * DashUpset renders an UpSet figure (built in Python by create_upset) with
 * plotly.js and turns clicks into two declared, callback-addressable props:
 * selected_intersection and selected_sets. It is the compiled component behind
 * dash_upset.UpSet; application code should construct it through UpSet(...),
 * which builds the figure for you.
 *
 * The clicked trace is identified by its stable meta id:
 * "upset:intersection-bars" and "upset:matrix-dots" update selected_intersection;
 * "upset:set-bars" updates selected_sets. Clicks elsewhere are ignored.
 */
const DashUpset = (props) => {
    const {id, figure, config, style, className, setProps} = props;

    const handleClick = (event) => {
        if (!setProps || !event || !event.points || !event.points.length) {
            return;
        }
        const point = event.points[0];
        const trace = point.data || {};
        const meta = trace.meta;
        const customdata = point.customdata || [];

        if (meta === 'upset:intersection-bars') {
            const label = customdata.length ? customdata[0] : null;
            setProps({
                selected_intersection: {
                    label,
                    sets: setsFromLabel(label),
                    size: point.y,
                },
            });
        } else if (meta === 'upset:matrix-dots') {
            const label = customdata.length > 1 ? labelFromDot(customdata[1]) : null;
            setProps({
                selected_intersection: {label, sets: setsFromLabel(label)},
            });
        } else if (meta === 'upset:set-bars') {
            const name = customdata.length ? customdata[0] : null;
            if (name) {
                setProps({selected_sets: [name]});
            }
        }
    };

    return (
        <div id={id} style={style} className={className}>
            <Plot
                data={(figure && figure.data) || []}
                layout={(figure && figure.layout) || {}}
                frames={(figure && figure.frames) || undefined}
                config={config}
                onClick={handleClick}
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
