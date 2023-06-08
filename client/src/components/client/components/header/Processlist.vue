<template>
  <div>
    <v-dialog v-model="dialog" fullscreen max-width="100%" transition="fade-transition">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="padding-right:10px; padding-bottom:2px">fas fa-server</v-icon>PROCESSLIST</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <div class="body-1" :title="server.shared ? server.secured ? 'Shared (Secured)' : 'Shared' : server.secured ? 'Personal (Secured)' : 'Personal'">{{ server.name }}</div>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn text @click="settingsProcesslist" style="height:100%"><v-icon small style="padding-right:10px; font-size:14px;">fas fa-cog</v-icon>Settings</v-btn>
          <v-btn text @click="exportProcesslist" style="height:100%"><v-icon small style="padding-right:10px">fas fa-arrow-down</v-icon>Export</v-btn>
          <v-btn text @click="stopProcesslist" :title="stopped ? 'Start processlist retrieval' : 'Stop processlist retrieval'" style="height:100%"><v-icon small style="padding-right:10px">{{ stopped ? 'fas fa-play' : 'fas fa-stop'}}</v-icon>{{ stopped ? 'START' : 'STOP' }}</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <div><span class="body-1 font-weight-medium">{{ rowCount }}</span><span class="body-1"> Connection(s)</span></div>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-text-field @input="onSearch" v-model="search" label="Search" color="white" append-icon="search" single-line hide-details></v-text-field>
          <v-divider class="mx-3" inset vertical style="margin-right:0px!important"></v-divider>
          <v-btn @click="dialog = false" icon style="margin-left:3px;"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:0px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <ag-grid-vue suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressFieldDotNotation suppressContextMenu preventDefaultOnContextMenu oncontextmenu="return false" @grid-ready="onGridReady" @first-data-rendered="onFirstDataRendered" @cell-key-down="onCellKeyDown" @cell-context-menu="onContextMenu" style="width:100%; height:calc(100vh - 48px);" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="header" :rowData="items"></ag-grid-vue>
                <v-menu v-model="contextMenu" :position-x="contextMenuX" :position-y="contextMenuY" absolute offset-y style="z-index:10">
                  <v-list style="padding:0px;">
                    <v-list-item-group v-model="contextMenuModel">
                      <div v-for="[index, item] of contextMenuItems.entries()" :key="index">
                        <v-list-item :disabled="contextMenuDisabled(item)" v-if="item != '|'" @click="contextMenuClicked(item)">
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
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="padding-right:10px; padding-bottom:2px">fas fa-cog</v-icon>SETTINGS</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="settingsDialog = false"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-bottom:15px;">
                  <v-text-field v-model="settingsItem.refresh_rate" label="Refresh Rate (seconds)" :rules="[v => v == parseInt(v) && v > 0 || '']" filled hide-details></v-text-field>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px;">
                      <v-btn :loading="loading" :disabled="loading" @click="settingsProcesslistSubmit" color="#00b16a">Confirm</v-btn>
                    </v-col>
                    <v-col>
                      <v-btn :disabled="loading" @click="settingsDialog = false" color="#EF5354">Cancel</v-btn>
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
    <v-dialog v-model="killDialog" :persistent="loading" max-width="50%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1">KILL QUERIES</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="killDialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-bottom:15px">
                  <div class="body-1">Are you sure you want to kill the selected queries?</div>
                  <v-checkbox v-model="killDialogCheckbox" label="Terminate the connection" hide-details style="margin-top:15px;"></v-checkbox>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px">
                      <v-btn :loading="loading" @click="killQuerySubmit" color="#00b16a">Confirm</v-btn>
                    </v-col>
                    <v-col>
                      <v-btn :disabled="loading" @click="killDialog = false" color="#EF5354">Cancel</v-btn>
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
    <!-- Explain Dialog -->
    <!-------------------->
    <v-dialog v-model="explainDialog" max-width="100%" fullscreen>
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="padding-right:10px; padding-bottom:3px">fas fa-chart-pie</v-icon>EXPLAIN QUERY</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn @click="explainDialog = false" icon style="margin-left:5px"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:0px">
          <v-container style="padding:0px; max-width:100%">
            <v-layout wrap>
              <v-flex xs12>
                <Splitpanes horizontal @ready="initAceClient()" style="height:calc(100vh - 48px)">
                  <Pane size="50">
                    <div id="explainEditor" style="float:left; height:100%; width:100%"></div>
                  </Pane>
                  <Pane size="50" min-size="0">
                    <ag-grid-vue suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressFieldDotNotation suppressContextMenu preventDefaultOnContextMenu oncontextmenu="return false" @grid-ready="onExplainGridReady" @cell-key-down="onCellKeyDown" @first-data-rendered="onFirstExplainDataRendered" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="single" :columnDefs="explainColumns" :rowData="explainItems"></ag-grid-vue>
                  </Pane>
                </Splitpanes>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!-------------->
    <!-- Snackbar -->
    <!-------------->
    <v-snackbar v-model="snackbar" :multi-line="false" timeout=1000 :color="snackbarColor" bottom style="padding-top:0px;">
      <div style="text-align:center">{{ snackbarText }}</div>
    </v-snackbar>
  </div>
