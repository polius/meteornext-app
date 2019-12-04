import Vue from 'vue'
import App from './App.vue'
import vuetify from './plugins/vuetify';
import router from './router'
import store from './store'
import Axios from 'axios'

Vue.config.productionTip = false

Vue.prototype.$http = Axios;
Vue.prototype.$http.defaults.baseURL = "http://" + window.location.hostname + ":5000"
Vue.prototype.$http.defaults.headers.common['Content-type'] = "application/json"

const token = localStorage.getItem('token')
if (token) Vue.prototype.$http.defaults.headers.common['Authorization'] = `Bearer ${token}`

new Vue({
  el: '#app',
  vuetify,
  router,
  store,
  components: { App },
  template: '<App/>',
  render: h => h(App)
})