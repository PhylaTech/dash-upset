const path = require('path');
const TerserPlugin = require('terser-webpack-plugin');
const { LicenseWebpackPlugin } = require('license-webpack-plugin');
const packagejson = require('./package.json');

const dashLibraryName = packagejson.name.replace(/-/g, '_');

module.exports = (env, argv) => {
    const mode = (argv && argv.mode) || 'production';
    const modeSuffix = mode === 'development' ? 'dev' : 'min';
    const filename = `${dashLibraryName}.${modeSuffix}.js`;

    return {
        mode,
        entry: { main: './src/lib/index.js' },
        output: {
            path: path.resolve(__dirname, dashLibraryName),
            filename,
            library: dashLibraryName,
            libraryTarget: 'window',
        },
        devtool: 'source-map',
        optimization: {
            // Terser's default extractComments emits a *.LICENSE.txt holding
            // only the few deps that kept a @license banner through
            // minification (misleadingly partial). Disable it; the complete,
            // accurate third-party notice comes from LicenseWebpackPlugin,
            // which walks the module graph and lists every bundled package.
            minimizer: [new TerserPlugin({ extractComments: false })],
        },
        plugins: [
            new LicenseWebpackPlugin({
                perChunkOutput: false,
                outputFilename: 'THIRD_PARTY_LICENSES.txt',
                // react / react-dom / prop-types are externals (provided by
                // Dash), so they never enter the graph and aren't listed.
            }),
        ],
        // react / react-dom / prop-types are provided by Dash on the page;
        // plotly.js is bundled (a trimmed core + bar + scatter build) so the
        // component renders without depending on a dcc.Graph being present.
        externals: {
            react: 'React',
            'react-dom': 'ReactDOM',
            'prop-types': 'PropTypes',
        },
        module: {
            rules: [
                {
                    test: /\.jsx?$/,
                    exclude: /node_modules/,
                    use: { loader: 'babel-loader' },
                },
                {
                    // plotly.js's core pulls in a stylesheet (maplibre); inline
                    // it at runtime rather than emitting a separate asset.
                    test: /\.css$/,
                    use: ['style-loader', 'css-loader'],
                },
            ],
        },
    };
};
