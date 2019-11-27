import Vue from 'vue'
import Vuex from 'vuex'
import axios from 'axios'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    url: '',
    username: localStorage.getItem('username') || '',
    token: localStorage.getItem('token') || '',
    coins: localStorage.getItem('coins') || 0,
    admin: localStorage.getItem('admin') == '1' ? true : false,
    deployments_enable: localStorage.getItem('deployments_enable') == '1' ? true : false,
    deployments_basic: localStorage.getItem('deployments_basic') == '1' ? true : false,
    deployments_pro: localStorage.getItem('deployments_pro') == '1' ? true : false,
    deployments_inbenta: localStorage.getItem('deployments_inbenta') == '1' ? true : false,
    deployments_edit: localStorage.getItem('deployments_edit') == '1' ? true : false
  },
  mutations: {
    init(state, data) {
      state.url = 'http://' + data.settings.server.host + ':' + data.settings.server.port
    },
    auth(state, data) {
      state.username = data.username
      state.token = data.token
      state.coins = data.coins
      state.admin = data.admin == 1
      state.deployments_enable = data.deployments_enable == 1
      state.deployments_basic = data.deployments_basic == 1
      state.deployments_pro = data.deployments_pro == 1
      state.deployments_inbenta = data.deployments_inbenta == 1
      state.deployments_edit = data.deployments_edit == 1
    },
    logout(state) {
      state.username = ''
      state.token = ''
      state.coins = 0
      state.admin = false
      state.deployments_enable = 0
      state.deployments_basic = 0
      state.deployments_pro = 0
      state.deployments_inbenta = 0
      state.deployments_edit = 0
    },
    coins(state, value) {
      state.coins = value
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
              coins: response.data.data.coins,
              admin: response.data.data.admin,
              deployments_enable: response.data.data.deployments_enable,
              deployments_basic: response.data.data.deployments_basic,
              deployments_pro: response.data.data.deployments_pro,
              deployments_inbenta: response.data.data.deployments_inbenta,
              deployments_edit: response.data.data.deployments_edit
            }
            // Store variables to the local storage
            localStorage.setItem('username', data['username'])
            localStorage.setItem('token', data['token'])
            localStorage.setItem('coins', data['coins'])
            localStorage.setItem('admin', data['admin'])
            localStorage.setItem('deployments_enable', data['deployments_enable'])
            localStorage.setItem('deployments_basic', data['deployments_basic'])
            localStorage.setItem('deployments_pro', data['deployments_pro'])
            localStorage.setItem('deployments_inbenta', data['deployments_inbenta'])
            localStorage.setItem('deployments_edit', data['deployments_edit'])

            // Add the token to the axios lib
            axios.defaults.headers.common['Authorization'] = `Bearer ${data['token']}`

            // Store variables to vuex
            commit('auth', data)
            resolve(response)
          })
          .catch(error => {
            commit('logout')
            // Remove variables from the local storage
            localStorage.removeItem('username')
            localStorage.removeItem('token')
            localStorage.removeItem('coins')
            localStorage.removeItem('admin')
            localStorage.removeItem('deployments_enable')
            localStorage.removeItem('deployments_basic')
            localStorage.removeItem('deployments_pro')
            localStorage.removeItem('deployments_inbenta')
            localStorage.removeItem('deployments_edit')
            reject(error)
          })
      })
    },
    coins({ commit }, value) {
      return new Promise((resolve) => {
        commit('coins', value)
        // Remove variables from the local storage
        localStorage.setItem('coins', value)
        resolve()
      })
    },
    logout({ commit }) {
      return new Promise((resolve) => {
        commit('logout')
        // Remove variables from the local storage
        localStorage.removeItem('username')
        localStorage.removeItem('token')
        localStorage.removeItem('coins')
        localStorage.removeItem('admin')
        localStorage.removeItem('deployments_enable')
        localStorage.removeItem('deployments_basic')
        localStorage.removeItem('deployments_pro')
        localStorage.removeItem('deployments_inbenta')
        localStorage.removeItem('deployments_edit')

        // Remove token from axios header
        delete axios.defaults.headers.common['Authorization']
        resolve()
      })
    }
  },
  getters: {
    isLoggedIn: state => !!state.token,
    url: state => state.url,
    username: state => state.username,
    coins: state => state.coins,
    admin: state => state.admin,
    deployments_enable: state => state.deployments_enable,
    deployments_basic: state => state.deployments_basic,
    deployments_pro: state => state.deployments_pro,
    deployments_inbenta: state => state.deployments_inbenta,
    deployments_edit: state => state.deployments_edit
  }
})