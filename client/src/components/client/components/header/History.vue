<template>
  <div>
    <v-dialog v-model="dialog" max-width="80%">
      <v-card>
        <v-toolbar flat dense color="primary">
          <v-toolbar-title class="white--text body-1"><v-icon small style="padding-right:10px; padding-bottom:2px">fas fa-history</v-icon>QUERY HISTORY</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn text :disabled="history.length == 0" @click="clear" style="height:100%;"><v-icon small style="font-size:14px; padding-right:10px; padding-bottom:2px;">fas fa-broom</v-icon>Clear</v-btn>
          <v-btn text :disabled="history.length == 0" @click="save" style="height:100%;"><v-icon small style="font-size:14px; padding-right:10px;">fas fa-arrow-down</v-icon>Export</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-text-field @input="onSearch" v-model="search" label="Search" append-icon="search" color="white" single-line hide-details></v-text-field>
          <v-divider class="mx-3" inset vertical style="margin-right:0px!important"></v-divider>
          <v-btn @click="dialog = false" icon style="margin-left:3px"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:0px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <ag-grid-vue suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressFieldDotNotation suppressContextMenu preventDefaultOnContextMenu oncontextmenu="return false" @grid-ready="onGridReady" @cell-key-down="onCellKeyDown" style="width:100%; height:80vh;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="single" :columnDefs="header" :rowData="history"></ag-grid-vue>
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
        { headerName: 'Section', colId: 'section', field: 'section', sortable: true, filter: true, resizable: true, editable: false, valueGetter: function(params) { return params.data.section.toUpperCase() }},
        { headerName: 'Time', colId: 'time', field: 'time', sortable: true, filter: true, resizable: true, editable: false },
        { headerName: 'Connection', colId: 'connection', field: 'connection', sortable: true, filter: true, resizable: true, editable: false },
        { headerName: 'Database', colId: 'database', field: 'database', sortable: true, filter: true, resizable: true, editable: false },
        { headerName: 'Query', colId: 'query', field: 'query', sortable: true, filter: true, resizable: true, editable: false },
        { headerName: 'Status', colId: 'status', field: 'status', sortable: true, filter: true, resizable: true, editable: false,
          cellRenderer: function(params) {
            if (params.value) return '<i class="fas fa-check-circle" title="Success" style="color:#00b16a; margin-right:8px;"></i>Success'
            else return '<i class="fas fa-times-circle" title="Failed" style="color:#EF5354; margin-right:8px;"></i>Failed'
          }
        },
        { headerName: 'Records', colId: 'records', field: 'records', sortable: true, filter: true, resizable: true, editable: false },
        { headerName: 'Elapsed', colId: 'elapsed', field: 'elapsed', sortable: true, filter: true, resizable: true, editable: false },
        { headerName: 'Error', colId: 'error', field: 'error', sortable: true, filter: true, resizable: true, editable: false },
      ]
    }
  },
  components: { AgGridVue },
  computed: {
    ...mapFields([
      'history',
      'dialogOpened',
    ], { path: 'client/client' }),
    ...mapFields([
      'headerTab',
      'headerTabSelected',
    ], { path: 'client/connection' }),
  },
  activated() {
    EventBus.$on('show-history', this.showDialog);
  },
  watch: {
    dialog: function(value) {
      this.dialogOpened = value
      if (!value) {
        const tab = {'client': 0, 'structure': 1, 'content': 2, 'info': 3, 'objects': 7}
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
            let allColIds = this.columnApi.getColumns().map(column => column.colId)
            this.columnApi.autoSizeColumns(allColIds)
          }
        }
      })
    },
    onCellKeyDown(e) {
      if (e.event.key == "c" && (e.event.ctrlKey || e.event.metaKey)) {
        let selectedRows = this.gridApi.getSelectedRows()
        if (selectedRows.length > 1) {
          // Copy values
          let header = Object.keys(selectedRows[0])
          let value = selectedRows.map(row => header.map(fieldName => row[fieldName] == null ? 'NULL' : row[fieldName]).join('\t')).join('\n')
          this.copyToClipboard(value)
          // Apply effect
          // this.gridApi.flashCells({
          //   rowNodes: this.gridApi.getSelectedNodes(),
          //   flashDelay: 200,
          //   fadeDelay: 200,
          // })
        }
        else {
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
      }
      else if (['ArrowUp','ArrowDown'].includes(e.event.key)) {
        let cell = this.gridApi.getFocusedCell()
        let row = this.gridApi.getDisplayedRowAtIndex(cell.rowIndex)
        let node = this.gridApi.getRowNode(row.id)
        this.gridApi.deselectAll()
        node.setSelected(true)
      }
    },
    onSearch(value) {
      this.gridApi.setQuickFilter(value)
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
      const a = document.createElement('a')
      a.href = URL.createObjectURL(new Blob([text]))
      a.setAttribute('download', filename)
      document.body.appendChild(a)
      a.click()
      document.body.removeChild(a)
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
  },
}
</script>