// initial state
const state = () => ({
  servers: [],
  connections: [
    {
      // Server
      server: {},

      // Header
      headerTab: 0,

      // Database Selector
      databaseItems: [],
      database: '',

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
      structureTab: 'columns',
      structureOrigin: {},
      structureHeaders: [],
      structureItems: [],

      // Content
      contentTableSelected: '',
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
      infoEditor: null,
      infoHeaders: [],
      infoItems: [],

      // Bottom Bar
      bottomBarClient: { text: '', status: '', info: '' },
      bottomBarContent: { text: '', status: '', info: '' },
      bottomBarStructure: { text: '', status: '', info: '' },

      // AG Grid API
      gridApi: { client: null, structure: null, content: null, info: null },
      columnApi: { client: null, structure: null, content: null, info: null },

      // AG Grid Helpers
      isRowSelected: false,
      currentCellEditMode: 'edit', // edit - new
      currentCellEditNode: {},
      currentCellEditValues: {},

      // Client Dialog
      dialog: false,
      dialogMode: '',
      dialogTitle: '',
      dialogText: '',
      dialogButtonText1: '',
      dialogButtonText2: '',
      dialogSelect: '',

      // Edit Dialog
      editDialog: false,
      editDialogTitle: '',
      editDialogEditor: null,

      // Structure Dialog
      structureDialog: false,
      structureDialogMode: '',
      structureDialogTitle: '',
      structureDialogItem: {},
      structureDialogColumnTypes: [],
      structureDialogCollations: [],

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
  updateCurrentConn({ commit }, data) { commit('updateCurrentConn', data) },
  addEditorCompleters({ commit }, data) { commit('addEditorCompleters', data) },
  removeEditorCompleters({ commit }, data) { commit('removeEditorCompleters', data) },
  updateGridApi({ commit }, data) { commit('updateGridApi', data) },
}

// mutations
const mutations = {
  connection(state, data) { state.connections[state.currentConn][data.k] = data.v },
  updateCurrentConn(state, data) { state.currentConn = data },
  addEditorCompleters(state, data) { 
    state.connections[state.currentConn].editor.completers.push(data) 
    state.connections[state.currentConn].editorCompleters = data
  },
  removeEditorCompleters(state, data) { 
    state.connections[state.currentConn].editor.completers.splice(data + 1, 1)
    state.connections[state.currentConn].editorCompleters.splice(data, 1)
  },
  updateGridApi(state, data) {
    state.connections[state.currentConn].gridApi[data.key] = data.value.api
    state.connections[state.currentConn].columnApi[data.key] = data.value.columnApi
  },
}

export default {
  namespaced: true,
  state,
  getters,
  actions,
  mutations
}