var webpack = require('webpack');
var path = require('path');
var pwd = path.resolve(__dirname);

//
// Handling and defining environments
//

// a list of environments which are considered 'production'
// for the purpose of building the JS bundle
var PROD_ENVIRONMENTS = ['beta', 'staging', 'tr_staging', 'tr_prod'];

var ENV = process.env.REACT_ENV || 'local'; // REACT_ENV is set inside fabfile

var IS_PROD = PROD_ENVIRONMENTS.indexOf(ENV) >= 0;
var NODE_ENV = IS_PROD ? 'production' : 'development';

// whether or not we should do the hot load configuration
var HOT_LOAD = JSON.parse(process.env.HOT_LOAD || 'false');
if (HOT_LOAD) {
  console.warn(
    "WARNING: Hot module replacement will be enabled. " +
    "This should ONLY be used for local development.\n"
  );
}

//
// Configuring webpack plugins
//
//

var plugins = [];

//
// default plugins
//
plugins.push(
  // define some global constants that are injected in compile-time
  new webpack.DefinePlugin({
    '__ENV__': JSON.stringify(ENV),
    'process.env': {
      'NODE_ENV': JSON.stringify(NODE_ENV)
    }
  })
);

plugins.push(
  // to ignore dynamic require for moment.js locales
  // see https://github.com/webpack/webpack/issues/198#issuecomment-50233174
  new webpack.IgnorePlugin(/^\.\/locale$/, /moment$/)
);

//
// conditional on environment plugins
//

if (IS_PROD) {
  plugins.push(new webpack.optimize.UglifyJsPlugin());
  plugins.push(new webpack.optimize.DedupePlugin());
  plugins.push(new webpack.optimize.OccurenceOrderPlugin());
}

if (HOT_LOAD) {
  plugins.push(new webpack.HotModuleReplacementPlugin());
  plugins.push(new webpack.NoErrorsPlugin());
  plugins.push(new webpack.ProgressPlugin(function(percentage, message) {
    process.stdout.write('.');
    if (percentage === 1) {
      process.stdout.write('\n\n');
    }
  }));
}


//
// Entry points (conditionally hot reloaded)
//
//

var baseEntry = {
  'header': './common/Main.jsx',
  'report': './report/Main.jsx',
  // 'report_mobile': './report_mobile/Main.jsx',
  'account': './account/Main.jsx',
  'upload': './upload/Main.jsx',
  'getstarted': './getstarted/Main.jsx',
  'summary': './summary/Main.jsx',
}

var hotLoadEntry = {};
// converts each entry point to an array ['entryPoint', 'webpack/hot...']
Object.keys(baseEntry).forEach(function(key) {
  var entryPoint = baseEntry[key];
  hotLoadEntry[key] = ['webpack-dev-server/client?http://0.0.0.0:3000', 'webpack/hot/only-dev-server', entryPoint];
});

var entry = HOT_LOAD ? hotLoadEntry : baseEntry;

//
// Preloaders
//
//

var preLoaders = [];

if (/*ENV === 'local'*/ true) { // we are not ready for ESLint
  preLoaders.push({
    test: /\.(js|jsx)$/,
    loader: 'eslint-loader',
    include: [
      // path.resolve(__dirname, 'common/'),
      path.resolve(__dirname, 'account/'),
      path.resolve(__dirname, 'upload/'),
      path.resolve(__dirname, 'common/'),

      // path.resolve(__dirname, 'report/')
      path.resolve(__dirname, 'report/Main.jsx'),
      path.resolve(__dirname, 'report/components/'),
      path.resolve(__dirname, 'report/redux/')
    ]
  });
}

//
// Loaders
//
//

var loaders = [
  { test: /\.css$/, loader:
    'style!' + (IS_PROD ? 'css' : 'css?localIdentName=[name]--[local]--[hash:base64:5]') + '!autoprefixer'
  },
  {
    test: /\.(js|jsx)$/,
    exclude: /node_modules/,
    loader: 'babel'
  },
  {
    test: /\.scss$/,
    loader: 'style!css!autoprefixer!sass'
  },
  {
    test: /\.json$/,
    use: 'json-loader'
  }
];

if (HOT_LOAD) {
  loaders.forEach(function(loaderConfig) {
    // prepend each loader string with 'react-hot!'
    loaderConfig.loader = 'react-hot-loader/webpack!' + loaderConfig.loader;
  });
}


//
// The actual webpack config object follows
//
//

module.exports = {
  entry: entry,
  devtool: IS_PROD ? 'cheap-source-map' : 'eval',
  output: {
    path: pwd + '/build',
    filename: '[name].entry.js',
    publicPath: HOT_LOAD ? 'http://0.0.0.0:3000/static/react/build' : undefined,
  },
  module: {
    preLoaders: preLoaders,
    loaders: loaders,
  },
  resolve: {
    alias: {
      utils: pwd + '/utils',
      common: pwd + '/common',
      report: pwd + '/report',
      // report_mobile: pwd + '/report_mobile',
      account: pwd + '/account',
      getstarted: pwd + '/getstarted'
    },
    extensions: ['', '.js', '.jsx', '.json']
  },
  plugins: plugins,
  externals: [{
    xmlhttprequest: '{XMLHttpRequest:XMLHttpRequest}'
  }]
};
