<template>
  <div>
    <v-dialog v-model="dialog" max-width="90%">
      <v-card >
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="padding-right:10px; padding-bottom:3px">fas fa-arrow-down</v-icon>EXPORT OBJECTS</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="tabClick('sql')" :color="sqlColor" style="margin-right:10px;">SQL</v-btn>
          <v-btn @click="tabClick('csv')" :color="csvColor">CSV</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="selectAll" text title="Select all" style="height:100%"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-check-square</v-icon>Select all</v-btn>
          <v-btn @click="deselectAll" text title="Deselect all" style="height:100%"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-square</v-icon>Deselect all</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-text-field @input="onSearch" v-model="search" label="Search" append-icon="search" color="white" single-line hide-details></v-text-field>
          <v-divider class="ml-3 mr-1" inset vertical></v-divider>
          <v-btn @click="dialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-card>
                  <v-row no-gutters align="center" justify="center">
                    <v-col cols="auto" style="display:flex; margin:15px">
                      <v-icon size="20" color="info">fas fa-info-circle</v-icon>
                    </v-col>
                    <v-col>
                      <div class="text-body-1" style="color:#e2e2e2">To export objects larger than 10 MB use the Utils section.</div>
                    </v-col>
                  </v-row>
                </v-card>
                <v-form @submit.prevent ref="dialogForm" style="margin-top:10px; margin-bottom:10px;">
                  <div style="padding-left:1px; padding-right:1px;">
                    <v-tabs v-model="tabObjectsSelected" show-arrows dense background-color="#303030" color="white" slider-color="white" slider-size="1" slot="extension" class="elevation-2">
                      <v-tabs-slider></v-tabs-slider>
                      <v-tab><span class="pl-2 pr-2">{{ `Tables (${objectsSelected.tables}/${objectsItems.tables.length})` }}</span></v-tab>
                      <v-divider class="mx-3" inset vertical></v-divider>
                      <v-tab v-if="tab == 'sql'"><span class="pl-2 pr-2">{{ `Views (${objectsSelected.views}/${objectsItems.views.length})` }}</span></v-tab>
                      <v-divider v-if="tab == 'sql'" class="mx-3" inset vertical></v-divider>
                      <v-tab v-if="tab == 'sql'"><span class="pl-2 pr-2">{{ `Triggers (${objectsSelected.triggers}/${objectsItems.triggers.length})` }}</span></v-tab>
                      <v-divider v-if="tab == 'sql'" class="mx-3" inset vertical></v-divider>
                      <v-tab v-if="tab == 'sql'"><span class="pl-2 pr-2">{{ `Functions (${objectsSelected.functions}/${objectsItems.functions.length})` }}</span></v-tab>
                      <v-divider v-if="tab == 'sql'" class="mx-3" inset vertical></v-divider>
                      <v-tab v-if="tab == 'sql'"><span class="pl-2 pr-2">{{ `Procedures (${objectsSelected.procedures}/${objectsItems.procedures.length})` }}</span></v-tab>
                      <v-divider v-if="tab == 'sql'" class="mx-3" inset vertical></v-divider>
                      <v-tab v-if="tab == 'sql'"><span class="pl-2 pr-2">{{ `Events (${objectsSelected.events}/${objectsItems.events.length})` }}</span></v-tab>
                      <v-divider v-if="tab == 'sql'" class="mx-3" inset vertical></v-divider>
                      <v-spacer></v-spacer>
                      <v-btn :disabled="loading" :loading="loading" @click="buildObjects()" title="Refresh" text style="font-size:16px; padding:0px; min-width:36px; height:36px; margin-top:6px; margin-right:8px;"><v-icon small>fas fa-redo-alt</v-icon></v-btn>
                    </v-tabs>
                  </div>
                  <div style="height:50vh">
                    <ag-grid-vue v-show="tabObjectsSelected == 0 && tab == 'csv'" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection oncontextmenu="return false" @grid-ready="onGridReady('tablesCsv', $event)" @selection-changed="onSelectionChanged('tablesCsv')" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="single" :columnDefs="objectsHeaders.tables" :defaultColDef="defaultColDefCsv" :rowData="objectsItems.tables"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 0 && tab == 'sql'" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection oncontextmenu="return false" @grid-ready="onGridReady('tables', $event)" @selection-changed="onSelectionChanged('tables')" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.tables" :defaultColDef="defaultColDef" :rowData="objectsItems.tables"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 1" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection oncontextmenu="return false" @grid-ready="onGridReady('views', $event)" @selection-changed="onSelectionChanged('views')" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.views" :defaultColDef="defaultColDef" :rowData="objectsItems.views"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 2" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection oncontextmenu="return false" @grid-ready="onGridReady('triggers', $event)" @selection-changed="onSelectionChanged('triggers')" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.triggers" :defaultColDef="defaultColDef" :rowData="objectsItems.triggers"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 3" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection oncontextmenu="return false" @grid-ready="onGridReady('functions', $event)" @selection-changed="onSelectionChanged('functions')" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.functions" :defaultColDef="defaultColDef" :rowData="objectsItems.functions"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 4" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection oncontextmenu="return false" @grid-ready="onGridReady('procedures', $event)" @selection-changed="onSelectionChanged('procedures')" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.procedures" :defaultColDef="defaultColDef" :rowData="objectsItems.procedures"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 5" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection oncontextmenu="return false" @grid-ready="onGridReady('events', $event)" @selection-changed="onSelectionChanged('events')" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.events" :defaultColDef="defaultColDef" :rowData="objectsItems.events"></ag-grid-vue>
                  </div>
                  <v-row v-if="tab == 'sql'" no-gutters>
                    <v-col cols="auto">
                      <v-select v-model="include" @change="includeChanged" :items="includeItems" label="Include" dense outlined hide-details style="margin-top:15px; width:250px;"></v-select>
                    </v-col>
                    <v-col cols="auto" style="margin-left:10px">
                      <v-text-field v-model="rows" outlined dense label="New INSERT statement every X rows" :rules="[v => v == parseInt(v) && v > 0 || '']" hide-details style="margin-top:15px; width:250px;"></v-text-field>
                    </v-col>
                    <v-col cols="auto" style="margin-left:10px; margin-top:4px">
                      <v-checkbox :disabled="include == 'Content'" v-model="includeDropTable" label="Include DROP syntax" hide-details></v-checkbox>
                    </v-col>
                    <v-col cols="auto" style="margin-left:15px; margin-top:4px">
                      <v-checkbox :disabled="include == 'Content'" v-model="includeDelimiters" label="Include DELIMITERs" hide-details></v-checkbox>
                    </v-col>
                  </v-row>
                  <v-checkbox v-else-if="tab == 'csv'" v-model="includeFields" label="Include field names in first row" hide-details style="padding:0px; margin-top:10px"></v-checkbox>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px">
                      <v-btn :loading="loading" @click="exportObjectsSubmit" color="#00b16a">Export</v-btn>
                    </v-col>
                    <v-col>
                      <v-btn :disabled="loading" @click="dialog = false" color="#EF5354">Cancel</v-btn>
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
                <!-- <v-col v-if="progressTimeValue != null" class="flex-grow-0 flex-shrink-0">
                  <div class="body-1">{{ progressTimeValue.format('HH:mm:ss') }}</div>
                </v-col> -->
              </v-row>
              <v-flex xs12>
                <div style="margin-top:10px; margin-bottom:10px;">
                  <v-progress-linear :value="progressValue" rounded color="primary" height="25">
                    <template>
                      {{ progressValue + '%' }}
                    </template>
                  </v-progress-linear>
                  <div class="body-1" style="margin-top:10px">
                    <v-icon v-if="progressStep == 'success'" title="Finished successfully" small style="color:rgb(0, 177, 106); padding-bottom:2px;">fas fa-check-circle</v-icon>
                    <v-icon v-else-if="progressStep == 'fail'" title="Finished with errors" small style="color:#EF5354; padding-bottom:2px;">fas fa-times-circle</v-icon>
                    <v-icon v-else-if="progressStep == 'stop'" title="Stopped" small style="color:#fa8231; padding-bottom:2px;">fas fa-exclamation-circle</v-icon>
                    <v-progress-circular v-else indeterminate size="16" width="2" color="primary" style="margin-top:-2px"></v-progress-circular>
                    <span style="margin-left:8px">{{ progressStep == 'export' ? progressText + (progressBytes == 0 ? ' Fetching data... ' : ' Downloading data... [' + this.progressBytes + ' / ' + this.progressTotal + ']') : progressText }}</span>  
                  </div>
                  <v-textarea v-if="exportErrors.length > 0" readonly filled label="Errors" :value="exportErrors" height="40vh" style="margin-top:10px; margin-bottom:15px" hide-details></v-textarea>
                </div>
                <v-divider></v-divider>
                <v-row no-gutters style="margin-top:15px;">
                  <v-col v-if="progressStep == 'export'" cols="auto" style="margin-right:5px; margin-bottom:10px;">
                    <v-btn @click="cancelExport" color="#EF5354">Cancel</v-btn>
                  </v-col>
                  <v-col v-else style="margin-bottom:10px;">
                    <v-btn :disabled="loading" @click="closeExport" cols="auto" color="primary">Close</v-btn>
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
      objectsSelected: {'tables':0,'views':0,'triggers':0,'functions':0,'procedures':0,'events':0},
      // Include
      include: 'Structure + Content',
      rows: '1000',
      includeItems: ['Structure + Content','Structure','Content'],
      includeDropTable: true,
      includeDelimiters: false,
      includeFields: true,
      // Progress
      dialogProgress: false,
      progressText: '', 
      progressStep: 'export', 
      progressValue: 0,
      progressBytes: 0,
      progressTotal: 0,
      progressTimeEvent: null,
      progressTimeValue: null,
      // Axios Abort Controller
      abortController: null,
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
      'id',
      'server',
      'database',
      'objectsHeaders',
      'objectsItems',
    ], { path: 'client/connection' }),
  },
  activated() {
    EventBus.$on('show-bottombar-objects-export', this.showDialog);
  },
  watch: {
    tabObjectsSelected: function(val) {
      if (this.tab == 'csv') this.resizeTable('tablesCsv')
      else if (this.tab == 'sql') this.resizeTable(this.objects[val])
    },
    dialog: function(val) {
      this.dialogOpened = val
    },
  },
  methods: {
    showDialog(data) {
      this.include = 'Structure + Content'
      this.rows = '1000'
      this.search = ''
      this.onSearch('')
      this.includeFields = true
      this.dialog = true
      this.tabClick('sql')
      setTimeout(() => {
        this.buildObjects(data)
        for (let obj of this.objects) {
          if (this.gridApi[obj] != null) this.gridApi[obj].deselectAll()
        }
        if (data !== undefined) {
          const match = {'tables':0,'views':1,'triggers':2,'functions':3,'procedures':4,'events':5}
          this.tabObjectsSelected = match[data['object']]
        }
        else this.tabObjectsSelected = 0
      },0)
    },
    onGridReady(object, params) {
      setTimeout(() => {
        this.gridApi[object] = params.api
        this.columnApi[object] = params.columnApi
        this.gridApi[object].showLoadingOverlay()
      },0)
    },
    onSelectionChanged(object) {
      if (object == 'tablesCsv') this.objectsSelected['tables'] = this.gridApi[object].getSelectedRows().length
      else this.objectsSelected[object] = this.gridApi[object].getSelectedRows().length
    },
    selectAll() {
      const objects = (this.tab == 'sql') ? ['tables','views','triggers','functions','procedures','events'] : ['tablesCsv']
      for (let obj of objects) try { this.gridApi[obj].selectAll() } catch {} // eslint-disable-line
    },
    deselectAll() {
      const objects = (this.tab == 'sql') ? ['tables','views','triggers','functions','procedures','events'] : ['tablesCsv']
      for (let obj of objects) try { this.gridApi[obj].deselectAll() } catch {} // eslint-disable-line
    },
    resizeTable(object) {
      setTimeout(() => {
        if (this.columnApi[object] == null) return
        var allColumnIds = []
        this.columnApi[object].getColumns().forEach(function(column) {
          allColumnIds.push(column.colId)
        })
        this.columnApi[object].autoSizeColumns(allColumnIds)
        this.gridApi[object].hideOverlay()
      },0)
    },
    tabClick(object) {
      if (object == 'sql') {
        this.sqlColor = 'primary'
        this.csvColor = '#779ecb'
      }
      else if (object == 'csv') {
        this.sqlColor = '#779ecb'
        this.csvColor = 'primary'
        this.resizeTable('tablesCsv')
      }
      // Deselect all rows
      const objects = ['tables','tablesCsv','views','triggers','functions','procedures','events']
      for (let obj of objects) try { this.gridApi[obj].deselectAll() } catch {} // eslint-disable-line
      // Change tab
      this.tab = object
      this.tabObjectsSelected = 0
    },
    buildObjects(data) {
      for (let obj of this.objects) {
        if (this.gridApi[obj] != null) this.gridApi[obj].showLoadingOverlay()
      }
      new Promise((resolve, reject) => {
        this.loading = true
        EventBus.$emit('get-objects', true, resolve, reject)
      })
      .then(() => {
        this.objectsSelected = {'tables':0,'views':0,'triggers':0,'functions':0,'procedures':0,'events':0}
        for (let obj of this.objects) this.resizeTable(obj)
        if (data !== undefined) this.selectRows(data)
      })
      .finally(() => this.loading = false)
    },
    selectRows(data) {
      this.gridApi[data['object']].forEachNode(node => {
        if (data['items'].includes(node.data.name)) node.setSelected(true)
      })
    },
    includeChanged() {
      if (this.include == 'Content') {
        this.includeDropTable = false
        this.includeDelimiters = false
      }
    },
    exportObjectsSubmit() {
      // Check if all fields are filled
      if (!this.$refs.dialogForm.validate()) {
        EventBus.$emit('send-notification', 'Please make sure all required fields are filled out correctly', '#EF5354')
        return
      }
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
        EventBus.$emit('send-notification', 'Please select at least one object to export', '#EF5354')
        return
      }
      // Limit export size
      if (['Structure + Content','Content'].includes(this.include)) {
        for (let i of this.gridApi['tables'].getSelectedRows()) {
          if (i['data_length']/1024/1024 > 10) {
            EventBus.$emit('send-notification', 'To export objects larger than 10 MB use the Utils section.', '#EF5354')
            return
          }
        }
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
      this.progressTimeEvent = setInterval(() => requestAnimationFrame(() => this.progressTimeValue.add(1, 'second')), 1000)

      // Build Header
      if (this.tab == 'sql') {
        let header = ''
        header += "# ************************************************************\n"
        header += "# Meteor Next - Export SQL\n"
        header += "# Host: " + this.server['hostname'] + " (" + this.server['engine'] + " " + this.server['version'] + ")\n"
        header += "# Database: " + this.database + "\n"
        header += "# Generation Time: " + moment.utc().format('YYYY-MM-DD HH:mm:ss') + " UTC\n"
        header += "# ************************************************************\n\n"
        header += "SET NAMES utf8mb4 COLLATE utf8mb4_unicode_ci;\n"
        header += "SET @OLD_TIME_ZONE=@@TIME_ZONE, TIME_ZONE='+00:00';\n"
        header += "SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0;\n"
        header += "SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0;\n"
        header += "SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO';\n"
        header += "SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0;\n\n"
        this.exportData = new Blob([header])
      }

      // Export Objects
      new Promise((resolve, reject) => {
        this.exportObjects(objects, resolve, reject)
      }).then (() => {
        // Build Footer
        if (this.tab == 'sql') {
          let footer = ""
          footer += "SET TIME_ZONE=@OLD_TIME_ZONE;\n"
          footer += "SET SQL_MODE=@OLD_SQL_MODE;\n"
          footer += "SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS;\n"
          footer += "SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS;\n"
          footer += "SET SQL_NOTES=@OLD_SQL_NOTES;\n\n"
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
          this.exportData = new Blob([this.exportData, footer])
        }
        // Download file
        const url = window.URL.createObjectURL(this.exportData)
        const link = document.createElement('a')
        const name = (this.tab == 'sql') ? this.database : objects['tables'][0]
        const extension = (this.tab == 'sql') ? 'sql' : 'csv'
        link.setAttribute('download', name + '.' + extension)
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
        connection: this.id + '-shared',
        server: this.server.id,
        engine: this.server.engine,
        database: this.database,
        mode: this.tab,
        include: this.include,
        rows: this.rows,
        includeDropTable: this.includeDropTable,
        includeDelimiters: this.includeDelimiters,
        includeFields: this.includeFields,
        object: '',
        items: [],
      }
      let total = objects['tables'].length
      if (payload['mode'] == 'sql') total += objects['views'].length + objects['triggers'].length + objects['functions'].length + objects['procedures'].length + objects['events'].length
      let t = 1
      const jobs = async () => {
        let objectsType = (payload['mode'] == 'csv') ? ['tables'] : ['tables','views','triggers','functions','procedures','events']
        for (let objSchema of objectsType) {
          const n = objects[objSchema].length
          let i = 1
          for (let objName of objects[objSchema]) {
            // Start Object Export
            payload['object'] = objSchema.slice(0, -1)
            payload['items'] = JSON.stringify([objName])
            this.progressText = objSchema.charAt(0).toUpperCase() + objSchema.slice(1,-1) + ' ' + i.toString() + ' of ' + n.toString() + ' (' + objName + ').'
            const data = await this.exportObject(payload)
            this.exportData = new Blob([this.exportData, data])
            // Check Errors
            let dataSlice = await data.slice(0, 1024).text()
            if (payload['mode'] == 'sql' && dataSlice.split("\n")[3].startsWith('# Error: ')) {
              if (this.exportErrors.length != 0) this.exportErrors += '\n'
              this.exportErrors += dataSlice.split("\n")[3].substring(9)
            }
            // Update Progress Value
            this.progressValue = Math.round(100*t/total)
            i += 1
            t += 1
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
        else if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
        reject()
      })
    },
    async exportObject(payload) {
      // Build options
      this.abortController = new AbortController()
      this.progressBytes = 0
      this.progressTotal = 0
      const options = {
        signal: this.abortController.signal,
        onDownloadProgress: (progressEvent) => {
          this.progressBytes = this.parseBytes(progressEvent.loaded)
          this.progressTotal = this.parseBytes(progressEvent.total)
        },
        responseType: 'blob',
        params: payload,
      }
      // Execute Query
      const response = await axios.get('/client/export', options)
      return response.data
    },
    cancelExport() {
      this.abortController.abort()
    },
    closeExport() {
      this.dialogProgress = false
      this.dialog = false
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
      for (let id of ids) {
        if (this.gridApi[id] != null) this.gridApi[id].setQuickFilter(value)
      }
    },
  }
}
</script>