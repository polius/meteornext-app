import { v4 as uuidv4 } from 'uuid';

// CONNECTION
const connection = () => {
  return {
    // Connection Index
    index: 1,

    // Connection Identifier
    id: uuidv4(),

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
    sidebarOrigin: [],
    sidebarSelected: [],
    sidebarOpened: [],
    sidebarMode: 'servers',
    sidebarSearch: '',
    sidebarLoading: false,
    sidebarLoadingServer: false,
    sidebarLoadingObject: false,

    // Client
    clientHeaders: [],
    clientItems: [],
    clientQueries: '',
    clientQuery: { query: '', range: null },
    clientQueryStopped: false,
    clientExecuting: null, // query, explain, stop
    clientCompleters: { databases: [], objects: [] },
    clientSession: null,
    clientLimit: null,

    // Structure
    tabStructureSelected: 'columns',
    structureHeaders: { columns: [], indexes: [], fks: [], triggers: [] },
    structureItems: { columns: [], indexes: [], fks: [], triggers: [] },
    structureState: null,
    structureQueryStopped: false,

    // Content
    contentColumnsName: [],
    contentColumnsDefault: [],
    contentColumnsType: {},
    contentColumnsExtra: [],
    contentPks: [],
    contentSearchColumn: '',
    contentSearchFilter: '=',
    contentSearchFilterText: '',
    contentSearchFilterText2: '',
    contentHeaders: [],
    contentItems: [],
    contentSortState: [],
    contentState: null,
    contentExecuting: false,

    // Info
    infoHeaders: { tables: [], views: [], triggers: [], functions: [], procedures: [], events: [] },
    infoItems: { tables: [], views: [], triggers: [], functions: [], procedures: [], events: [] },
    infoEditor: { tables: '', views: '', triggers: '', functions: '', procedures: '', events: '' },
    infoState: null,

    // Objects
    tabObjectsSelected: 'tables',
    objectsHeaders: { tables: [], views: [], triggers: [], functions: [], procedures: [], events: [] },
    objectsItems: { tables: [], views: [], triggers: [], functions: [], procedures: [], events: [] },
    objectsState: null,

    // Rights
    rights: { sidebar: [], login: {}, server: {}, schema: [], resources: {}, syntax: '' },
    rightsDiff: { login: {}, server: { grant: [], revoke: [] }, schema: { grant: [], revoke: [] }, resources: {} },
    rightsSelected: {},
    rightsForm: { login: null, resources: null },
    rightsSidebarSelected: [],
    rightsSidebarOpened: [],
    rightsLoading: false,

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
}

const getDefaultState = () => {
  return {
    servers: [],
    serversList: [],
    components: {
      // Client ACE Editor
      editor: null,
      editorTools: null,
      editorKeywords: null,
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
    connections: [JSON.parse(JSON.stringify(connection()))],
    currentConn: 0,
    connectionIndex: 1,
    history: [],
    settings: {},
    dialogOpened: false,
  }
}

// STATE
const state = getDefaultState()

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
  logout({ commit }) { commit('logout') },
  reset({ commit }) { commit('reset') },
  newConnection({ commit }) { commit('newConnection') },
  changeConnection({ commit }, data) { commit('changeConnection', data) },
  deleteConnection({ commit }, data) { commit('deleteConnection', data) },
  addHistory({ commit }, data) { commit('addHistory', data) },
}

// MUTATIONS
const mutations = {
  logout(state) {
    state.connections[state.currentConn].clientExecuting = null
    if (state.components.gridApi.client != null) state.components.gridApi.client.showNoRowsOverlay()
    if (state.connections[state.currentConn].bottomBar.client['status'] == 'executing') state.connections[state.currentConn].bottomBar.client = { text: '', status: '', info: '' }
  },
  reset(state) {
    Object.assign(state, getDefaultState())
  },
  newConnection(state) {
    // Store Client ACE Editor (current connection)
    state.connections[state.currentConn].clientQueries = state.components.editor.getValue()
    state.connections[state.currentConn].clientSession = state.components.editor.session
    // Add new connection
    state.connectionIndex += 1
    let conn = JSON.parse(JSON.stringify(connection()))
    conn.index = state.connectionIndex
    conn.id = uuidv4()
    state.connections.push(conn)
    // Change connection pointer
    state.currentConn = state.connections.length - 1
    // Init servers list
    state.connections[state.currentConn].sidebarItems = state.servers.slice(0)
    // Clear current queries
    state.connections[state.currentConn].clientQueries = ''
    // Init completers
    state.connections[state.currentConn].clientCompleters = [state.components.editorKeywords]
  },
  changeConnection(state, data) {
    // Store Client ACE Editor (current connection)
    state.connections[state.currentConn].clientQueries = state.components.editor.getValue()
    state.connections[state.currentConn].clientSession = state.components.editor.session
    // Change current connection
    state.currentConn = data
  },
  deleteConnection(state, data) {
    // Array contains only 1 element
    if (state.connections.length == 1) {
      // Re-Initialize current connection
      state.connections = [JSON.parse(JSON.stringify(connection()))]
      state.connections[0].id = uuidv4()
      // Init servers list
      state.connections[state.currentConn].sidebarItems = state.servers.slice(0)
      // Clean selected database
      state.connections[state.currentConn].database = ''
    }
    // Delete last element of array
    else if (data == state.connections.length - 1) {
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
  },
  addHistory(state, data) {
    const server = 'server' in data ? data['server'] : state.connections[state.currentConn].server
    const moment = require('moment')
    for (let query of data['queries']) {
      state.history.unshift({
        'section': data['section'],
        'time': moment().format('YYYY-MM-DD HH:mm:ss'),
        'connection': '[' + server.engine + ' ' + server.version + '] ' + server.name,
        'database': query['database'],
        'query': query['query'],
        'status': 'error' in query ? false : true,
        'records': query['rowCount'],
        'elapsed': data['elapsed'] + 's',
        'error': 'error' in query ? query['error'] : null
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