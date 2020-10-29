<template>
  <div>
    <v-dialog v-model="dialog" max-width="90%">
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
                <ag-grid-vue suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection suppressContextMenu preventDefaultOnContextMenu @grid-ready="onGridReady" @cell-key-down="onCellKeyDown" style="width:100%; height:80vh;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="single" :columnDefs="header" :rowData="items"></ag-grid-vue>
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
                  <v-switch v-model="settings.analyze" label="Analyze SELECT queries" hide-details></v-switch>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px;">
                      <v-btn @click="settingsProcesslistSubmit" color="primary">Save</v-btn>
                    </v-col>
                    <v-col>
                      <v-btn @click="settingsDialog = false" outlined color="#e74d3c">Cancel</v-btn>
                    </v-col>
                  </v-row>
                </div>
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
      // Dialog
      dialog: false,
      stopped: false,
      refreshRate: 3,
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
      this.getProcesslist()
    },
    onGridReady(params) {
      this.gridApi = params.api
      this.columnApi = params.columnApi
      this.resizeTable()
    },
    resizeTable() {
      this.$nextTick(() => {
        if (this.gridApi != null) {
          let allColIds = this.columnApi.getAllColumns().map(column => column.colId)
          this.columnApi.autoSizeColumns(allColIds)
        }
      })
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
    onSearch(value) {
      this.gridApi.setQuickFilter(value)
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
        if (!this.analyze) { resolve(); return }
        console.log("PROMISE")
        let queries = data.reduce((acc, val) => {
          if (val.Info != null && val.Info.toLowerCase().startsWith('select')) acc.push(val.Info)
          return acc
        },[])
        if (queries.length == 0) resolve()
        else this.analyzeQueries(queries, resolve)
      }).then((result) => {
        console.log("OK")
        console.log(result)
        // Build header
        if (this.header.length == 0 && data.length > 0) {
          let keys = Object.keys(data[0])
          let header = []
          for (let key of keys) header.push({ headerName: key, colId: key, field: key, sortable: true, filter: true, resizable: true, editable: false })
          this.header = header.slice(0)
        }
        // Build items
        this.items = data
        this.gridApi.setRowData(data)
        // Resize table
        this.resizeTable()
        // Repeat processlist request
        this.timer = setTimeout(this.getProcesslist, this.refreshRate * 1000)
      })
    },
    analyzeQueries(queries, resolve) {
      const payload = {
        connection: 0,
        server: this.server.id,
        database: null,
        queries,
        executeAll: true,
      }
      axios.post('/client/execute', payload)
        .then((response) => {
          let data = JSON.parse(response.data.data)[0].data
          this.parseAnalyzer(data)
          resolve(data)
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message, 'error')
        })
    },
    parseAnalyzer(data) {
      console.log(data)
    },
    stopProcesslist() {
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
      this.refreshRate = this.settings['refresh']
      this.analyze = this.settings['analyze']
      this.settingsDialog = false
      EventBus.$emit('send-notification', 'Changes saved', '#00b16a', 1)
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
  }
}
</script>