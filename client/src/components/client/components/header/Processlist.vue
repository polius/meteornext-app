<template>
  <div>
    <v-dialog v-model="dialog" fullscreen max-width="100%" transition="fade-transition">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text body-1"><v-icon small style="padding-right:10px; padding-bottom:2px">fas fa-server</v-icon>PROCESSLIST</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <div class="body-1">{{ server.name }}</div>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn text @click="stopProcesslist" :title="stopped ? 'Start processlist retrieval' : 'Stop processlist retrieval'" style="margin-right:10px; height:100%"><v-icon small style="padding-right:10px">{{ stopped ? 'fas fa-play' : 'fas fa-stop'}}</v-icon>{{ stopped ? 'START' : 'STOP' }}</v-btn>
          <v-btn text @click="exportProcesslist" style="margin-right:10px; height:100%"><v-icon small style="padding-right:10px">fas fa-arrow-down</v-icon>Export</v-btn>
          <v-btn text @click="settingsProcesslist" style="height:100%"><v-icon small style="padding-right:10px; font-size:14px;">fas fa-cog</v-icon>Settings</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-text-field @input="onSearch" v-model="search" label="Search" solo color="white" dense background-color="transparent" hide-details style="margin-right:-10px"></v-text-field>
          <!-- <v-btn @click="dialog = false" icon style="margin-left:5px;"><v-icon>fas fa-times-circle</v-icon></v-btn> -->
        </v-toolbar>
        <v-card-text style="padding:0px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <ag-grid-vue suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressContextMenu preventDefaultOnContextMenu @grid-ready="onGridReady" @first-data-rendered="onFirstDataRendered" @cell-key-down="onCellKeyDown" @cell-context-menu="onContextMenu" style="width:100%; height:calc(100vh - 48px);" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="header" :rowData="items"></ag-grid-vue>
                <v-menu v-model="contextMenu" :position-x="contextMenuX" :position-y="contextMenuY" absolute offset-y style="z-index:10">
                  <v-list style="padding:0px;">
                    <v-list-item-group v-model="contextMenuModel">
                      <div v-for="[index, item] of contextMenuItems.entries()" :key="index">
                        <v-list-item v-if="item != '|'" @click="contextMenuClicked(item)">
                          <v-list-item-title>{{item}}</v-list-item-title>
                        </v-list-item>
                        <v-divider v-else></v-divider>
                      </div>
                    </v-list-item-group>
                  </v-list>
                </v-menu>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!--------------------->
    <!-- Settings Dialog -->
    <!--------------------->
    <v-dialog v-model="settingsDialog" max-width="50%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">SETTINGS</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="settingsDialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-bottom:15px;">
                  <v-text-field v-model="settingsItem.refresh_rate" label="Refresh Rate (seconds)" :rules="[v => v == parseInt(v) && v > 0 || '']" filled hide-details></v-text-field>
                  <v-switch v-model="settingsItem.analyze_queries" label="Analyze scanned rows" hide-details></v-switch>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px;">
                      <v-btn :loading="loading" :disabled="loading" @click="settingsProcesslistSubmit" color="primary">Save</v-btn>
                    </v-col>
                    <v-col>
                      <v-btn :disabled="loading" @click="settingsDialog = false" outlined color="#e74d3c">Cancel</v-btn>
                    </v-col>
                  </v-row>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!----------------->
    <!-- Kill Dialog -->
    <!----------------->
    <v-dialog v-model="killDialog" persistent max-width="50%">
      <v-card>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <div class="text-h6" style="font-weight:400;">Kill queries</div>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:15px; margin-bottom:15px;">
                  <div class="body-1" style="font-weight:300; font-size:1.05rem!important;">Are you sure you want to kill the selected queries?</div>
                  <v-checkbox v-model="killDialogCheckbox" label="Terminate the connection" hide-details style="margin-top:15px;"></v-checkbox>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loading" @click="killQuerySubmit" color="primary">Kill</v-btn>
                    </v-col>
                    <v-col style="margin-bottom:10px;">
                      <v-btn :disabled="loading" @click="killDialog = false" outlined color="#e74d3c">Cancel</v-btn>
                    </v-col>
                  </v-row>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!-------------------->
    <!-- Analyze Dialog -->
    <!-------------------->
    <v-dialog v-model="analyzeDialog" max-width="90%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">Analyze queries</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="exportAnalyze" color="primary"><v-icon small style="padding-right:10px">fas fa-arrow-down</v-icon>Export</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-text-field @input="onAnalyzeSearch" v-model="analyzeDialogSearch" label="Search" outlined dense color="white" hide-details></v-text-field>
          <v-btn @click="analyzeDialog = false" icon style="margin-left:5px"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:0px">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <ag-grid-vue suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection suppressContextMenu preventDefaultOnContextMenu @grid-ready="onAnalyzeGridReady" @cell-key-down="onCellKeyDown" @first-data-rendered="onFirstAnalyzeDataRendered" style="width:100%; height:80vh;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="single" :columnDefs="analyzeColumns" :rowData="analyzeItems"></ag-grid-vue>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped src="@/styles/agGridVue.css"></style>

