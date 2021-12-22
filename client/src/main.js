import Vue from 'vue'
import App from './App.vue'
import vuetify from './plugins/vuetify';
import router from './router'
import store from './store'
import Axios from 'axios'
import Cookies from 'js-cookie'

Vue.config.productionTip = false

Vue.prototype.$http = Axios
Vue.prototype.$http.defaults.headers.common['Access-Control-Allow-Origin'] = '*'
// Vue.prototype.$http.defaults.headers.common['Cache-Control'] = 'no-cache'
// Vue.prototype.$http.defaults.headers.common['Pragma'] = 'no-cache'
// Vue.prototype.$http.defaults.headers.common['Expires'] = '0'
Vue.prototype.$http.defaults.baseURL = window.location.protocol + "//" + window.location.host + "/api"

Vue.prototype.$http.interceptors.request.use(
  config => {
    config.headers.common['X-CSRF-TOKEN'] = Cookies.get('csrf_access_token')
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

new Vue({
  el: '#app',
  vuetify,
  router,
  store,
  components: { App },
  template: '<App/>',
  render: h => h(App)
})