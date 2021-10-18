<template>
  <div>
    <v-dialog v-model="dialog" max-width="90%">
      <v-card >
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="padding-right:10px; padding-bottom:3px">fas fa-clone</v-icon>CLONE OBJECTS</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="selectAll" text title="Select all" style="height:100%"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-check-square</v-icon>Select all</v-btn>
          <v-btn @click="deselectAll" text title="Deselect all" style="height:100%"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-square</v-icon>Deselect all</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-text-field @input="onSearch" v-model="search" label="Search" append-icon="search" color="white" single-line hide-details></v-text-field>
          <v-divider class="ml-3 mr-1" inset vertical></v-divider>
          <v-btn @click="dialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:5px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form @submit.prevent ref="dialogForm" style="margin-top:10px; margin-bottom:10px;">
                  <div style="padding-left:1px; padding-right:1px;">
                    <v-tabs v-model="tabObjectsSelected" show-arrows dense background-color="#303030" color="white" slider-color="white" slider-size="1" slot="extension" class="elevation-2">
                      <v-tabs-slider></v-tabs-slider>
                      <v-tab><span class="pl-2 pr-2">{{ `Tables (${objectsSelected.tables}/${objectsItems.tables.length})` }}</span></v-tab>
                      <v-divider class="mx-3" inset vertical></v-divider>
                      <v-tab><span class="pl-2 pr-2">{{ `Views (${objectsSelected.views}/${objectsItems.views.length})` }}</span></v-tab>
                      <v-divider class="mx-3" inset vertical></v-divider>
                      <v-tab><span class="pl-2 pr-2">{{ `Triggers (${objectsSelected.triggers}/${objectsItems.triggers.length})` }}</span></v-tab>
                      <v-divider class="mx-3" inset vertical></v-divider>
                      <v-tab><span class="pl-2 pr-2">{{ `Functions (${objectsSelected.functions}/${objectsItems.functions.length})` }}</span></v-tab>
                      <v-divider class="mx-3" inset vertical></v-divider>
                      <v-tab><span class="pl-2 pr-2">{{ `Procedures (${objectsSelected.procedures}/${objectsItems.procedures.length})` }}</span></v-tab>
                      <v-divider class="mx-3" inset vertical></v-divider>
                      <v-tab><span class="pl-2 pr-2">{{ `Events (${objectsSelected.events}/${objectsItems.events.length})` }}</span></v-tab>
                      <v-divider class="mx-3" inset vertical></v-divider>
                      <v-spacer></v-spacer>
                      <v-btn :disabled="loading" :loading="loading" @click="buildObjects()" title="Refresh" text style="font-size:16px; padding:0px; min-width:36px; height:36px; margin-top:6px; margin-right:8px;"><v-icon small>fas fa-redo-alt</v-icon></v-btn>
                    </v-tabs>
                  </div>
                  <div style="height:54vh">
                    <ag-grid-vue v-show="tabObjectsSelected == 0" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection oncontextmenu="return false" @grid-ready="onGridReady('tables', $event)" @new-columns-loaded="onNewColumnsLoaded('tables')" @selection-changed="onSelectionChanged('tables')" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.tables" :defaultColDef="defaultColDef" :rowData="objectsItems.tables"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 1" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection oncontextmenu="return false" @grid-ready="onGridReady('views', $event)" @selection-changed="onSelectionChanged('views')" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.views" :defaultColDef="defaultColDef" :rowData="objectsItems.views"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 2" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection oncontextmenu="return false" @grid-ready="onGridReady('triggers', $event)" @selection-changed="onSelectionChanged('triggers')" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.triggers" :defaultColDef="defaultColDef" :rowData="objectsItems.triggers"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 3" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection oncontextmenu="return false" @grid-ready="onGridReady('functions', $event)" @selection-changed="onSelectionChanged('functions')" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.functions" :defaultColDef="defaultColDef" :rowData="objectsItems.functions"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 4" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection oncontextmenu="return false" @grid-ready="onGridReady('procedures', $event)" @selection-changed="onSelectionChanged('procedures')" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.procedures" :defaultColDef="defaultColDef" :rowData="objectsItems.procedures"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 5" suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection oncontextmenu="return false" @grid-ready="onGridReady('events', $event)" @selection-changed="onSelectionChanged('events')" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.events" :defaultColDef="defaultColDef" :rowData="objectsItems.events"></ag-grid-vue>
                  </div>
                  <v-row no-gutters style="margin-top:15px">
                    <v-col cols="auto">
                      <v-text-field v-model="database" label="Source Database" dense outlined readonly hide-details style="width:300px"></v-text-field>
                    </v-col>
                    <v-col cols="auto" style="margin-left:14px; margin-right:14px">
                      <v-icon size="18" style="margin-top:13px">fas fa-arrow-right</v-icon>
                    </v-col>
                    <v-col cols="auto">
                      <v-autocomplete v-model="targetDatabase" :items="databaseItems" label="Target Database" dense outlined :rules="[v => !!v || '']" required hide-details style="width:300px"></v-autocomplete>
                    </v-col>
                  </v-row>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loading" @click="cloneObjectsSubmit" color="#00b16a">Clone</v-btn>
                    </v-col>
                    <v-col style="margin-bottom:10px;">
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
                  <div class="text-h6" style="font-weight:400;">Clone Progress</div>
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
                    <span style="margin-left:8px">{{ progressText }}</span>  
                  </div>
                  <v-textarea v-if="cloneErrors.length > 0" readonly filled label="Errors" :value="cloneErrors" height="40vh" style="margin-top:10px; margin-bottom:15px" hide-details></v-textarea>
                </div>
                <v-divider></v-divider>
                <v-row no-gutters style="margin-top:15px;">
                  <v-col v-if="progressStep == 'clone'" cols="auto" style="margin-right:5px; margin-bottom:10px;">
                    <v-btn @click="cancelClone" color="#EF5354">Cancel</v-btn>
                  </v-col>
                  <v-col v-else style="margin-bottom:10px;">
                    <v-btn :disabled="loading" @click="closeClone" cols="auto" color="primary">Close</v-btn>
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
      tabObjectsSelected: 0,
      // AG-Grid
      gridApi: { tables: null, views: null, triggers: null, functions: null, procedures: null, events: null },
      columnApi: { tables: null, views: null, triggers: null, functions: null, procedures: null, events: null },
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
      targetDatabase: '',
      // Progress
      dialogProgress: false,
      progressText: '', 
      progressStep: 'clone', 
      progressValue: 0,
      progressTimeEvent: null,
      progressTimeValue: null,
      selected: undefined,
      // Axios Cancel Token
      cancelToken: null,
      // Clone Errors
      cloneErrors: '',
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
      'databasePrev',
      'databaseItems',
      'objectsHeaders',
      'objectsItems',
    ], { path: 'client/connection' }),
  },
  activated() {
    EventBus.$on('show-bottombar-objects-clone', this.showDialog);
  },
  watch: {
    dialog: function(val) {
      this.dialogOpened = val
      if (this.database != this.databasePrev) this.buildObjects()
    },
  },
  methods: {
    showDialog(selected) {
      this.selected = selected
      this.targetDatabase = ''
      this.dialog = true
      setTimeout(() => {
        for (let obj of this.objects) {
          if (this.gridApi[obj] != null) this.gridApi[obj].deselectAll()
        }
        if (selected === undefined) this.tabObjectsSelected = 0
        else this.selectRow()
      },0)
    },
    onGridReady(object, params) {
      setTimeout(() => {
        this.gridApi[object] = params.api
        this.columnApi[object] = params.columnApi
        if (this.databasePrev != this.database) this.gridApi[object].showLoadingOverlay()
        else this.resizeTable(object, true)
      },0)
    },
    onNewColumnsLoaded(object) {
      if (this.gridApi[object] != null) this.resizeTable(object, true)
    },
    onSelectionChanged(object) {
      this.objectsSelected[object] = this.gridApi[object].getSelectedRows().length
    },
    selectAll() {
      const objects = ['tables','views','triggers','functions','procedures','events']
      for (let obj of objects) try { this.gridApi[obj].selectAll() } catch {} // eslint-disable-line
    },
    deselectAll() {
      const objects = ['tables','views','triggers','functions','procedures','events']
      for (let obj of objects) try { this.gridApi[obj].deselectAll() } catch {} // eslint-disable-line
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
      setTimeout(() => {
        var allColumnIds = [];
        this.columnApi[object].getAllColumns().forEach(function(column) {
          allColumnIds.push(column.colId);
        })
        this.columnApi[object].autoSizeColumns(allColumnIds);
      },0)
      setTimeout(() => {
        if (this.objectsItems[object].length > 0) this.gridApi[object].hideOverlay()
        else this.gridApi[object].showNoRowsOverlay()
        if (selectRow) this.selectRow()
        this.loading = false
      },0)
    },
    buildObjects() {
      for (let obj of this.objects) {
        if (this.gridApi[obj] != null) this.gridApi[obj].showLoadingOverlay()
      }
      new Promise((resolve, reject) => {
        this.loading = true
        EventBus.$emit('get-objects', true, resolve, reject)
      })
      .finally(() => this.databasePrev = this.database)
    },
    cloneObjectsSubmit() {
      // Check if all fields are filled
      if (!this.$refs.dialogForm.validate()) {
        EventBus.$emit('send-notification', 'Please make sure all required fields are filled out correctly', '#EF5354')
        return
      }
      // Check if target database == source database
      if (this.database == this.targetDatabase) {
        EventBus.$emit('send-notification', "The target database cannot be the same as the source database", '#EF5354')
        return
      }
      // Get selected objects
      let objects = {'tables': [], 'views': [], 'triggers': [], 'functions': [], 'procedures': [], 'events': []}
      objects['tables'] = this.gridApi['tables'].getSelectedRows().map(x => x.name)
      objects['views'] = this.gridApi['views'].getSelectedRows().map(x => x.name)
      objects['triggers'] = this.gridApi['triggers'].getSelectedRows().map(x => x.name)
      objects['functions'] = this.gridApi['functions'].getSelectedRows().map(x => x.name)
      objects['procedures'] = this.gridApi['procedures'].getSelectedRows().map(x => x.name)
      objects['events'] = this.gridApi['events'].getSelectedRows().map(x => x.name)
      // Check if no objects are selected
      if (objects['tables'].length == 0 && objects['views'].length == 0 && objects['triggers'].length == 0 && objects['functions'].length == 0 && objects['procedures'].length == 0 && objects['events'].length == 0) {
        EventBus.$emit('send-notification', 'Please select at least one object to clone', '#EF5354')
        return
      }
      // Init Clone
      this.loading = true
      this.progressStep = 'clone'
      this.progressValue = 0
      this.cloneErrors = ''
      this.dialogProgress = true

      // Start Timer
      this.progressTimeValue = moment().startOf("day");
      this.progressTimeEvent = setInterval(() => requestAnimationFrame(() => this.progressTimeValue.add(1, 'second')), 1000)

      // Clone Objects
      new Promise((resolve, reject) => {
        this.cloneObjects(objects, resolve, reject)
      }).then (() => {
        // Update clone status
        if (this.cloneErrors.length == 0) {
          this.progressStep = 'success'
          this.progressText = 'Clone finished successfully.'
        }
        else {
          this.progressStep = 'fail'
          this.progressText = 'Clone finished with errors.'
        }
      })
      .catch(() => {})
      .finally(() => {
        clearInterval(this.progressTimeEvent)
        this.loading = false
      })
    },
    cloneObjects(objects, resolve, reject) {
      var payload = {
        connection: this.id + '-shared',
        server: this.server.id,
        options: {
          origin: this.database,
          target: this.targetDatabase,
          object: '',
          items: [],
        }
      }
      let total = objects['tables'].length + objects['views'].length + objects['triggers'].length + objects['functions'].length + objects['procedures'].length + objects['events'].length
      let t = 1
      const jobs = async () => {
        for (let objSchema of ['tables','views','triggers','functions','procedures','events']) {
          const n = objects[objSchema].length
          let i = 1
          for (let objName of objects[objSchema]) {
            // Start Object Clone
            payload['options']['object'] = objSchema.slice(0, -1)
            payload['options']['items'] = [objName]
            this.progressText = objSchema.charAt(0).toUpperCase() + objSchema.slice(1,-1) + ' ' + i.toString() + ' of ' + n.toString() + ' (' + objName + ').'
            const response = await this.cloneObject(payload)
            // Check Errors
            if (response.status != 200) this.cloneErrors += (this.cloneErrors.length != 0) ? '\n' + response.data.message : response.data.message
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
          this.progressText = 'Clone interrupted by user.'
          this.error = ''
        }
        else if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
        reject()
      })
    },
    async cloneObject(payload) {
      // Build options
      const CancelToken = axios.CancelToken
      this.cancelToken = CancelToken.source()
      const options = { cancelToken: this.cancelToken.token }
      // Execute Query
      try { return await axios.post('/client/clone', payload, options) }
      catch (error) { return error.response }
    },
    cancelClone() {
      this.cancelToken.cancel()
    },
    closeClone() {
      this.dialogProgress = false
      this.dialog = false
    },
    onSearch(value) {
      for (let id of ['tables','views','triggers','functions','procedures','events']) this.gridApi[id].setQuickFilter(value)
    },
  }
}
</script>