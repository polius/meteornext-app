<template>
  <div>
    <v-dialog v-model="dialog" persistent max-width="90%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text"><v-icon small style="padding-right:10px; padding-bottom:2px">fas fa-server</v-icon>Processlist</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="stopProcesslist" color="primary" :title="stopped ? 'Start processlist retrieval' : 'Stop processlist retrieval'" style="margin-right:10px;"><v-icon small style="padding-right:10px">{{ stopped ? 'fas fa-play' : 'fas fa-stop'}}</v-icon>{{ stopped ? 'START' : 'STOP' }}</v-btn>
          <v-btn @click="exportProcesslist" color="primary" style="margin-right:10px;"><v-icon small style="padding-right:10px">fas fa-arrow-down</v-icon>Export</v-btn>
          <v-btn @click="settingsProcesslist" color="primary"><v-icon small style="padding-right:10px; font-size:14px;">fas fa-cog</v-icon>Settings</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-text-field @input="onSearch" v-model="search" label="Search" outlined dense color="white" hide-details></v-text-field>
          <v-btn @click="dialog = false" icon style="margin-left:5px"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:0px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <ag-grid-vue suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressContextMenu preventDefaultOnContextMenu @grid-ready="onGridReady" @first-data-rendered="onFirstDataRendered" @cell-key-down="onCellKeyDown" @cell-context-menu="onContextMenu" style="width:100%; height:80vh;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="header" :rowData="items"></ag-grid-vue>
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
                  <v-text-field v-model="settings.refresh" label="Refresh Rate (seconds)" :rules="[v => v == parseInt(v) && v > 0 || '']" filled hide-details></v-text-field>
                  <v-switch v-model="settings.analyze" label="Analyze scanned rows" hide-details></v-switch>
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
                <ag-grid-vue suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection suppressContextMenu preventDefaultOnContextMenu @grid-ready="onAnalyzeGridReady" @cell-key-down="onCellKeyDown" style="width:100%; height:80vh;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="single" :columnDefs="analyzeColumns" :rowData="analyzeItems"></ag-grid-vue>
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
      stopped: false,
      refreshRate: 5,
      analyze: false,
      timer: null,
      // AG Grid
      gridApi: null,
      columnApi: null,
      search: '',
      header: [],
      items: [],
      // Settings Dialog
      settingsDialog: false,
      settings: {},
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
    }
  },
  components: { AgGridVue },
  computed: {
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
      if (!value) {
        const tab = {'client': 0, 'structure': 1, 'content': 2, 'info': 3, 'objects': 6}
        this.headerTab = tab[this.headerTabSelected]
        clearTimeout(this.timer)
      }
    }
  },
  methods: {
    showDialog() {
      this.dialog = true
      this.stopped = false
      this.search = ''
      this.getSettings()
    },
    onGridReady(params) {
      this.gridApi = params.api
      this.columnApi = params.columnApi
    },
    onAnalyzeGridReady(params) {
      this.analyzeGridApi = params.api
      this.analyzeColumnApi = params.columnApi
    },
    onFirstDataRendered() {
      this.resizeTable()
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
      this.contextMenuItems = ['Analyze','Kill','|','Select All','Deselect All']
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
        if (!this.analyze) resolve()
        else this.analyzeQueries(resolve, data)
      }).then((result) => {
        // Build header
        let header = []
        if (data.length > 0) {
          let keys = Object.keys(data[0])
          for (let key of keys) header.push({ headerName: key, colId: key, field: key, sortable: true, filter: true, resizable: true, editable: false })
          if (this.analyze) header.push({ headerName: 'Scanned Rows', colId: 'scanned', field: 'scanned', sortable: true, filter: true, resizable: true, editable: false,
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
        const shouldResize = (this.analyze && !scannedIn) || (!this.analyze && scannedIn) 
        // Apply new columns
        this.header = header.slice(0)
        this.gridApi.setColumnDefs(this.header)
        if (shouldResize) this.resizeTable()
        // Build items
        if (result !== undefined) {
          for (let i = 0; i < data.length; ++i) {
            if (i in result) {
              data[i]['scanned'] = result[i].reduce((acc, val) => {
                if (val['rows'] != null) {
                  if (acc == null)  acc = val['rows']
                  else acc *= val['rows']
                }
                return acc
              }, null)
            }
            else data[i]['scanned'] = null
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
        this.timer = setTimeout(this.getProcesslist, this.refreshRate * 1000)
      })
    },
    analyzeQueries(resolve, data) {
      // Build data
      let match = {}
      let queries = []
      let database = []
      data.forEach((val, index) => {
        if (val.Info != null && (val.Info.toLowerCase().startsWith('select') || val.Info.toLowerCase().startsWith('insert') || val.Info.toLowerCase().startsWith('update') || val.Info.toLowerCase().startsWith('delete'))) {
          queries.push('EXPLAIN ' + val.Info)
          database.push(val.db)
          match[queries.length - 1] = index
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
          resolve(this.parseAnalyzer(data, match))
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else {
            let data = JSON.parse(error.response.data.data)
            resolve(this.parseAnalyzer(data, match))
          }
        })
    },
    parseAnalyzer(data, match) {
      let parsedData = {}
      for (const [i, v] of data.entries()) {
        if ('error' in v) parsedData[match[i]] = v['error']
        else parsedData[match[i]] = v['data']
      }
      return parsedData
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
    getSettings() {
      // Get processlist settings
      axios.get('/client/processlist')
        .then((response) => {
          // Get stored user values
          let data = response.data.processlist
          if (data.length != 0) {
            this.refreshRate = data[0].refresh_rate
            this.analyze = data[0].analyze_queries
          }
          // Start processlist retrieval
          this.getProcesslist()
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message, 'error')
        })
    },
    settingsProcesslist() {
      this.settings['refresh'] = this.refreshRate
      this.settings['analyze'] = this.analyze
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
        refresh_rate: this.settings['refresh'],
        analyze_queries: this.settings['analyze']
      }
      axios.put('/client/processlist', payload)
        .then((response) => {
            this.refreshRate = this.settings['refresh']
            this.analyze = this.settings['analyze']
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
      // Build analyze table
      this.analyzeDialog = true
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