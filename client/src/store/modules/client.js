// CONNECTION
const connection = {
  // Connection Index
  index: 1,

  // Server
  server: {},

  // Header
  headerTab: 0,
  headerTabSelected: 'client',

  // Database Selector
  database: '',
  databaseItems: [],
  table: '',
  tableItems: [],

  // Sidebar
  sidebarItems: [],
  sidebarSelected: [],
  sidebarOpened: [],
  sidebarMode: 'servers',
  sidebarSearch: '',
  sidebarLoading: false,

  // Client
  clientHeaders: [],
  clientItems: [],
  clientQueries: '',
  clientQuery: { query: '', range: null },
  clientExecuting: null, // query, explain, stop

  // Structure
  tabStructureSelected: 'columns',
  structureHeaders: { columns: [], indexes: [], fks: [], triggers: [] },
  structureItems: { columns: [], indexes: [], fks: [], triggers: [] },

  // Content
  contentColumnsName: [],
  contentColumnsDefault: [],
  contentColumnsType: {},
  contentPks: [],
  contentSearchColumn: '',
  contentSearchFilterItems: ['=', '!=', '>', '<', '>=', '<=', 'LIKE', 'NOT LIKE', 'IN', 'NOT IN', 'BETWEEN', 'IS NULL', 'IS NOT NULL'],
  contentSearchFilter: '=',
  contentSearchFilterText: '',
  contentSearchFilterText2: '',
  contentHeaders: [],
  contentItems: [],

  // Info
  infoHeaders: { tables: [], views: [], triggers: [], functions: [], procedures: [], events: [] },
  infoItems: { tables: [], views: [], triggers: [], functions: [], procedures: [], events: [] },
  infoEditor: { tables: '', views: '', triggers: '', functions: '', procedures: '', events: '' },

  // Objecs
  objectsTab: 0,
  tabObjectsSelected: 'databases',
  objectsHeaders: { databases: [], tables: [], views: [], triggers: [], functions: [], procedures: [], events: [] },
  objectsItems: { databases: [], tables: [], views: [], triggers: [], functions: [], procedures: [], events: [] },

  // Rights
  rights: { sidebar: [], login: {}, server: {}, schema: [], resources: {}, syntax: '' },
  rightsDiff: { login: {}, server: { grant: [], revoke: [] }, schema: { grant: [], revoke: [] }, resources: {} },
  rightsSelected: {},
  rightsForm: { login: null, resources: null },
  rightsSidebarSelected: [],
  rightsSidebarOpened: [],

  // Bottom Bar
  bottomBar: {
    client: { text: '', status: '', info: '' },
    content: { text: '', status: '', info: '' },
    structure: {
      columns: { text: '', status: '', info: '' },
      indexes: { text: '', status: '', info: '' },
      fks: { text: '', status: '', info: '' },
      triggers: { text: '', status: '', info: '' }
    },
    objects: { databases: '', tables: '', views: '', triggers: '', functions: '', procedures: '', events: '' }
  },
}

// STATE
const state = {
  servers: [],
  components: {
    // Client ACE Editor
    editor: null,
    editorTools: null,
    editorMarkers: [],
    editorCompleters: [],

    // AG Grid API
    gridApi: {
      client: null,
      structure: { columns: null, indexes: null, fks: null, triggers: null },
      content: null,
      info: null,
      objects: { tables: null, views: null, triggers: null, functions: null, procedures: null, events: null },
    },
    columnApi: {
      client: null,
      structure: { columns: null, indexes: null, fks: null, triggers: null },
      content: null,
      info: null,
      objects: { tables: null, views: null, triggers: null, functions: null, procedures: null, events: null },
    },
  },
  connections: [JSON.parse(JSON.stringify(connection))],
  currentConn: 0,
  connectionIndex: 1,
  history: []
}

// GETTERS
const getters = {
  currentConn: state => state.currentConn,
  connections: state => state.connections,
  connection: state => state.connections[state.currentConn],
  components: state => state.components,
  client: state => state,
}

// ACTIONS
const actions = {
  newConnection({ commit }) { commit('newConnection') },
  changeConnection({ commit }, data) { commit('changeConnection', data) },
  deleteConnection({ commit }, data) { commit('deleteConnection', data) },
  addHistory({ commit }, data) { commit('addHistory', data) },
}

// MUTATIONS
const mutations = {
  newConnection(state) {
    // Store Client ACE Editor (current connection)
    state.connections[state.currentConn].clientQueries = state.components.editor.getValue()
    // Add new connection
    state.connectionIndex += 1
    let conn = JSON.parse(JSON.stringify(connection))
    conn.index = state.connectionIndex
    state.connections.push(conn)
    // Change connection pointer
    state.currentConn = state.connections.length - 1
    // Init servers list
    state.connections[state.currentConn].sidebarItems = state.servers.slice(0)
    // Init Client ACE Editor
    state.components.editor.setValue('')
  },
  changeConnection(state, data) {
    // Store Client ACE Editor (current connection)
    state.connections[state.currentConn].clientQueries = state.components.editor.getValue()
    // Change current connection
    state.currentConn = data
    // Load Client ACE Editor (new connection)
    state.components.editor.setValue(state.connections[state.currentConn].clientQueries, 1)
  },
  deleteConnection(state, data) {
    // Array contains only 1 element
    if (state.connections.length == 1) {
      // Re-Initialize current connection
      state.connections = [JSON.parse(JSON.stringify(connection))]
      // Init servers list
      state.connections[state.currentConn].sidebarItems = state.servers.slice(0)
    }
    // Delete last element of array
    else if (data + 1 == state.connections.length) {
      state.currentConn = data - 1
      state.connections.splice(data, 1)
    }
    // Delete other element
    else {
      if (data < state.currentConn) {
        state.connections.splice(data, 1)
        state.currentConn -= 1
      }
      else if (data > state.currentConn) {
        state.connections.splice(data, 1)
      }
      else {
        state.currentConn = data + 1
        state.connections.splice(data, 1)
        state.currentConn = data
      }
    }
    // Load Client ACE Editor
    state.components.editor.setValue(state.connections[state.currentConn].clientQueries, 1)
  },
  addHistory(state, data) {
    const moment = require('moment')
    const server = state.connections[state.currentConn].server
    for (let query of data['queries']) {
      state.history.push({
        'section': data['section'],
        'time': moment().format('YYYY-MM-DD HH:mm:ss'),
        'connection': '[' + server.type + ' ' + server.version + '] ' + server.name,
        'database': state.connections[state.currentConn].database,
        'query': query,
        'status': data['status'],
        'error': data['error']
      })
    }
  },
  client(state, data) { state[data.k] = data.v },
  components(state, data) { state.components[data.k] = data.v },
  connection(state, data) { state.connections[state.currentConn][data.k] = data.v },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}