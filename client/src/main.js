import Vue from 'vue'
import App from './App.vue'
import vuetify from './plugins/vuetify';
import router from './router'
import store from './store'
import Axios from 'axios'
import settings from './settings.json'

Vue.config.productionTip = false

Vue.prototype.$http = Axios;
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

// Load IP from 'settings.json'
store.dispatch('init', { settings })