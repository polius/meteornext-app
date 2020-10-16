module.exports = {
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
  }
}