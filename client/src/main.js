import Vue from 'vue'
import App from './App.vue'
import vuetify from './plugins/vuetify';
import router from './router'
import store from './store'
import Axios from 'axios'
import Cookies from 'js-cookie'

Vue.config.productionTip = false

Vue.prototype.$http = Axios
// Vue.prototype.$http.defaults.headers.common['Content-type'] = "application/json"
Vue.prototype.$http.defaults.headers.common['Access-Control-Allow-Origin'] = '*'
Vue.prototype.$http.defaults.baseURL = window.location.protocol + "//" + window.location.host + "/api"

// const token = localStorage.getItem('token')
// if (token) Vue.prototype.$http.defaults.headers.common['Authorization'] = `Bearer ${token}`

const token = Cookies.get('csrf_access_token')
if (token) Vue.prototype.$http.defaults.headers.common['X-CSRF-TOKEN'] = token

new Vue({
  el: '#app',
  vuetify,
  router,
  store,
  components: { App },
  template: '<App/>',
  render: h => h(App)
})