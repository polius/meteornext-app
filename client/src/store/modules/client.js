// CONNECTION
const connection = {
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

  // Treeview Menu (right click)
  showMenu: false,
  x: 0,
  y: 0,
  menuItems: ["Rename", "Truncate", "Delete", "Duplicate", "Export"],

  // Loadings
  loadingServer: false,
  loadingQuery: false,
  loadingDialog: false,

  // Client
  clientHeaders: [],
  clientItems: [],
  clientQuery: '',

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
  contentSearchFilterText2: '', // contentSearchFilterItems == 'BETWEEN'
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

  // AG Grid Helpers
  isRowSelected: false,
  currentCellEditMode: 'edit', // edit - new
  currentCellEditNode: {},
  currentCellEditValues: {},

  // Snackbar
  snackbar: false,
  snackbarTimeout: Number(5000),
  snackbarColor: '',
  snackbarText: '',

  // Helpers
  click: undefined,
  gridEditing: false
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
  // changeConnection({ commit }, data) { commit('currentConn', data) },
  // deleteConnection({ commit }, data) { commit('deleteConnection', data) },
}

// MUTATIONS
const mutations = {
  newConnection(state) { 
    state.connections.push(JSON.parse(JSON.stringify(connection)))
    state.currentConn = state.connections.length - 1
    state.connections[state.currentConn].treeviewItems = state.servers.slice(0)
  },
  // currentConn(state, data) { state.currentConn = data },
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