<script>
import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'
import {AgGridVue} from "ag-grid-vue";

import axios from 'axios'

export default {
  data() {
    return {
      loading: false,
      // Dialog
      dialog: false,
      stopped: true,
      timer: null,
      loaded : false,
      // AG Grid
      gridApi: null,
      columnApi: null,
      search: '',
      header: [],
      items: [],
      // Settings Dialog
      settingsDialog: false,
      settingsItem: {},
      // Context Menu
      contextMenu: false,
      contextMenuModel: null,
      contextMenuItems: [],
      contextMenuItem: {},
      contextMenuX: 0,
      contextMenuY: 0,
      // Kill Dialog
      killDialog: false,
      killDialogCheckbox: false,
      // Analyze Dialog
      analyzeDialog: false,
      analyzeDialogSearch: '',
      analyzeGridApi: null,
      analyzeColumnApi: null,
      analyzeColumns: [],
      analyzeItems: [],
      analyzeData: {},
    }
  },
  components: { AgGridVue },
  computed: {
    ...mapFields([
      'settings',
      'dialogOpened',
    ], { path: 'client/client' }),
    ...mapFields([
      'headerTab',
      'headerTabSelected',
      'server',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('show-processlist', this.showDialog);
  },
  watch: {
    dialog: function(value) {
      this.dialogOpened = value
      if (!value) {
        const tab = {'client': 0, 'structure': 1, 'content': 2, 'info': 3, 'objects': 6}
        this.headerTab = tab[this.headerTabSelected]
        clearTimeout(this.timer)
      }
    },
  },
  methods: {
    showDialog() {
      this.dialog = true
      this.search = ''
      this.loaded = false
      this.stopped = false
      if (this.gridApi != null) {
        this.loaded = true
        this.getProcesslist()
      }
    },
    onGridReady(params) {
      this.gridApi = params.api
      this.columnApi = params.columnApi
      if (this.loaded == false) {
        this.loaded = true
        this.getProcesslist()
      }
    },
    onAnalyzeGridReady(params) {
      this.analyzeGridApi = params.api
      this.analyzeColumnApi = params.columnApi
    },
    onFirstDataRendered() {
      this.resizeTable()
    },
    onFirstAnalyzeDataRendered() {
      if (this.analyzeGridApi != null) this.analyzeGridApi.sizeColumnsToFit()
    },
    resizeTable() {
      if (this.gridApi != null) this.gridApi.sizeColumnsToFit()
    },
    onCellKeyDown(e) {
      if (e.event.key == "c" && (e.event.ctrlKey || e.event.metaKey)) {
        navigator.clipboard.writeText(e.value)

        // Highlight cells
        e.event.target.classList.add('ag-cell-highlight');
        e.event.target.classList.remove('ag-cell-highlight-animation')

        // Add animation
        window.setTimeout(function () {
            e.event.target.classList.remove('ag-cell-highlight')
            e.event.target.classList.add('ag-cell-highlight-animation')
            e.event.target.style.transition = "background-color " + 200 + "ms"

            // Remove animation
            window.setTimeout(function () {
                e.event.target.classList.remove('ag-cell-highlight-animation')
                e.event.target.style.transition = null;
            }, 200);
        }, 200);
      }
    },
    onContextMenu(e) {
      const selectedNodes = this.gridApi.getSelectedNodes().map(node => node.data.Id)
      if (!selectedNodes.includes(e.node.data.Id)) this.gridApi.deselectAll()
      e.node.setSelected(true)
      this.contextMenuModel = null
      this.contextMenuX = e.event.clientX
      this.contextMenuY = e.event.clientY
      this.contextMenuItems = ['Kill','|','Select All','Deselect All']
      if (this.settings['analyze_queries'] == 1 || false) this.contextMenuItems.unshift('Analyze')
      this.contextMenu = true
    },
    contextMenuClicked(item) {
      if (item == 'Analyze') this.analyzeQuery()
      else if (item == 'Kill') this.killQuery()
      else if (item == 'Select All') this.gridApi.selectAll()
      else if (item == 'Deselect All') this.gridApi.deselectAll()
    },
    onSearch(value) {
      this.gridApi.setQuickFilter(value)
    },
    onAnalyzeSearch(value) {
      this.analyzeGridApi.setQuickFilter(value)
    },
    getProcesslist() {
      if (this.stopped) return
      const payload = {
        connection: 0,
        server: this.server.id,
        database: null,
        queries: ['SHOW FULL PROCESSLIST'],
      }
      axios.post('/client/execute', payload)
        .then((response) => {
          let data = JSON.parse(response.data.data)[0].data
          this.parseProcesslist(data)
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message, 'error')
        })
    },
    parseProcesslist(data) {
      new Promise((resolve) => {
        if (!(this.settings['analyze_queries'] == 1 || false)) { this.analyzeData = {}; resolve() }
        else this.analyzeQueriesFunction(resolve, data)
      }).then(() => {
        // Build header
        let header = []
        if (data.length > 0) {
          let keys = Object.keys(data[0])
          for (let key of keys) header.push({ headerName: key, colId: key, field: key, sortable: true, filter: true, resizable: true, editable: false })
          if (this.settings['analyze_queries'] == 1 || false) header.push({ headerName: 'Scanned Rows', colId: 'scanned', field: 'scanned', sortable: true, filter: true, resizable: true, editable: false,
            cellRenderer: function(params) {
              if (params.value != null) {
                if (params.value < 10000) return '<i class="fas fa-circle" style="color:#00b16a; margin-right:10px"></i>' + params.value
                else if (params.value < 1000000) return '<i class="fas fa-circle" style="color:#fa8131; margin-right:10px"></i>' + params.value
                else return '<i class="fas fa-circle" style="color:#e74d3c; margin-right:10px"></i>' + params.value 
              }
              return '<i class="fas fa-circle" style="color:grey; margin-right:10px"></i>Not a DML query'
            }
          })
        }
        // Check if resize columns is needed
        const scannedIn = this.header.some(x => x.colId == 'scanned')
        const shouldResize = ((this.settings['analyze_queries'] == 1 || false) && !scannedIn) || ((!this.settings['analyze_queries'] == 1 || true) && scannedIn) 
        // Apply new columns
        this.header = header.slice(0)
        this.gridApi.setColumnDefs(this.header)
        if (shouldResize) this.resizeTable()
        // Build items
        if (Object.keys(this.analyzeData).length != 0) {
          for (let row of data) {
            if (row['Id'] in this.analyzeData) {
              row['scanned'] = this.analyzeData[row['Id']].reduce((acc, val) => {
                if (val['rows'] != null) {
                  if (acc == null)  acc = val['rows']
                  else acc *= val['rows']
                }
                return acc
              }, null)
            }
            else row['scanned'] = null
          }
        }
        // Preserve selected / filtered nodes
        const selectedNodes = this.gridApi.getSelectedNodes().map(node => node.data.Id)
        const filterModel = this.gridApi.getFilterModel()
        // Reload new items
        this.items = data
        this.gridApi.setRowData(data)
        // Apply selected / filtered nodes
        this.$nextTick(() => {
          this.gridApi.forEachNode((node) => node.setSelected(selectedNodes.includes(node.data.Id)))
          this.gridApi.setFilterModel(filterModel)
        })
        // Repeat processlist request
        this.timer = setTimeout(this.getProcesslist, (this.settings['refresh_rate'] || 5) * 1000)
      })
    },
    analyzeQueriesFunction(resolve, data) {
      // Build data
      let match = {}
      let queries = []
      let database = []
      data.forEach((val) => {
        if (val.Info != null && (val.Info.toLowerCase().startsWith('select') || val.Info.toLowerCase().startsWith('insert') || val.Info.toLowerCase().startsWith('update') || val.Info.toLowerCase().startsWith('delete'))) {
          queries.push('EXPLAIN ' + val.Info)
          database.push(val.db)
          match[queries.length - 1] = val.Id
        }
      })
      if (queries.length == 0) resolve()
      // Build payload
      const payload = {
        connection: 0,
        server: this.server.id,
        database,
        queries,
        executeAll: true,
      }
      // Get explain
      axios.post('/client/execute', payload)
        .then((response) => {
          let data = JSON.parse(response.data.data)
          this.parseAnalyzer(data, match)
          resolve()
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else {
            let data = JSON.parse(error.response.data.data)
            this.parseAnalyzer(data, match)
            resolve()
          }
        })
    },
    parseAnalyzer(data, match) {
      let parsedData = {}
      for (const [i, v] of data.entries()) {
        if ('error' in v) parsedData[match[i]] = v['error']
        else parsedData[match[i]] = v['data']
      }
      this.analyzeData = JSON.parse(JSON.stringify(parsedData))
    },
    stopProcesslist() {
      if (this.stopped) clearTimeout(this.timer)
      this.stopped = !this.stopped
      if (!this.stopped) this.getProcesslist() 
    },
    exportProcesslist() {
      let replacer = (key, value) => value === null ? undefined : value
      let header = Object.keys(this.items[0])
      let exportData = this.items.map(row => header.map(fieldName => JSON.stringify(row[fieldName], replacer)).join(','))
      exportData.unshift(this.header.map(row => row['headerName']).join(','))
      exportData = exportData.join('\r\n')
      this.download('processlist.csv', exportData)
    },
    exportAnalyze() {
      let replacer = (key, value) => value === null ? undefined : value
      let header = Object.keys(this.analyzeItems[0])
      let exportData = this.analyzeItems.map(row => header.map(fieldName => JSON.stringify(row[fieldName], replacer)).join(','))
      exportData.unshift(this.analyzeColumns.map(row => row['headerName']).join(','))
      exportData = exportData.join('\r\n')
      this.download('processlist_analyze.csv', exportData)
    },
    settingsProcesslist() {
      this.settingsItem.refresh_rate = this.settings['refresh_rate'] || 5
      this.settingsItem.analyze_queries = this.settings['analyze_queries'] == 1 || false
      this.settingsDialog = true
    },
    settingsProcesslistSubmit() {
      // Check if all required fields are filled
      if (!this.$refs.form.validate()) {
        EventBus.$emit('send-notification', 'Please make sure all required fields are filled out correctly', 'error')
        return
      }
      this.loading = true
      const payload = {
        refresh_rate: this.settingsItem['refresh_rate'],
        analyze_queries: this.settingsItem['analyze_queries']
      }
      axios.put('/client/settings', payload)
        .then((response) => {
          this.settings['refresh_rate'] = payload.refresh_rate
          this.settings['analyze_queries'] = payload.analyze_queries ? 1 : 0
          this.settingsDialog = false
          EventBus.$emit('send-notification', response.data.message, '#00b16a', 1)
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
        })
    },
    download(filename, text) {
      var element = document.createElement('a')
      element.setAttribute('href', 'data:text/plain;charset=utf-8,' + encodeURIComponent(text))
      element.setAttribute('download', filename)
      element.style.display = 'none'
      document.body.appendChild(element)
      element.click()
      document.body.removeChild(element)
    },
    analyzeQuery() {
      const selectedIds = this.gridApi.getSelectedRows().map(x => x.Id.toString())
      const selectedData = Object.keys(this.analyzeData).filter(key => selectedIds.includes(key)).reduce((obj, key) => { return {...obj, [key]: this.analyzeData[key] }}, {})
      if (Object.keys(selectedData) == 0) EventBus.$emit('send-notification', 'The selected queries can\'t be analyzed (not a DML query)', 'error')
      else {
        // Build columns
        if (this.analyzeColumns.length == 0) {
          let header = []
          let keys = Object.keys(Object.values(selectedData)[0][0])
          for (let key of keys) header.push({ headerName: key, colId: key, field: key, sortable: true, filter: true, resizable: true, editable: false })
          this.analyzeColumns = header
        }
        // Build items
        let items = []
        for (let query of Object.values(selectedData)) {
          for (let row of query) items.push(row)
        }
        this.analyzeItems = items.slice(0)
        if (this.analyzeGridApi != null) this.analyzeGridApi.sizeColumnsToFit()
        this.analyzeDialog = true
      }
    },
    killQuery() {
      this.killDialogCheckbox = false
      this.killDialog = true
    },
    killQuerySubmit() {
      // Build queries
      let queries = this.gridApi.getSelectedRows().map(x => x.Id)
      if (this.server.type == 'Aurora MySQL') {
        if (this.killDialogCheckbox) queries = queries.map(x => 'CALL mysql.rds_kill(' + x + ')')
        else queries = queries.map(x => 'CALL mysql.rds_kill_query(' + x + ')')
      }
      else {
        if (this.killDialogCheckbox) queries = queries.map(x => 'KILL ' + x)
        else queries = queries.map(x => 'KILL QUERY ' + x)
      } 
      // Build payload
      const payload = {
        connection: 0,
        server: this.server.id,
        database: null,
        queries,
        executeAll: true,
      }
      // Kill queries
      axios.post('/client/execute', payload)
        .then(() => {
          EventBus.$emit('send-notification', 'Queries killed', '#00b16a', 2)
          this.killDialog = false
          clearTimeout(this.timer)
          this.getProcesslist()
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
        })
    }
  }
}
</script>