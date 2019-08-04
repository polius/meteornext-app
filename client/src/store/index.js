import Vue from 'vue'
import Vuex from 'vuex'
import axios from 'axios'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    url: '',
    username: '',
    token: localStorage.getItem('token') || '',
    admin: false
  },
  mutations: {
    init(state, data) {
      state.url = 'http://' + data.settings.host + ':' + data.settings.port
    },
    auth(state, data) {
      state.username = data.username
      state.token = data.token
      state.admin = data.admin
    },
    logout(state) {
      state.username = ''
      state.token = ''
      state.admin = false
    }
  },
  actions: {
    init({ commit }, settings) {
      commit('init', settings)
    },
    login({ commit }, user) {
      return new Promise((resolve, reject) => {
        axios({ url: this.getters.url + '/login', data: user, method: 'POST' })
          .then(response => {
            var data = { 
              username: response.data.data.username,
              token: response.data.data.access_token,
              admin: response.data.data.admin
            }
            localStorage.setItem('token', data['token'])
            axios.defaults.headers.common['Authorization'] = `Bearer ${data['token']}`
            commit('auth', data)
            resolve(response)
          })
          .catch(error => {
            commit('logout')
            localStorage.removeItem('token')
            reject(error)
          })
      })
    },
    logout({ commit }) {
      return new Promise((resolve, reject) => {
        commit('logout')
        localStorage.removeItem('token')
        delete axios.defaults.headers.common['Authorization']
        resolve()
      })
    }
  },
  getters: {
    isLoggedIn: state => !!state.token,
    url: state => state.url,
    username: state => state.username,
    admin: state => state.admin
  }
})