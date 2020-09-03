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
  databaseItems: [],
  database: '',
  tableItems: [],
  table: '',

  // Treeview
  treeview: [],
  treeviewItems: [],
  treeviewSelected: {},
  treeviewOpened: [],
  treeviewMode: 'servers',
  treeviewSearch: '',

  // Client
  clientHeaders: [],
  clientItems: [],
  clientQuery: '',
  clientQueryExecuting: false,

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
  tabObjectsSelected: 'databases',
  objectsHeaders: { databases: [], tables: [], views: [], triggers: [], functions: [], procedures: [], events: [] },
  objectsItems: { databases: [], tables: [], views: [], triggers: [], functions: [], procedures: [], events: [] },

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
}

// MUTATIONS
const mutations = {
  newConnection(state) {
    state.connectionIndex += 1
    // Add new connection
    let conn = JSON.parse(JSON.stringify(connection))
    conn.index = state.connectionIndex
    state.connections.push(conn)
    // Change connection pointer
    state.currentConn = state.connections.length - 1
    // Init servers list
    state.connections[state.currentConn].treeviewItems = state.servers.slice(0)
    // Init Client ACE Editor
    state.components.editor.setValue('')
  },
  changeConnection(state, data) {
    // Change current connection
    state.currentConn = data
    // Load Client ACE Editor
    state.components.editor.setValue(state.connections[state.currentConn].clientQuery,1)
  },
  deleteConnection(state, data) {
    // Array contains only 1 element
    if (state.connections.length == 1) {
      // Re-Initialize current connection
      state.connections = [JSON.parse(JSON.stringify(connection))]
      // Init servers list
      state.connections[state.currentConn].treeviewItems = state.servers.slice(0)
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
    state.components.editor.setValue(state.connections[state.currentConn].clientQuery, 1)
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