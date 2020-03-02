const fs = require('fs')

module.exports = {
  productionSourceMap: false,
  devServer: {
    disableHostCheck: true
  },
  css: {
    loaderOptions: {
      sass: {
        prependData: `@import "@/styles/variables.scss"`
      }
    }
  }
}