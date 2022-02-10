import axios from 'axios'
import Cookies from 'js-cookie'

// initial state
const state = () => ({
  isLoggedIn: Cookies.get('csrf_access_token') !== undefined,
  username: localStorage.getItem('username') || '',
  remember: localStorage.getItem('remember') == '1' ? true : false,
  coins: localStorage.getItem('coins') || 0,
  admin: localStorage.getItem('admin') == '1' ? true : false,
  owner: localStorage.getItem('owner') == '1' ? true : false,
  inventory_enabled: localStorage.getItem('inventory_enabled') == '1' ? true : false,
  deployments_enabled: localStorage.getItem('deployments_enabled') == '1' ? true : false,
  deployments_basic: localStorage.getItem('deployments_basic') == '1' ? true : false,
  deployments_pro: localStorage.getItem('deployments_pro') == '1' ? true : false,
  monitoring_enabled: localStorage.getItem('monitoring_enabled') == '1' ? true : false,
  utils_enabled: localStorage.getItem('utils_enabled') == '1' ? true : false,
  client_enabled: localStorage.getItem('client_enabled') == '1' ? true : false,
  coins_execution: localStorage.getItem('coins_execution') || 0,
  utils_coins: localStorage.getItem('utils_coins') || 0,
  coins_day: localStorage.getItem('coins_day') || 0,
})

// getters
const getters = {
  isLoggedIn: state => state.isLoggedIn,
  username: state => state.username,
  remember: state => state.remember,
  coins: state => state.coins,
  admin: state => state.admin,
  owner: state => state.owner,
  inventory_enabled: state => state.inventory_enabled,
  deployments_enabled: state => state.deployments_enabled,
  deployments_basic: state => state.deployments_basic,
  deployments_pro: state => state.deployments_pro,
  monitoring_enabled: state => state.monitoring_enabled,
  utils_enabled: state => state.utils_enabled,
  client_enabled: state => state.client_enabled,
  coins_execution: state => state.coins_execution,
  utils_coins: state => state.utils_coins,
  coins_day: state => state.coins_day,
}

// actions
const actions = {
  init({ commit }, settings) {
    commit('init', settings)
  },
  login({ commit }, user) {
    return new Promise((resolve, reject) => {
      axios.post('/login', user)
        .then(response => {
          if (response.status == 200) {
            let data = {
              username: response.data.data.username,
              remember: user['remember'],
              coins: response.data.data.coins,
              admin: response.data.data.admin,
              owner: response.data.data.owner,
              inventory_enabled: response.data.data.inventory_enabled,
              deployments_enabled: response.data.data.deployments_enabled,
              deployments_basic: response.data.data.deployments_basic,
              deployments_pro: response.data.data.deployments_pro,
              monitoring_enabled: response.data.data.monitoring_enabled,
              utils_enabled: response.data.data.utils_enabled,
              client_enabled: response.data.data.client_enabled,
              coins_execution: response.data.data.coins_execution,
              utils_coins: response.data.data.utils_coins,
              coins_day: response.data.data.coins_day,
            }
            // Store variables to the local storage
            localStorage.setItem('username', data['username'])
            localStorage.setItem('remember', user['remember'] ? '1' : '0')
            localStorage.setItem('coins', data['coins'])
            localStorage.setItem('admin', data['admin'])
            localStorage.setItem('owner', data['owner'])
            localStorage.setItem('inventory_enabled', data['inventory_enabled'])
            localStorage.setItem('deployments_enabled', data['deployments_enabled'])
            localStorage.setItem('deployments_basic', data['deployments_basic'])
            localStorage.setItem('deployments_pro', data['deployments_pro'])
            localStorage.setItem('monitoring_enabled', data['monitoring_enabled'])
            localStorage.setItem('utils_enabled', data['utils_enabled'])
            localStorage.setItem('client_enabled', data['client_enabled'])
            localStorage.setItem('coins_execution', data['coins_execution'])
            localStorage.setItem('utils_coins', data['utils_coins'])
            localStorage.setItem('coins_day', data['coins_day'])

            // Add the token to the axios lib
            axios.defaults.headers.common['X-CSRF-TOKEN'] = Cookies.get('csrf_access_token')
            // Store variables to vuex
            commit('auth', data)
          }
          resolve(response)
        })
        .catch(error => {
          commit('logout')
          // Remove variables from the local storage
          if (!user['remember']) localStorage.removeItem('username')
          localStorage.removeItem('coins')
          localStorage.removeItem('admin')
          localStorage.removeItem('owner')
          localStorage.removeItem('inventory_enabled')
          localStorage.removeItem('deployments_enabled')
          localStorage.removeItem('deployments_basic')
          localStorage.removeItem('deployments_pro')
          localStorage.removeItem('monitoring_enabled')
          localStorage.removeItem('utils_enabled')
          localStorage.removeItem('client_enabled')
          localStorage.removeItem('coins_execution')
          localStorage.removeItem('utils_coins')
          localStorage.removeItem('coins_day')
          Cookies.remove('csrf_access_token')
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
  logout({ commit, getters }) {
    return new Promise((resolve) => {
      axios.post('/logout').finally(() => {
        commit('logout')
        // Remove variables from the local storage
        if (!getters.remember) localStorage.removeItem('username')
        localStorage.removeItem('coins')
        localStorage.removeItem('admin')
        localStorage.removeItem('owner')
        localStorage.removeItem('inventory_enabled')
        localStorage.removeItem('deployments_enabled')
        localStorage.removeItem('deployments_basic')
        localStorage.removeItem('deployments_pro')
        localStorage.removeItem('monitoring_enabled')
        localStorage.removeItem('utils_enabled')
        localStorage.removeItem('client_enabled')
        localStorage.removeItem('coins_execution')
        localStorage.removeItem('utils_coins')
        localStorage.removeItem('coins_day')
        Cookies.remove('csrf_access_token')

        // Remove token from axios header
        delete axios.defaults.headers.common['X-CSRF-TOKEN']
        resolve()
      })
    })
  }
}

// mutations
const mutations = {
  auth(state, data) {
    state.isLoggedIn = true
    state.username = data.username
    state.remember = data.remember == 1
    state.coins = data.coins
    state.admin = data.admin == 1
    state.owner = data.owner == 1
    state.inventory_enabled = data.inventory_enabled == 1
    state.deployments_enabled = data.deployments_enabled == 1
    state.deployments_basic = data.deployments_basic == 1
    state.deployments_pro = data.deployments_pro == 1
    state.monitoring_enabled = data.monitoring_enabled == 1
    state.utils_enabled = data.utils_enabled == 1
    state.client_enabled = data.client_enabled == 1
    state.coins_execution = data.coins_execution
    state.utils_coins = data.utils_coins
    state.coins_day = data.coins_day
  },
  logout(state) {
    state.isLoggedIn = false
    state.username = (state.remember) ? state.username : ''
    state.coins = 0
    state.admin = 0
    state.owner = 0
    state.inventory_enabled = 0
    state.deployments_enabled = 0
    state.deployments_basic = 0
    state.deployments_pro = 0
    state.monitoring_enabled = 0
    state.utils_enabled = 0
    state.client_enabled = 0
    state.coins_execution = 0
    state.utils_coins = 0
    state.coins_day = 0
  },
  coins(state, value) {
    state.coins = value
  }
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}