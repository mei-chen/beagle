var webpack = require('webpack');
var WebpackDevServer = require('webpack-dev-server');
var config = require('./webpack.config');

var host = '0.0.0.0';
var port = 3000;

new WebpackDevServer(webpack(config), {
  publicPath: config.output.publicPath,
  hot: true,
  historyApiFallback: true,
  quiet: false, // don't suppress console.errors
  noInfo: false, // don't suppress build succeeded/failed
  stats: {
    assets: false,
    colors: true,
    chunks: false,
    chunkModules: false
  },
  disableHostCheck: true
}).listen(port, host, function (err, result) {
  if (err) {
    console.log(err);
  }

  console.log('hot load server listening at ' + host + ':' + port);
});
