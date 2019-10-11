import Vue from 'vue'
import Vuex from 'vuex'
import axios from 'axios'

Vue.use(Vuex)

export default new Vuex.Store({
  state: {
    url: '',
    username: localStorage.getItem('username') || '',
    token: localStorage.getItem('token') || '',
    admin: localStorage.getItem('admin') == '1' ? true : false,
    deployments_enable: localStorage.getItem('deployments_enable') == '1' ? true : false,
    deployments_edit: localStorage.getItem('deployments_edit') == '1' ? true : false
  },
  mutations: {
    init(state, data) {
      var prefix = data.settings.ssl ? 'https://' : 'http://'
      state.url = prefix + data.settings.host + ':' + data.settings.port
    },
    auth(state, data) {
      state.username = data.username
      state.token = data.token
      state.admin = data.admin == 1
      state.deployments_enable = data.deployments_enable == 1
      state.deployments_edit = data.deployments_edit == 1
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
              admin: response.data.data.admin,
              deployments_enable: response.data.data.deployments_enable,
              deployments_edit: response.data.data.deployments_edit
            }
            // Store variables to the local storage
            localStorage.setItem('username', data['username'])
            localStorage.setItem('token', data['token'])
            localStorage.setItem('admin', data['admin'])
            localStorage.setItem('deployments_enable', data['deployments_enable'])
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
            localStorage.removeItem('admin')
            localStorage.removeItem('deployments_enable')
            localStorage.removeItem('deployments_edit')
            reject(error)
          })
      })
    },
    logout({ commit }) {
      return new Promise((resolve) => {
        commit('logout')
        // Remove variables from the local storage
        localStorage.removeItem('username')
        localStorage.removeItem('token')
        localStorage.removeItem('admin')
        localStorage.removeItem('deployments_enable')
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
    admin: state => state.admin,
    deployments_enable: state => state.deployments_enable,
    deployments_edit: state => state.deployments_edit
  }
})