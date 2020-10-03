<template>
  <div>
    <v-dialog v-model="dialog" persistent max-width="90%">
      <v-card >
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">Export Objects</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="tabClick('sql')" :color="sqlColor" style="margin-right:10px;">SQL</v-btn>
          <v-btn @click="tabClick('csv')" :color="csvColor" style="margin-right:10px;">CSV</v-btn>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="dialog = false" icon><v-icon>fas fa-times-circle</v-icon></v-btn>
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
                    </v-tabs>
                  </div>
                  <div style="height:55vh">
                    <ag-grid-vue v-show="tabObjectsSelected == 0 && tab == 'csv'" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection @grid-ready="onGridReady('tablesCsv', $event)" @new-columns-loaded="onNewColumnsLoaded('tables')" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="single" :columnDefs="objectsHeaders.tables" :defaultColDef="defaultColDefCsv" :rowData="objectsItems.tables"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 0 && tab == 'sql'" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection @grid-ready="onGridReady('tables', $event)" @new-columns-loaded="onNewColumnsLoaded('tables')" @row-data-changed="selectRow('views')" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.tables" :defaultColDef="defaultColDef" :rowData="objectsItems.tables"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 1" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection @grid-ready="onGridReady('views', $event)" @row-data-changed="selectRow('views')" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.views" :defaultColDef="defaultColDef" :rowData="objectsItems.views"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 2" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection @grid-ready="onGridReady('triggers', $event)" @row-data-changed="selectRow('triggers')" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.triggers" :defaultColDef="defaultColDef" :rowData="objectsItems.triggers"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 3" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection @grid-ready="onGridReady('functions', $event)" @row-data-changed="selectRow('functions')" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.functions" :defaultColDef="defaultColDef" :rowData="objectsItems.functions"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 4" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection @grid-ready="onGridReady('procedures', $event)" @row-data-changed="selectRow('procedures')" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.procedures" :defaultColDef="defaultColDef" :rowData="objectsItems.procedures"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 5" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection @grid-ready="onGridReady('events', $event)" @row-data-changed="selectRow('events')" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.events" :defaultColDef="defaultColDef" :rowData="objectsItems.events"></ag-grid-vue>
                  </div>
                  <v-select v-if="tab == 'sql'" v-model="include" :items="includeItems" label="Include" outlined hide-details style="margin-top:15px"></v-select>
                  <v-checkbox v-if="tab == 'csv'" v-model="includeFields" label="Include field names in first row" hide-details style="padding:0px; margin-top:10px"></v-checkbox>
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
              <div class="text-h6" style="font-weight:400;">Export Progress</div>
              <v-flex xs12>
                <div style="margin-top:10px; margin-bottom:10px;">
                  <v-progress-linear :indeterminate="step == 'export'" value="100" rounded color="primary" height="25">
                    <template>
                      {{ 'Exporting: ' + this.progress }}
                    </template>
                  </v-progress-linear>
                  <div class="body-1" style="margin-top:10px">
                    <v-icon v-if="step == 'success'" title="Success" small style="color:rgb(0, 177, 106); padding-bottom:2px;">fas fa-check-circle</v-icon>
                    <v-icon v-else-if="step == 'fail'" title="Failed" small style="color:rgb(231, 76, 60); padding-bottom:2px;">fas fa-times-circle</v-icon>
                    <v-icon v-else-if="step == 'stop'" title="Stopped" small style="color:#fa8231; padding-bottom:2px;">fas fa-exclamation-circle</v-icon>
                    <v-progress-circular v-else indeterminate size="16" width="2" color="primary" style="margin-top:-2px"></v-progress-circular>
                    <span style="margin-left:8px">{{ text }}</span>  
                  </div>
                  <v-card v-if="error.length != 0" style="margin-top:10px">
                    <v-card-text>
                      <div class="body-1">{{ error }}</div>
                    </v-card-text>
                  </v-card>
                </div>
                <v-divider></v-divider>
                <div v-if="step == 'export'" style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn @click="cancelExport" color="#e74c3c">Cancel</v-btn>
                    </v-col>
                    <v-col style="margin-bottom:10px;">
                      <v-btn :disabled="loading" @click="dialogProgress = false" outlined color="#e74d3c">Close</v-btn>
                    </v-col>
                  </v-row>
                </div>
                <div v-else style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loading" @click="dialogProgress = false" color="primary">Close</v-btn>
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
      // Include
      include: 'Structure + Content',
      includeItems: ['Structure + Content','Structure','Content'],
      includeFields: true,
      // Progress
      dialogProgress: false,
      text: 'Exporting objects...', 
      step: 'export', 
      progress: 0,
      error: '',
      selected: undefined,
      // Axios Cancel Token
      cancelToken: null,
    }
  },
  components: { AgGridVue },
  computed: {
    ...mapFields([
      'index',
      'server',
      'database',
      'objectsHeaders',
      'objectsItems',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('SHOW_BOTTOMBAR_OBJECTS_EXPORT', this.showDialog);
  },
  watch: {
    tabObjectsSelected: function(val) {
      let objects = ['tables','views','triggers','functions','procedures','events']
      if (this.tab == 'csv') this.resizeTable('tablesCsv')
      else if (this.tab == 'sql') this.resizeTable(objects[val])
    },
  },
  methods: {
    showDialog(selected) {
      this.selected = selected
      this.tabClick('sql')
      if (selected === undefined) this.tabObjectsSelected = 0
      this.include = 'Structure + Content'
      this.includeFields = true
      this.$nextTick(() => { this.dialog = true })
      this.$nextTick(() => { 
        if (this.gridApi['tables'] != null) this.gridApi['tables'].showLoadingOverlay()
      })
      this.$nextTick(() => { this.buildObjects() })
    },
    onGridReady(object, params) {
      this.gridApi[object] = params.api
      this.columnApi[object] = params.columnApi
      this.gridApi[object].showLoadingOverlay()
      this.selectRow(object)
    },
    onNewColumnsLoaded(object) {
      if (this.gridApi[object] != null) this.resizeTable(object)
    },
    selectRow(object) {
      if (this.selected === undefined || this.gridApi[object] == null || object != this.selected['object']) return
      let objects = ['tables','views','triggers','functions','procedures','events']
      this.$nextTick(() => { this.tabObjectsSelected = objects.indexOf(object) })
      this.$nextTick(() => {
        this.gridApi[object].forEachNode((node) => {
          if (node.data.name == this.selected['name']) node.setSelected(true)
        })
      })
    },
    resizeTable(object) {
      this.$nextTick(() => {
        var allColumnIds = [];
        this.columnApi[object].getAllColumns().forEach(function(column) {
          allColumnIds.push(column.colId);
        });
        this.columnApi[object].autoSizeColumns(allColumnIds);
      })
      let obj = (object == 'tablesCsv') ? 'tables' : object 
      if (this.objectsItems[obj].length > 0) this.gridApi[obj].hideOverlay()
      else this.gridApi[obj].showNoRowsOverlay()
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
      this.tab = object
      this.tabObjectsSelected = 0
    },
    buildObjects() {
      let promise = new Promise((resolve, reject) => {
        this.loading = true
        EventBus.$emit('GET_OBJECTS', resolve, reject)
      })
      promise.finally(() => {
        this.loading = false 
      })
    },
    exportObjectsSubmit() {
      // Get selected objects
      let tables = this.gridApi['tables'].getSelectedRows()
      let tablesCsv = this.gridApi['tablesCsv'].getSelectedRows()
      let views = this.gridApi['views'].getSelectedRows()
      let triggers = this.gridApi['triggers'].getSelectedRows()
      let functions = this.gridApi['functions'].getSelectedRows()
      let procedures = this.gridApi['procedures'].getSelectedRows()
      let events = this.gridApi['events'].getSelectedRows()
      // Check if no objects are selected
      if ((this.tab == 'sql' && tables.length == 0 && views.length == 0 && triggers.length == 0 && functions.length == 0 && procedures.length == 0 && events.length == 0) ||
        (this.tab == 'csv' && tablesCsv.length == 0)) {
        EventBus.$emit('SEND_NOTIFICATION', 'Please select at least one object to export', 'error')
        return
      }
      this.loading = true
      // Init Dialog Progress
      this.text = 'Exporting objects...'
      this.step = 'export'
      this.progress = 0
      this.error = ''
      this.dialogProgress = true
      // Build request parameters
      let objects = {}
      if (this.tab == 'csv') {
        objects['tables'] = tablesCsv.reduce((acc, curr) => { acc.push(curr['name']); return acc }, [])
      }
      else if (this.tab == 'sql') {
        objects['tables'] = tables.reduce((acc, curr) => { acc.push(curr['name']); return acc }, [])
        objects['views'] = views.reduce((acc, curr) => { acc.push(curr['name']); return acc }, [])
        objects['triggers'] = triggers.reduce((acc, curr) => { acc.push(curr['name']); return acc }, [])
        objects['functions'] = functions.reduce((acc, curr) => { acc.push(curr['name']); return acc }, [])
        objects['procedures'] = procedures.reduce((acc, curr) => { acc.push(curr['name']); return acc }, [])
        objects['events'] = events.reduce((acc, curr) => { acc.push(curr['name']); return acc }, [])
      }
      const payload = {
        connection: this.index,
        server: this.server.id,
        database: this.database,
        options: {
          mode: this.tab,
          objects: objects,
          include: this.include,
          fields: this.includeFields
        }
      }
      const CancelToken = axios.CancelToken;
      this.cancelToken = CancelToken.source();
      const options = {
        onDownloadProgress: (progressEvent) => {
          this.progress = this.parseBytes(progressEvent.loaded)
        },
        responseType: 'blob',
        cancelToken: this.cancelToken.token,
        params: payload,
      }
      // Start request
      axios.get('/client/export', options)
      .then((response) => {
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a')
        link.href = url
        if (this.tab == 'sql') link.setAttribute('download', this.database + '.sql')
        else if (this.tab == 'csv') link.setAttribute('download', objects['tables'][0] + '.csv')
        document.body.appendChild(link)
        link.click()
        link.remove()
        this.step = 'success'
        this.text = 'Objects successfully exported.'
      })
      .catch((error) => {
        if (axios.isCancel(error)) {
          this.step = 'stop'
          this.text = 'Export stopped.'
          this.error = ''
          this.loading = false
        }
        else if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
        else {
          // Convert error from 'arraybuffer' to 'json'
          let err = JSON.parse(Buffer.from(error.response.data).toString('utf8'))
          this.step = 'fail'
          this.text = 'An error occurred during the export process.'
          this.error = err.message
          this.loading = false
        }
      })
      .finally(() => { this.loading = false })
    },
    cancelExport() {
      EventBus.$emit('SEND_NOTIFICATION', 'Stopping the export process...', 'warning')
      this.cancelToken.cancel()
    },
    parseBytes(value) {
      if (value/1024 < 1) return value + ' B'
      else if (value/1024/1024 < 1) return Math.trunc(value/1024*100)/100 + ' KB'
      else if (value/1024/1024/1024 < 1) return Math.trunc(value/1024/1024*100)/100 + ' MB'
      else if (value/1024/1024/1024/1024 < 1) return Math.trunc(value/1024/1024/1024*100)/100 + ' GB'
      else return Math.trunc(value/1024/1024/1024/1024*100)/100 + ' TB' 
    },
  }
}
</script>