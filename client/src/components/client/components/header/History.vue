<template>
  <div>
    <v-dialog v-model="dialog" max-width="80%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text"><v-icon small style="padding-right:10px; padding-bottom:2px">fas fa-history</v-icon>Query History</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn :disabled="history.length == 0" @click="clear" color="primary" style="margin-right:10px;"><v-icon small style="font-size:14px; padding-right:10px; padding-bottom:2px;">fas fa-broom</v-icon>Clear</v-btn>
          <v-btn :disabled="history.length == 0" @click="save" color="primary" style="margin-right:10px;"><v-icon small style="font-size:14px; padding-right:10px;">fas fa-arrow-down</v-icon>Export</v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="dialog = false" icon><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:0px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-text-field ref="field" v-model="search" label="Filter..." solo dense clearable hide-details></v-text-field>
                <ag-grid-vue suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection @grid-ready="onGridReady" @cell-key-down="onCellKeyDown" style="width:100%; height:70vh;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="single" :columnDefs="header" :rowData="history"></ag-grid-vue>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped src="@/styles/agGridVue.css"></style>
<style scoped>
::v-deep .v-label {
  font-size: 14px;
}
</style>

<script>
import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'
import {AgGridVue} from "ag-grid-vue";

export default {
  data() {
    return {
      dialog: false,
      // AG Grid
      gridApi: null,
      columnApi: null,
      search: '',
      header: [
        { headerName: 'Time', colId: 'time', field: 'time', sortable: true, filter: true, resizable: true, editable: false },
        { headerName: 'Connection', colId: 'connection', field: 'connection', sortable: true, filter: true, resizable: true, editable: false },
        { headerName: 'Database', colId: 'database', field: 'database', sortable: true, filter: true, resizable: true, editable: false },
        { headerName: 'Query', colId: 'query', field: 'query', sortable: true, filter: true, resizable: true, editable: false }
      ]
    }
  },
  components: { AgGridVue },
  computed: {
    ...mapFields([
      'history',
    ], { path: 'client/client' }),
    ...mapFields([
      'headerTab',
      'headerTabSelected',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('SHOW_HISTORY', this.showDialog);
  },
  watch: {
    dialog: function(value) {
      if (!value) {
        const tab = {'client': 0, 'structure': 1, 'content': 2, 'info': 3, 'objects': 6}
        this.headerTab = tab[this.headerTabSelected]
      }
    }
  },
  methods: {
    showDialog() {
      this.search = ''
      this.dialog = true
      this.resizeTable()
    },
    onGridReady(params) {
      this.gridApi = params.api
      this.columnApi = params.columnApi
      this.resizeTable()
    },
    resizeTable() {
      this.$nextTick(() => {
        if (this.gridApi != null) {
          if (this.history.length == 0) this.gridApi.sizeColumnsToFit()
          else {
            let allColIds = this.columnApi.getAllColumns().map(column => column.colId)
            this.columnApi.autoSizeColumns(allColIds)
          }
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
    clear() {
      this.history = []
    },
    save() {
      let replacer = (key, value) => value === null ? undefined : value
      let header = Object.keys(this.history[0])
      let exportData = this.history.map(row => header.map(fieldName => JSON.stringify(row[fieldName], replacer)).join(','))
      exportData.unshift(this.header.map(row => row['headerName']).join(','))
      exportData = exportData.join('\r\n')
      this.download('query_history.csv', exportData)
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
  },
}
</script>