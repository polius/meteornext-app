// initial state
const state = () => ({
  servers: [],
  connections: [
    {
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

      // Client ACE Editor
      editor: null,
      editorTools: null,
      editorMarkers: [],
      editorCompleters: [],
      editorQuery: '',

      // Client AG-GRID
      clientHeaders: [],
      clientItems: [],

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

      // Objects
      objectHeaders: { tables: [], views: [], triggers: [], functions: [], procedures: [], events: [] },
      objectItems: { tables: [], views: [], triggers: [], functions: [], procedures: [], events: [] },

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
        objects: { tables: '', views: '', triggers: '', functions: '', procedures: '', events: '' }
      },

      // AG Grid API
      gridApi: { 
        client: null, 
        structure: { columns: null, indexes: null, fks: null, triggers: null }, 
        content: null, 
        info: null, 
        object: { tables: null, views: null, triggers: null, functions: null, procedures: null, events: null },
      },
      columnApi: { 
        client: null, 
        structure: { columns: null, indexes: null, fks: null, triggers: null }, 
        content: null, 
        info: null,
        object: { tables: null, views: null, triggers: null, functions: null, procedures: null, events: null },
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
  ],
  currentConn: 0
})

// getters
const getters = {
  currentConn: state => state.currentConn,
  connections: state => state.connections,
  connection: state => state.connections[state.currentConn],
}

// actions
const actions = {
  // updateCurrentConn({ commit }, data) { commit('updateCurrentConn', data) },
  // addEditorCompleters({ commit }, data) { commit('addEditorCompleters', data) },
  // removeEditorCompleters({ commit }, data) { commit('removeEditorCompleters', data) },
  // updateGridApi({ commit }, data) { commit('updateGridApi', data) },
}

// mutations
const mutations = {
  connection(state, data) { state.connections[state.currentConn][data.k] = data.v },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}