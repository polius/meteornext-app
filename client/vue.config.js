const fs = require('fs')

module.exports = {
  productionSourceMap: false,
  devServer: {
    disableHostCheck: true
  }
}

/*
module.exports = {
    devServer: {
        https: {
          key: fs.readFileSync('./certs/example.com+5-key.pem'),
          cert: fs.readFileSync('./certs/example.com+5.pem'),
        },
        public: 'https://localhost:8080/'
    }
}
*/