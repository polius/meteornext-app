import axios from 'axios'

// initial state
const state = () => ({
  username: localStorage.getItem('username') || '',
  token: localStorage.getItem('token') || '',
  coins: localStorage.getItem('coins') || 0,
  admin: localStorage.getItem('admin') || false,
  owner: localStorage.getItem('owner') || false,
  inventory_enabled: localStorage.getItem('inventory_enabled') == '1' ? true : false,
  inventory_secured: localStorage.getItem('inventory_secured') == '1' ? true : false,
  deployments_enabled: localStorage.getItem('deployments_enabled') == '1' ? true : false,
  deployments_basic: localStorage.getItem('deployments_basic') == '1' ? true : false,
  deployments_pro: localStorage.getItem('deployments_pro') == '1' ? true : false,
  deployments_inbenta: localStorage.getItem('deployments_inbenta') == '1' ? true : false,
  monitoring_enabled: localStorage.getItem('monitoring_enabled') == '1' ? true : false,
  utils_enabled: localStorage.getItem('utils_enabled') == '1' ? true : false,
  client_enabled: localStorage.getItem('client_enabled') == '1' ? true : false
})

// getters
const getters = {
  isLoggedIn: state => !!state.token,
  username: state => state.username,
  coins: state => state.coins,
  admin: state => state.admin,
  owner: state => state.owner,
  inventory_enabled: state => state.inventory_enabled,
  inventory_secured: state => state.inventory_secured,
  deployments_enabled: state => state.deployments_enabled,
  deployments_basic: state => state.deployments_basic,
  deployments_pro: state => state.deployments_pro,
  deployments_inbenta: state => state.deployments_inbenta,
  monitoring_enabled: state => state.monitoring_enabled,
  utils_enabled: state => state.utils_enabled,
  client_enabled: state => state.client_enabled
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
          if (response.status == 202) resolve(response)
          var data = {
            username: response.data.data.username,
            token: response.data.data.access_token,
            coins: response.data.data.coins,
            admin: response.data.data.admin,
            owner: response.data.data.owner,
            inventory_enabled: response.data.data.inventory_enabled,
            inventory_secured: response.data.data.inventory_secured,
            deployments_enabled: response.data.data.deployments_enabled,
            deployments_basic: response.data.data.deployments_basic,
            deployments_pro: response.data.data.deployments_pro,
            deployments_inbenta: response.data.data.deployments_inbenta,
            monitoring_enabled: response.data.data.monitoring_enabled,
            utils_enabled: response.data.data.utils_enabled,
            client_enabled: response.data.data.client_enabled
          }
          // Store variables to the local storage
          localStorage.setItem('username', data['username'])
          localStorage.setItem('token', data['token'])
          localStorage.setItem('coins', data['coins'])
          localStorage.setItem('admin', data['admin'])
          localStorage.setItem('owner', data['owner'])
          localStorage.setItem('inventory_enabled', data['inventory_enabled'])
          localStorage.setItem('inventory_secured', data['inventory_secured'])
          localStorage.setItem('deployments_enabled', data['deployments_enabled'])
          localStorage.setItem('deployments_basic', data['deployments_basic'])
          localStorage.setItem('deployments_pro', data['deployments_pro'])
          localStorage.setItem('deployments_inbenta', data['deployments_inbenta'])
          localStorage.setItem('monitoring_enabled', data['monitoring_enabled'])
          localStorage.setItem('utils_enabled', data['utils_enabled'])
          localStorage.setItem('client_enabled', data['client_enabled'])

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
          localStorage.removeItem('owner')
          localStorage.removeItem('inventory_enabled')
          localStorage.removeItem('inventory_secured')
          localStorage.removeItem('deployments_enabled')
          localStorage.removeItem('deployments_basic')
          localStorage.removeItem('deployments_pro')
          localStorage.removeItem('deployments_inbenta')
          localStorage.removeItem('monitoring_enabled')
          localStorage.removeItem('utils_enabled')
          localStorage.removeItem('client_enabled')
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
      localStorage.removeItem('owner')
      localStorage.removeItem('inventory_enabled')
      localStorage.removeItem('inventory_secured')
      localStorage.removeItem('deployments_enabled')
      localStorage.removeItem('deployments_basic')
      localStorage.removeItem('deployments_pro')
      localStorage.removeItem('deployments_inbenta')
      localStorage.removeItem('monitoring_enabled')
      localStorage.removeItem('utils_enabled')
      localStorage.removeItem('client_enabled')

      // Remove token from axios header
      delete axios.defaults.headers.common['Authorization']
      resolve()
    })
  }
}

// mutations
const mutations = {
  auth(state, data) {
    state.username = data.username
    state.token = data.token
    state.coins = data.coins
    state.admin = data.admin == 1
    state.owner = data.owner == 1
    state.inventory_enabled = data.inventory_enabled == 1
    state.inventory_secured = data.inventory_secured == 1
    state.deployments_enabled = data.deployments_enabled == 1
    state.deployments_basic = data.deployments_basic == 1
    state.deployments_pro = data.deployments_pro == 1
    state.deployments_inbenta = data.deployments_inbenta == 1
    state.monitoring_enabled = data.monitoring_enabled == 1
    state.utils_enabled = data.utils_enabled == 1
    state.client_enabled = data.client_enabled == 1
  },
  logout(state) {
    state.username = ''
    state.token = ''
    state.coins = 0
    state.admin = 0
    state.owner = 0
    state.inventory_enabled = 0
    state.inventory_secured = 0
    state.deployments_enabled = 0
    state.deployments_basic = 0
    state.deployments_pro = 0
    state.deployments_inbenta = 0
    state.monitoring_enabled = 0
    state.utils_enabled = 0
    state.client_enabled = 0
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