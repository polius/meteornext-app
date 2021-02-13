<template>
  <div>
    <v-dialog v-model="dialog" persistent max-width="90%">
      <v-card >
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text">Export Objects</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="tabClick('sql')" :color="sqlColor" style="margin-right:10px;">SQL</v-btn>
          <v-btn @click="tabClick('csv')" :color="csvColor" style="margin-right:10px;">CSV</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-text-field @input="onSearch" v-model="search" label="Search" append-icon="search" color="white" single-line hide-details></v-text-field>
          <v-divider class="ml-3 mr-1" inset vertical></v-divider>
          <v-btn @click="dialog = false" icon><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:5px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form @submit.prevent ref="dialogForm" style="margin-top:10px; margin-bottom:10px;">
                  <div style="padding-left:1px; padding-right:1px;">
                    <v-tabs v-model="tabObjectsSelected" show-arrows dense background-color="#303030" color="white" slider-color="white" slider-size="1" slot="extension" class="elevation-2">
                      <v-tabs-slider></v-tabs-slider>
                      <v-tab><span class="pl-2 pr-2">Tables</span></v-tab>
                      <v-divider class="mx-3" inset vertical></v-divider>
                      <v-tab v-if="tab == 'sql'"><span class="pl-2 pr-2">Views</span></v-tab>
                      <v-divider v-if="tab == 'sql'" class="mx-3" inset vertical></v-divider>
                      <v-tab v-if="tab == 'sql'"><span class="pl-2 pr-2">Triggers</span></v-tab>
                      <v-divider v-if="tab == 'sql'" class="mx-3" inset vertical></v-divider>
                      <v-tab v-if="tab == 'sql'"><span class="pl-2 pr-2">Functions</span></v-tab>
                      <v-divider v-if="tab == 'sql'" class="mx-3" inset vertical></v-divider>
                      <v-tab v-if="tab == 'sql'"><span class="pl-2 pr-2">Procedures</span></v-tab>
                      <v-divider v-if="tab == 'sql'" class="mx-3" inset vertical></v-divider>
                      <v-tab v-if="tab == 'sql'"><span class="pl-2 pr-2">Events</span></v-tab>
                      <v-divider v-if="tab == 'sql'" class="mx-3" inset vertical></v-divider>
                      <v-spacer></v-spacer>
                      <v-btn :disabled="loading" :loading="loading" @click="buildObjects()" title="Refresh" text style="font-size:16px; padding:0px; min-width:36px; height:36px; margin-top:6px; margin-right:8px;"><v-icon small>fas fa-redo-alt</v-icon></v-btn>
                    </v-tabs>
                  </div>
                  <div style="height:54vh">
                    <ag-grid-vue v-show="tabObjectsSelected == 0 && tab == 'csv'" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection @grid-ready="onGridReady('tablesCsv', $event)" @new-columns-loaded="onNewColumnsLoaded('tables')" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="single" :columnDefs="objectsHeaders.tables" :defaultColDef="defaultColDefCsv" :rowData="objectsItems.tables"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 0 && tab == 'sql'" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection @grid-ready="onGridReady('tables', $event)" @new-columns-loaded="onNewColumnsLoaded('tables')" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.tables" :defaultColDef="defaultColDef" :rowData="objectsItems.tables"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 1" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection @grid-ready="onGridReady('views', $event)" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.views" :defaultColDef="defaultColDef" :rowData="objectsItems.views"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 2" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection @grid-ready="onGridReady('triggers', $event)" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.triggers" :defaultColDef="defaultColDef" :rowData="objectsItems.triggers"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 3" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection @grid-ready="onGridReady('functions', $event)" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.functions" :defaultColDef="defaultColDef" :rowData="objectsItems.functions"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 4" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection @grid-ready="onGridReady('procedures', $event)" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.procedures" :defaultColDef="defaultColDef" :rowData="objectsItems.procedures"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 5" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection @grid-ready="onGridReady('events', $event)" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.events" :defaultColDef="defaultColDef" :rowData="objectsItems.events"></ag-grid-vue>
                  </div>
                  <v-row v-if="tab == 'sql'" no-gutters>
                    <v-col cols="auto">
                      <v-select v-model="include" @change="includeChanged" :items="includeItems" label="Include" dense outlined hide-details style="margin-top:15px; width:250px;"></v-select>
                    </v-col>
                    <v-col cols="auto" style="margin-left:10px; margin-top:4px">
                      <v-checkbox :disabled="include == 'Content'" v-model="includeDropTable" label="Include DROP syntax" hide-details></v-checkbox>
                    </v-col>
                  </v-row>
                  <v-checkbox v-else-if="tab == 'csv'" v-model="includeFields" label="Include field names in first row" hide-details style="padding:0px; margin-top:10px"></v-checkbox>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loading" @click="exportObjectsSubmit" color="primary">Export</v-btn>
                    </v-col>
                    <v-col style="margin-bottom:10px;">
                      <v-btn :disabled="loading" @click="dialog = false" outlined color="#e74d3c">Close</v-btn>
                    </v-col>
                  </v-row>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!-------------->
    <!-- PROGRESS -->
    <!-------------->
    <v-dialog v-model="dialogProgress" persistent max-width="50%">
      <v-card >
        <v-card-text style="padding:10px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-row no-gutters align="center">
                <v-col>
                  <div class="text-h6" style="font-weight:400;">Export Progress</div>
                </v-col>
                <v-col v-if="progressTimeValue != null" class="flex-grow-0 flex-shrink-0">
                  <div class="body-1">{{ progressTimeValue.format('HH:mm:ss') }}</div>
                </v-col>
              </v-row>
              <v-flex xs12>
                <div style="margin-top:10px; margin-bottom:10px;">
                  <v-progress-linear :indeterminate="progressStep == 'build'" :value="progressValue" rounded color="primary" height="25">
                    <template>
                      {{ progressValue + '%' }}
                    </template>
                  </v-progress-linear>
                  <div class="body-1" style="margin-top:10px">
                    <v-icon v-if="progressStep == 'success'" title="Finished successfully" small style="color:rgb(0, 177, 106); padding-bottom:2px;">fas fa-check-circle</v-icon>
                    <v-icon v-else-if="progressStep == 'fail'" title="Finished with errors" small style="color:rgb(231, 76, 60); padding-bottom:2px;">fas fa-times-circle</v-icon>
                    <v-icon v-else-if="progressStep == 'stop'" title="Stopped" small style="color:#fa8231; padding-bottom:2px;">fas fa-exclamation-circle</v-icon>
                    <v-progress-circular v-else indeterminate size="16" width="2" color="primary" style="margin-top:-2px"></v-progress-circular>
                    <span style="margin-left:8px">{{ progressText + ' ' + this.progressBytes }}</span>  
                  </div>
                  <v-textarea v-if="exportErrors.length > 0" readonly filled label="Errors" :value="exportErrors" height="40vh" style="margin-top:10px; margin-bottom:15px" hide-details></v-textarea>
                </div>
                <v-divider></v-divider>
                <v-row no-gutters style="margin-top:15px;">
                  <v-col v-if="['export','build'].includes(progressStep)" cols="auto" style="margin-right:5px; margin-bottom:10px;">
                    <v-btn @click="cancelExport" color="#e74c3c">Cancel</v-btn>
                  </v-col>
                  <v-col v-else style="margin-bottom:10px;">
                    <v-btn :disabled="loading" @click="dialogProgress = false" cols="auto" outlined color="#e74d3c">Close</v-btn>
                  </v-col>
                </v-row>
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
::v-deep textarea {
  color: rgba(255, 255, 255, 0.7)!important;
}
</style>

