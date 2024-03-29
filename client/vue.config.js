// const BundleAnalyzerPlugin = require('webpack-bundle-analyzer').BundleAnalyzerPlugin;
const CompressionWebpackPlugin = require('compression-webpack-plugin')

module.exports = {
  // configureWebpack: {
  //   plugins: [new BundleAnalyzerPlugin({ analyzerHost: '10.0.0.229'})]
  // },
  runtimeCompiler: true,
  productionSourceMap: false,
  devServer: {
    disableHostCheck: true,
    headers: { 'Access-Control-Allow-Origin': '*' }
  },
  css: {
    loaderOptions: {
      sass: {
        additionalData: `@import "@/styles/variables.scss"`,
      }
    }
  },
  configureWebpack: {
    plugins: [
      new CompressionWebpackPlugin() // Remove "{ cache: false }" for Production
    ]
  }
}