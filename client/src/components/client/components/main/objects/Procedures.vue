<template>
  <div style="height:100%">
    <!---------------->
    <!-- PROCEDURES -->
    <!---------------->
    <ag-grid-vue ref="agGridObjectsProcedures" suppressDragLeaveHidesColumns suppressContextMenu preventDefaultOnContextMenu suppressColumnVirtualisation @grid-ready="onGridReady" @new-columns-loaded="onNewColumnsLoaded" @cell-key-down="onCellKeyDown" @cell-context-menu="onContextMenu" style="width:100%; height:calc(100% - 84px);" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" rowDeselection="true" :stopEditingWhenGridLosesFocus="true" :columnDefs="objectsHeaders.procedures" :rowData="objectsItems.procedures"></ag-grid-vue>
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
    <!---------------->
    <!-- BOTTOM BAR -->
    <!---------------->
    <div style="height:35px; background-color:#303030; border-top:2px solid #2c2c2c;">
      <v-row no-gutters style="flex-wrap: nowrap;">
        <v-col cols="auto">
          <v-btn :disabled="loading" @click="refresh" text small title="Refresh" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
        </v-col>
        <v-col cols="auto">
          <v-btn :disabled="objectsItems.procedures.length == 0" @click="exportRows" text small title="Export rows" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:13px;">fas fa-arrow-down</v-icon></v-btn>
          <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
        </v-col>
        <v-col cols="auto" class="flex-grow-1 flex-shrink-1" style="min-width: 100px; max-width: 100%; margin-top:7px; padding-left:10px; padding-right:10px;">
        </v-col>
        <v-col cols="auto" class="flex-grow-0 flex-shrink-0" style="min-width: 100px; margin-top:7px; padding-left:10px; padding-right:10px;">
          <div class="body-2" style="text-align:right;">{{ bottomBar.objects.procedures }}</div>
        </v-col>
      </v-row>
    </div>
    <!------------------->
    <!-- EXPORT DIALOG -->
    <!------------------->
    <v-dialog v-model="exportDialog" persistent max-width="50%">
      <v-card>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <div class="text-h6" style="font-weight:400;">Export Rows</div>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:20px; margin-bottom:15px;">
                  <v-select outlined v-model="exportFormat" :items="['Meteor','JSON','CSV','SQL']" label="Format" hide-details></v-select>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loading" @click="exportRowsSubmit" color="primary">Export</v-btn>
                    </v-col>
                    <v-col style="margin-bottom:10px;">
                      <v-btn :disabled="loading" @click="exportDialog = false" outlined color="#e74d3c">Cancel</v-btn>
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

<script>
import {AgGridVue} from "ag-grid-vue";
import EventBus from '../../../js/event-bus'
import { mapFields } from '../../../js/map-fields'