</template>

<style scoped src="@/styles/agGridVue.css"></style>

<style scoped>
  ::v-deep .v-list-item__title {
  font-size: 0.9rem;
}
::v-deep .v-list-item__content {
  padding:0px;
}
::v-deep .v-list-item {
  min-height:40px;
}
</style>

<script>
import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'
import sqlFormatter from '@sqltools/formatter'

import {AgGridVue} from "ag-grid-vue"

import ace from "ace-builds"
import 'ace-builds/webpack-resolver'
import 'ace-builds/src-noconflict/ext-language_tools'

import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'

import axios from 'axios'

export default {
  data() {
    return {
      loading: false,
      // Dialog
      dialog: false,
      stopped: true,
      timer: null,
      // AG Grid
      gridApi: null,
      columnApi: null,
      search: '',
      header: [],
      items: [],
      selected: [],
      rowCount: 0,
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
      // Explain Dialog
      explainDialog: false,
      explainGridApi: null,
      explainColumnApi: null,
      explainColumns: [],
      explainItems: [],
      explainEditor: null,
      // Snackbar
      snackbar: false,
      snackbarText: '',
      snackbarColor: '',
    }
  },
  components: { Splitpanes, Pane, AgGridVue },
  computed: {
    ...mapFields([
      'settings',
      'dialogOpened',
    ], { path: 'client/client' }),
    ...mapFields([
      'headerTab',
      'headerTabSelected',
      'server',
      'id',
    ], { path: 'client/connection' }),
  },
  activated() {
    EventBus.$on('show-processlist', this.showDialog);
  },
  watch: {
    dialog: function(value) {
      this.dialogOpened = value
      if (!value) {
        const tab = {'client': 0, 'structure': 1, 'content': 2, 'info': 3, 'objects': 7}
        this.headerTab = tab[this.headerTabSelected]
        clearTimeout(this.timer)
      }
      else if (this.gridApi != null) this.gridApi.showLoadingOverlay()
    },
    explainDialog: function(value) {
      if (!value) return
      if (this.explainEditor != null) {
        let sqlFormatted = sqlFormatter.format(this.selected[0].Info, { reservedWordCase: 'upper', linesBetweenQueries: 2 })
        this.explainEditor.setValue(sqlFormatted, -1)
      }
      if (this.explainGridApi != null) {
        this.$nextTick(() => {
          let allColumnIds = this.explainColumnApi.getColumns().map(v => v.colId)
          this.explainColumnApi.autoSizeColumns(allColumnIds)
        })
      }
    }
  },
  methods: {
    showDialog() {
      this.items = []
      this.search = ''
      this.dialog = true
      this.stopped = false
      this.onSearch('')
      this.getProcesslist()
    },
    onGridReady(params) {
      this.gridApi = params.api
      this.columnApi = params.columnApi
      this.gridApi.showLoadingOverlay()
    },
    onExplainGridReady(params) {
      this.explainGridApi = params.api
      this.explainColumnApi = params.columnApi
    },
    onFirstDataRendered() {
      this.resizeTable()
    },
    onFirstExplainDataRendered() {
      if (this.explainGridApi != null) {
        // this.explainGridApi.sizeColumnsToFit()
        let allColumnIds = this.explainColumnApi.getColumns().map(v => v.colId)
        this.explainColumnApi.autoSizeColumns(allColumnIds)
      }
    },
    resizeTable() {
      if (this.gridApi != null) {
        let allColumnIds = this.columnApi.getColumns().map(v => v.colId)
        this.columnApi.autoSizeColumns(allColumnIds)
      }
    },
    onCellKeyDown(e) {
      if (e.event.key == "c" && (e.event.ctrlKey || e.event.metaKey)) {
        // Copy value
        this.copyToClipboard(e.value).then(() => {
          // Apply effect
          this.gridApi.flashCells({
            rowNodes: this.gridApi.getSelectedNodes(),
            columns: [this.gridApi.getFocusedCell().column.colId],
            flashDelay: 200,
            fadeDelay: 200,
          })
        })
      }
      else if (e.event.key == 'Backspace' && e.event.metaKey) this.killQuery()
      else if (['ArrowUp','ArrowDown'].includes(e.event.key)) {
        let cell = this.gridApi.getFocusedCell()
        let row = this.gridApi.getDisplayedRowAtIndex(cell.rowIndex)
        let node = this.gridApi.getRowNode(row.id)
        this.gridApi.deselectAll()
        node.setSelected(true)
      }
    },
    onContextMenu(e) {
      if (!this.gridApi.getSelectedNodes().some(x => x.id == e.node.id)) this.gridApi.deselectAll()
      e.node.setSelected(true)
      this.selected = this.gridApi.getSelectedRows()
      this.contextMenuModel = null
      this.contextMenuX = e.event.clientX
      this.contextMenuY = e.event.clientY
      this.contextMenuItems = ['Explain','Kill','|','Select All','Deselect All']
      this.contextMenu = true
    },
    contextMenuDisabled(item) {
      if (item == 'Explain' && this.selected.length > 1) return true
      return false
    },
    contextMenuClicked(item) {
      if (item == 'Explain') this.explainQuery()
      else if (item == 'Kill') this.killQuery()
      else if (item == 'Select All') this.gridApi.selectAll()
      else if (item == 'Deselect All') this.gridApi.deselectAll()
    },
    onSearch(value) {
      if (this.gridApi != null) {
        this.gridApi.setQuickFilter(value)
        this.rowCount = this.gridApi.getDisplayedRowCount()
      }
    },
    getProcesslist() {
      if (this.stopped || !this.dialog) { clearTimeout(this.timer); return }
      else if (this.gridApi == null) {
        clearTimeout(this.timer)
        this.timer = setTimeout(this.getProcesslist, 1000)
        return
      }
      const payload = {
        connection: this.id + '-shared',
        server: this.server.id
      }
      axios.get('/client/processlist', { params: payload })
        .then((response) => {
          this.parseProcesslist(response.data.processlist)
          this.gridApi.hideOverlay()
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    parseProcesslist(data) {
      // Build header
      let header_fields = ['ID', 'USER', 'HOST', 'DB', 'COMMAND', 'TIME', 'STATE', 'INFO']
      this.header = header_fields.map(x => ({"headerName": x, "colId": x, "field": x, "sortable": true, "filter": true, "resizable": true, "editable": false}))
      // Apply new columns
      this.gridApi.setColumnDefs(this.header)
      // Preserve selected / filtered nodes
      const selectedNodes = this.gridApi.getSelectedNodes().map(node => node.data.ID)
      const filterModel = this.gridApi.getFilterModel()
      // Reload new items
      this.items = data
      this.gridApi.setRowData(data)
      if (this.search.length == 0) this.rowCount = this.items.length
      // Apply selected / filtered nodes
      this.$nextTick(() => {
        this.gridApi.forEachNode((node) => node.setSelected(selectedNodes.includes(node.data.ID)))
        this.gridApi.setFilterModel(filterModel)
      })
      // Repeat processlist request
      clearTimeout(this.timer)
      this.timer = setTimeout(this.getProcesslist, (this.settings['refresh_rate'] || 5) * 1000)
    },
    stopProcesslist() {
      this.stopped = !this.stopped
      if (!this.stopped) {
        this.snackbarText = 'Processlist started'
        this.snackbarColor = '#00b16a'
        clearTimeout(this.timer)
        this.getProcesslist()
      }
      else {
        this.snackbarText = 'Processlist stopped'
        this.snackbarColor = '#00b16a'
        clearTimeout(this.timer)
      }
      this.snackbar = true
    },
    exportProcesslist() {
      let replacer = (key, value) => value === null ? undefined : value
      let header = Object.keys(this.items[0])
      let exportData = this.items.map(row => header.map(fieldName => JSON.stringify(row[fieldName], replacer)).join(','))
      exportData.unshift(this.header.map(row => row['headerName']).join(','))
      exportData = exportData.join('\r\n')
      this.download(this.server.name + '.csv', exportData)
    },
    settingsProcesslist() {
      this.settingsItem.refresh_rate = this.settings['refresh_rate'] || 5
      this.settingsDialog = true
    },
    settingsProcesslistSubmit() {
      // Check if all required fields are filled
      if (!this.$refs.form.validate()) {
        EventBus.$emit('send-notification', 'Please make sure all required fields are filled out correctly', '#EF5354')
        return
      }
      this.loading = true
      const payload = { refresh_rate: this.settingsItem['refresh_rate'] }
      axios.put('/client/settings', payload)
        .then((response) => {
          this.settings['refresh_rate'] = payload.refresh_rate
          this.settingsDialog = false
          EventBus.$emit('send-notification', response.data.message, '#00b16a', 1)
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    download(filename, text) {
      const a = document.createElement('a')
      a.href = URL.createObjectURL(new Blob([text]))
      a.setAttribute('download', filename)
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
    },
    initAceClient() {
      this.explainEditor = ace.edit("explainEditor", {
        mode: "ace/mode/mysql",
        theme: "ace/theme/monokai",
        keyboardHandler: "ace/keyboard/vscode",
        fontSize: 14,
        showPrintMargin: false,
        wrap: false,
        readOnly: true,
        showLineNumbers: true
      })
      this.explainEditor.container.addEventListener("keydown", (e) => {
        // - Increase Font Size -
        if (e.key.toLowerCase() == "+" && (e.ctrlKey || e.metaKey)) {
          let size = parseInt(this.explainEditor.getFontSize(), 10) || 12
          this.explainEditor.setFontSize(size + 1)
          e.preventDefault()
        }
        // - Decrease Font Size -
        else if (e.key.toLowerCase() == "-" && (e.ctrlKey || e.metaKey)) {
          let size = parseInt(this.explainEditor.getFontSize(), 10) || 12
          this.explainEditor.setFontSize(Math.max(size - 1 || 1))
          e.preventDefault()
        }
      }, false)
      let sqlFormatted = sqlFormatter.format(this.selected[0].Info, { reservedWordCase: 'upper', linesBetweenQueries: 2 })
      this.explainEditor.setValue(sqlFormatted, -1)
    },
    explainQuery() {
      const selectedQuery = this.selected.map(x => x.Info)[0]
      const selectedDatabase = this.selected.map(x => x.db)[0]
      let payload = {
        connection: this.id + '-shared2',
        server: this.server.id,
        query: selectedQuery.trim()
      }
      if (selectedDatabase != null) payload['database'] = selectedDatabase
      axios.get('/client/explain', { params: payload })
      .then((response) => {
        this.parseExplain(response.data.explain)
      })
      .catch((error) => {
        if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
        else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
      })
    },
    parseExplain(data) {
      this.explainColumns = Object.keys(data[0]).map(key => ({ headerName: key, colId: key, field: key, sortable: true, filter: true, resizable: true, editable: false }))
      this.explainItems = data
      this.explainDialog = true
    },
    killQuery() {
      this.killDialogCheckbox = false
      this.killDialog = true
    },
    killQuerySubmit() {
      // Build queries
      let queries = this.selected.map(x => x.Id)
      if (this.server.engine == 'Amazon Aurora (MySQL)') {
        if (this.killDialogCheckbox) queries = queries.map(x => 'CALL mysql.rds_kill(' + x + ')')
        else queries = queries.map(x => 'CALL mysql.rds_kill_query(' + x + ')')
      }
      else {
        if (this.killDialogCheckbox) queries = queries.map(x => 'KILL ' + x)
        else queries = queries.map(x => 'KILL QUERY ' + x)
      } 
      // Build payload
      const payload = {
        origin: 'processlist',
        connection: this.id + '-shared2',
        server: this.server.id,
        database: null,
        queries,
        executeAll: true,
      }
      this.loading = true
      // Kill queries
      axios.post('/client/execute', payload)
        .then(() => {
            EventBus.$emit('send-notification', 'Queries killed', '#00b16a', 2)
          })
          .catch((error) => {
            if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
            else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
          })
          .finally(() => { this.loading = false; this.killDialog = false })
    },
    copyToClipboard(textToCopy) {
      if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(textToCopy)
      else {
        let textArea = document.createElement("textarea")
        textArea.value = textToCopy
        textArea.style.position = "absolute"
        textArea.style.opacity = 0
        document.body.appendChild(textArea)
        textArea.select()
        return new Promise((res, rej) => {
          document.execCommand('copy') ? res() : rej()
          textArea.remove()
        })
      }
    },
  }
}
</script>