<script>
import moment from 'moment'
import {AgGridVue} from "ag-grid-vue";
import axios from 'axios'
import EventBus from '../../../js/event-bus'
import { mapFields } from '../../../js/map-fields'

export default {
  data() {
    return {
      loading: false,
      // Dialog
      dialog: false,
      search: '',
      // Tab Bar
      tab: 'sql',
      sqlColor: 'primary',
      csvColor: '#779ecb',
      tabObjectsSelected: 0,
      // AG-Grid
      gridApi: { tablesCsv: null, tables: null, views: null, triggers: null, functions: null, procedures: null, events: null },
      columnApi: { tablesCsv: null, tables: null, views: null, triggers: null, functions: null, procedures: null, events: null },
      defaultColDef: {
        flex: 1,
        minWidth: 100,
        resizable: true,
        headerCheckboxSelection: (params) => { return params.columnApi.getAllDisplayedColumns()[0] === params.column },
        checkboxSelection: (params) => { return params.columnApi.getAllDisplayedColumns()[0] === params.column },
      },
      defaultColDefCsv: {
        flex: 1,
        minWidth: 100,
        resizable: true,
        headerCheckboxSelection: false,
        checkboxSelection: (params) => { return params.columnApi.getAllDisplayedColumns()[0] === params.column },
      },
      objects: ['tables','views','triggers','functions','procedures','events'],
      // Include
      include: 'Structure + Content',
      includeItems: ['Structure + Content','Structure','Content'],
      includeDropTable: true,
      includeFields: true,
      // Progress
      dialogProgress: false,
      progressText: '', 
      progressStep: 'export', 
      progressValue: 0,
      progressBytes: 0,
      progressTimeEvent: null,
      progressTimeValue: null,
      selected: undefined,
      // Axios Cancel Token
      cancelToken: null,
      // Export Data
      exportData: [],
      exportErrors: '',
    }
  },
  components: { AgGridVue },
  computed: {
    ...mapFields([
      'dialogOpened',
    ], { path: 'client/client' }),
    ...mapFields([
      'index',
      'server',
      'database',
      'databasePrev',
      'objectsHeaders',
      'objectsItems',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('show-bottombar-objects-export', this.showDialog);
  },
  watch: {
    tabObjectsSelected: function(val) {
      if (this.tab == 'csv') this.resizeTable('tablesCsv', false)
      else if (this.tab == 'sql') this.resizeTable(this.objects[val], false)
    },
    dialog: function(val) {
      this.dialogOpened = val
    },
  },
  methods: {
    showDialog(selected) {
      this.include = 'Structure + Content'
      this.includeFields = true
      this.selected = selected
      this.dialog = true
      this.tabClick('sql')
      setTimeout(() => {
        if (this.database != this.databasePrev) this.buildObjects()
        for (let obj of this.objects) {
          if (this.gridApi[obj] != null) this.gridApi[obj].deselectAll()
        }
        if (selected === undefined) this.tabObjectsSelected = 0
        else this.selectRow()
      },100)
    },
    onGridReady(object, params) {
      this.gridApi[object] = params.api
      this.columnApi[object] = params.columnApi
    },
    onNewColumnsLoaded(object) {
      if (this.gridApi[object] != null) this.resizeTable(object, true)
    },
    selectRow() {
      if (this.selected === undefined || this.gridApi[this.selected['object']] == null) return
      this.$nextTick(() => { 
        this.tabObjectsSelected = this.objects.indexOf(this.selected['object'])
        this.gridApi[this.selected['object']].forEachNode((node) => {
          if (this.selected['items'].includes(node.data.name)) node.setSelected(true)
        })
      })
    },
    resizeTable(object, selectRow) {
      this.$nextTick(() => {
        var allColumnIds = [];
        this.columnApi[object].getAllColumns().forEach(function(column) {
          allColumnIds.push(column.colId);
        })
        this.columnApi[object].autoSizeColumns(allColumnIds);
      })
      this.$nextTick(() => {
        let obj = (object == 'tablesCsv') ? 'tables' : object 
        if (this.objectsItems[obj].length > 0) this.gridApi[obj].hideOverlay()
        else this.gridApi[obj].showNoRowsOverlay()
        if (selectRow) this.selectRow()
      })
    },
    tabClick(object) {
      if (object == 'sql') {
        this.sqlColor = 'primary'
        this.csvColor = '#779ecb'
      }
      else if (object == 'csv') {
        this.sqlColor = '#779ecb'
        this.csvColor = 'primary'
        this.resizeTable('tablesCsv', false)
      }
      this.tab = object
      this.tabObjectsSelected = 0
    },
    buildObjects() {
      for (let obj of this.objects) {
        if (this.gridApi[obj] != null) this.gridApi[obj].showLoadingOverlay()
      }
      new Promise((resolve, reject) => {
        this.loading = true
        EventBus.$emit('get-objects', true, resolve, reject)
      })
      .finally(() => {
        for (let obj of this.objects) {
          if (this.gridApi[obj] != null) this.gridApi[obj].hideOverlay()
        }
        this.loading = false
        this.databasePrev = this.database
      })
    },
    includeChanged() {
      if (this.include == 'Content') this.includeDropTable = false
    },
    exportObjectsSubmit() {
      // Get selected objects
      let objects = {'tables': [], 'views': [], 'triggers': [], 'functions': [], 'procedures': [], 'events': []}
      if (this.tab == 'sql') objects['tables'] = this.gridApi['tables'].getSelectedRows().map(x => x.name)
      else if (this.tab == 'csv') objects['tables'] = this.gridApi['tablesCsv'].getSelectedRows().map(x => x.name)
      objects['views'] = this.gridApi['views'].getSelectedRows().map(x => x.name)
      objects['triggers'] = this.gridApi['triggers'].getSelectedRows().map(x => x.name)
      objects['functions'] = this.gridApi['functions'].getSelectedRows().map(x => x.name)
      objects['procedures'] = this.gridApi['procedures'].getSelectedRows().map(x => x.name)
      objects['events'] = this.gridApi['events'].getSelectedRows().map(x => x.name)
      // Check if no objects are selected
      if (objects['tables'].length == 0 && objects['views'].length == 0 && objects['triggers'].length == 0 && objects['functions'].length == 0 && objects['procedures'].length == 0 && objects['events'].length == 0) {
        EventBus.$emit('send-notification', 'Please select at least one object to export', 'error')
        return
      }
      // Init Export
      this.loading = true
      this.progressStep = 'export'
      this.progressValue = 0
      this.exportData = []
      this.exportErrors = ''
      this.dialogProgress = true

      // Start Timer
      this.progressTimeValue = moment().startOf("day");
      this.progressTimeEvent = setInterval(() => {
        this.progressTimeValue.add(1, 'second')
      }, 1000)

      // Build Header
      if (this.tab == 'sql') {
        let header = ''
        header += '# ************************************************************\n'
        header += '# Meteor Next - Export SQL\n'
        header += '# Host: ' + this.server['hostname'] + ' (' + this.server['engine'] + ' ' + this.server['version'] + ')\n'
        header += '# Database: ' + this.database + '\n'
        header += '# Generation Time: ' + moment.utc().format("YYYY-MM-DD HH:mm:ss") + ' UTC\n'
        header += '# ************************************************************\n\n'
        header += 'SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;\n'
        header += 'SET FOREIGN_KEY_CHECKS = 0;\n\n'
        this.exportData.push(new Blob([header]))
      }

      // Export Objects
      new Promise((resolve, reject) => {
        this.exportObjects(objects, resolve, reject)
      }).then (() => {
        // Build Footer
        if (this.tab == 'sql') {
          let footer = ''
          footer += 'SET FOREIGN_KEY_CHECKS = 1;\n\n'
          if (this.exportErrors.length > 0) {
            footer += '# ************************************************************\n'
            footer += '# Export finished with errors\n'
            footer += '# ************************************************************'
          }
          else {
            footer += '# ************************************************************\n'
            footer += '# Export Finished Successfully\n'
            footer += '# ************************************************************'
          }
          this.exportData.push(new Blob([footer]))
        }
        // Download file
        this.progressStep = 'build'
        this.progressText = 'Building export file...'
        const url = window.URL.createObjectURL(new Blob(this.exportData))
        const link = document.createElement('a')
        link.setAttribute('download', 'export.sql')
        link.href = url
        document.body.appendChild(link)
        link.click()
        link.remove()
        // Update export status
        if (this.exportErrors.length == 0) {
          this.progressStep = 'success'
          this.progressText = 'Export finished successfully.'
        }
        else {
          this.progressStep = 'fail'
          this.progressText = 'Export finished with errors.'
        }
      })
      .catch(() => {})
      .finally(() => {
        clearInterval(this.progressTimeEvent)
        this.loading = false
      })
    },
    exportObjects(objects, resolve, reject) {
      var payload = {
        connection: 0,
        server: this.server.id,
        database: this.database,
        options: {
          mode: this.tab,
          include: this.include,
          includeDropTable: this.includeDropTable,
          fields: this.includeFields,
          object: '',
          items: [],
        }
      }
      const total = objects['tables'].length + objects['views'].length + objects['triggers'].length + objects['functions'].length + objects['procedures'].length + objects['events'].length
      let t = 1
      const jobs = async () => {
        for (let objSchema of ['tables','views','triggers','functions','procedures','events']) {
          const n = objects[objSchema].length
          let i = 1
          for (let objName of objects[objSchema]) {
            // Update Progress Text
            this.progressText = objSchema.charAt(0).toUpperCase() + objSchema.slice(1,-1) + ' ' + i.toString() + ' of ' + n.toString() + ' (' + objName + ').'
            // Start Object Export
            payload['options']['object'] = objSchema.slice(0, -1)
            payload['options']['items'] = [objName]
            const data = await this.exportObject(payload)
            this.exportData.push(new Blob([data]))
            // Update Progress Value
            this.progressValue = Math.round(100*t/total)
            i += 1
            t += 1
            // Check Errors
            // if (payload['options']['mode'] == 'sql' && data.split("\n")[3].startsWith('# Error: ')) {
            //   this.exportError = true
            //   if (this.exportErrors.length != 0) this.exportErrors += '\n'
            //   this.exportErrors += data.split("\n")[3].substring(9)
            // }
          }
        }
      }
      jobs()
      .then(() => resolve())
      .catch((error) => {
        if (axios.isCancel(error)) {
          this.progressStep = 'stop'
          this.progressText = 'Export interrupted by user.'
          this.error = ''
        }
        else if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
        reject()
      })
    },
    async exportObject(payload) {
      // Build options
      const CancelToken = axios.CancelToken
      this.cancelToken = CancelToken.source()
      this.progressBytes = ''
      const options = {
        cancelToken: this.cancelToken.token,
        onDownloadProgress: (progressEvent) => {
          this.progressBytes = this.parseBytes(progressEvent.loaded)
        },
        responseType: 'blob',
        params: payload,
      }
      // Execute Query
      const response = await axios.get('/client/export', options)
      return response.data
    },
    cancelExport() {
      this.cancelToken.cancel()
    },
    parseBytes(value) {
      if (value/1024 < 1) return value + ' B'
      else if (value/1024/1024 < 1) return Math.trunc(value/1024*100)/100 + ' KB'
      else if (value/1024/1024/1024 < 1) return Math.trunc(value/1024/1024*100)/100 + ' MB'
      else if (value/1024/1024/1024/1024 < 1) return Math.trunc(value/1024/1024/1024*100)/100 + ' GB'
      else return Math.trunc(value/1024/1024/1024/1024*100)/100 + ' TB' 
    },
    onSearch(value) {
      let ids = ['tablesCsv','tables','views','triggers','functions','procedures','events']
      for (let id of ids) this.gridApi[id].setQuickFilter(value)
    },
  }
}
</script>