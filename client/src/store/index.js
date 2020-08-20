import Vue from 'vue'
import Vuex from 'vuex'
import app from './modules/app'
import client from './modules/client'

Vue.use(Vuex)

export default new Vuex.Store({
  modules: {
    app,
    client
  }
})