export default {
  data() {
    return {
      // Loading
      loading: false,
      // Export Dialog
      exportDialog: false,
      exportFormat: 'Meteor',
      // Context Menu
      contextMenu: false,
      contextMenuModel: null,
      contextMenuItems: ['Copy SQL','Copy CSV','Copy JSON','|','Select All','Deselect All'],
      contextMenuItem: {},
      contextMenuX: 0,
      contextMenuY: 0,
    }
  },
  components: { AgGridVue },
  computed: {
    ...mapFields([
      'dialogOpened',
    ], { path: 'client/client' }),
    ...mapFields([
      'headerTabSelected',
      'tabObjectsSelected',
      'objectsHeaders',
      'objectsItems',
      'server',
      'bottomBar',
    ], { path: 'client/connection' }),
    ...mapFields([
      'gridApi',
      'columnApi',
    ], { path: 'client/components' }),
  },
  watch: {
    headerTabSelected(val) {
      if (val == 'objects') {
        this.$nextTick(() => {
          if (this.gridApi.objects.procedures != null) this.resizeTable()
        })
      }
    },
    tabObjectsSelected(val) {
      if (val == 'procedures') {
        this.$nextTick(() => { this.resizeTable() })
      }
    },
    exportDialog: function(val) {
      this.dialogOpened = val
    },
  },
  methods: {
   onGridReady(params) {
      this.gridApi.objects.procedures = params.api
      this.columnApi.objects.procedures = params.columnApi
      this.$refs['agGridObjectsProcedures'].$el.addEventListener('click', this.onGridClick)
      this.gridApi.objects.procedures.showLoadingOverlay()
    },
    onNewColumnsLoaded() {
      if (this.gridApi.objects.procedures != null) this.resizeTable()
    },
    onGridClick(event) {
      if (event.target.className == 'ag-center-cols-viewport') {
        this.gridApi.objects.procedures.deselectAll()
      }
    },
    resizeTable() {
      var allColumnIds = [];
      this.columnApi.objects.procedures.getAllColumns().forEach(function(column) {
        allColumnIds.push(column.colId);
      });
      this.columnApi.objects.procedures.autoSizeColumns(allColumnIds);
    },
    onCellKeyDown(e) {
      if (e.event.key == "c" && (e.event.ctrlKey || e.event.metaKey)) {
        let selectedRows = this.gridApi.objects.procedures.getSelectedRows()
        if (selectedRows.length > 1) {
          let header = Object.keys(selectedRows[0])
          let value = selectedRows.map(row => header.map(fieldName => row[fieldName] == null ? 'NULL' : row[fieldName]).join('\t')).join('\n')
          navigator.clipboard.writeText(value)
        }
        else {
          navigator.clipboard.writeText(e.value)

          // Highlight cells
          e.event.target.classList.add('ag-cell-highlight')
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
      }
    },
    onContextMenu(e) {
      e.node.setSelected(true)
      this.contextMenuModel = null
      this.contextMenuX = e.event.clientX
      this.contextMenuY = e.event.clientY
      this.contextMenu = true
    },
    contextMenuClicked(item) {
      if (item == 'Copy SQL') this.copySQL()
      else if (item == 'Copy CSV') this.copyCSV()
      else if (item == 'Copy JSON') this.copyJSON()
      else if (item == 'Select All') this.gridApi.objects.procedures.selectAll()
      else if (item == 'Deselect All') this.gridApi.objects.procedures.deselectAll()
    },
    copySQL() {
      var SqlString = require('sqlstring');
      let selectedRows = this.gridApi.objects.procedures.getSelectedRows()
      let rawQuery = 'INSERT INTO `<table>` (' + Object.keys(selectedRows[0]).map(x => '`' + x.trim() + '`').join() + ')\nVALUES\n'
      let values = ''
      let args = []
      for (let row of selectedRows) {
        let rowVal = Object.values(row)
        args = [...args, ...rowVal];
        values += '(' + '?,'.repeat(rowVal.length).slice(0, -1) + '),\n'
      }
      rawQuery += values.slice(0,-2) + ';'
      let query = SqlString.format(rawQuery, args)
      navigator.clipboard.writeText(query)
    },
    copyCSV() {
      let selectedRows = this.gridApi.objects.procedures.getSelectedRows()
      let replacer = (key, value) => value === null ? undefined : value
      let header = Object.keys(selectedRows[0])
      let csv = selectedRows.map(row => header.map(fieldName => JSON.stringify(row[fieldName], replacer)).join(','))
      csv.unshift(header.join(','))
      csv = csv.join('\r\n')
      navigator.clipboard.writeText(csv)
    },
    copyJSON() {
      let selectedRows = this.gridApi.objects.procedures.getSelectedRows()
      let json = JSON.stringify(selectedRows)
      navigator.clipboard.writeText(json)
    },
    refresh() {
      new Promise((resolve, reject) => {
        this.loading = true
        this.gridApi.objects.procedures.showLoadingOverlay()
        EventBus.$emit('get-objects', true, resolve, reject)
      }).finally(() => {
        this.gridApi.objects.procedures.hideOverlay() 
        this.loading = false 
      })
    },
    exportRows() {
      this.exportFormat = 'Meteor'
      this.exportDialog = true
    },
    exportRowsSubmit() {
      this.loading = true
      if (this.exportFormat == 'Meteor') {
        let exportData = 'var DATA = ' + JSON.stringify(this.objectsItems.procedures) + ';\n' + 'var COLUMNS = ' + JSON.stringify(this.objectsHeaders.procedures.map(x => x.colId)) + ';'
        this.download('export.js', exportData)
      }
      else if (this.exportFormat == 'JSON') {
        let exportData = JSON.stringify(this.objectsItems.procedures)
        this.download('export.json', exportData)
      }
      else if (this.exportFormat == 'CSV') {
        let replacer = (key, value) => value === null ? undefined : value
        let header = Object.keys(this.objectsItems.procedures[0])
        let exportData = this.objectsItems.procedures.map(row => header.map(fieldName => JSON.stringify(row[fieldName], replacer)).join(','))
        exportData.unshift(header.join(','))
        exportData = exportData.join('\r\n')
        this.download('export.csv', exportData)        
      }
      else if (this.exportFormat == 'SQL') {
        var SqlString = require('sqlstring');
        let rawQuery = 'INSERT INTO `<table>` (' + this.objectsHeaders.procedures.map(x => '`' + x.colId + '`').join() + ')\nVALUES\n'
        let values = ''
        let args = []
        for (let row of this.objectsItems.procedures) {
          let rowVal = Object.values(row)
          args = [...args, ...rowVal];
          values += '(' + '?,'.repeat(rowVal.length).slice(0, -1) + '),\n'
        }
        rawQuery += values.slice(0,-2) + ';'
        let exportData = SqlString.format(rawQuery, args)
        this.download('export.sql', exportData)
      }
      this.loading = false
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