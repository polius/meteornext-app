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
                      <v-tab @click="tabObjects('tables')"><span class="pl-2 pr-2">Tables</span></v-tab>
                      <v-divider class="mx-3" inset vertical></v-divider>
                      <v-tab v-if="tab == 'sql'" @click="tabObjects('views')"><span class="pl-2 pr-2">Views</span></v-tab>
                      <v-divider v-if="tab == 'sql'" class="mx-3" inset vertical></v-divider>
                      <v-tab v-if="tab == 'sql'" @click="tabObjects('triggers')"><span class="pl-2 pr-2">Triggers</span></v-tab>
                      <v-divider v-if="tab == 'sql'" class="mx-3" inset vertical></v-divider>
                      <v-tab v-if="tab == 'sql'" @click="tabObjects('functions')"><span class="pl-2 pr-2">Functions</span></v-tab>
                      <v-divider v-if="tab == 'sql'" class="mx-3" inset vertical></v-divider>
                      <v-tab v-if="tab == 'sql'" @click="tabObjects('procedures')"><span class="pl-2 pr-2">Procedures</span></v-tab>
                      <v-divider v-if="tab == 'sql'" class="mx-3" inset vertical></v-divider>
                      <v-tab v-if="tab == 'sql'" @click="tabObjects('events')"><span class="pl-2 pr-2">Events</span></v-tab>
                      <v-divider v-if="tab == 'sql'" class="mx-3" inset vertical></v-divider>
                    </v-tabs>
                  </div>
                  <div style="height:50vh">
                    <ag-grid-vue v-show="tabObjectsSelected == 0" suppressColumnVirtualisation suppressRowClickSelection @grid-ready="onGridReady('tables', $event)" @new-columns-loaded="onNewColumnsLoaded('tables')" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.tables" :defaultColDef="defaultColDef" :rowData="objectsItems.tables"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 1" suppressColumnVirtualisation suppressRowClickSelection @grid-ready="onGridReady('views', $event)" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.views" :defaultColDef="defaultColDef" :rowData="objectsItems.views"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 2" suppressColumnVirtualisation suppressRowClickSelection @grid-ready="onGridReady('triggers', $event)" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.triggers" :defaultColDef="defaultColDef" :rowData="objectsItems.triggers"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 3" suppressColumnVirtualisation suppressRowClickSelection @grid-ready="onGridReady('functions', $event)" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.functions" :defaultColDef="defaultColDef" :rowData="objectsItems.functions"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 4" suppressColumnVirtualisation suppressRowClickSelection @grid-ready="onGridReady('procedures', $event)" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.procedures" :defaultColDef="defaultColDef" :rowData="objectsItems.procedures"></ag-grid-vue>
                    <ag-grid-vue v-show="tabObjectsSelected == 5" suppressColumnVirtualisation suppressRowClickSelection @grid-ready="onGridReady('events', $event)" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="objectsHeaders.events" :defaultColDef="defaultColDef" :rowData="objectsItems.events"></ag-grid-vue>
                  </div>
                  <v-select v-if="tab == 'sql'" v-model="include" :items="includeItems" label="Include" outlined hide-details style="margin-top:15px"></v-select>
                  <v-text-field v-if="tab == 'csv'" v-model="nullValues" label="NULL values" outlined hide-details style="margin-top:15px"></v-text-field>
                  <v-checkbox v-if="tab == 'csv'" v-model="includeFields" label="Include field names in first row" hide-details style="padding:0px; margin-top:10px"></v-checkbox>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loading" @click="exportObjectsSubmit" color="primary">Export</v-btn>
                    </v-col>
                    <v-col style="margin-bottom:10px;">
                      <v-btn :disabled="loading" @click="this.dialog = false" outlined color="#e74d3c">Close</v-btn>
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
      gridApi: { tables: null, views: null, triggers: null, functions: null, procedures: null, events: null },
      columnApi: { tables: null, views: null, triggers: null, functions: null, procedures: null, events: null },
      defaultColDef: null,
      // Include
      include: 'Structure + Content',
      includeItems: ['Structure + Content','Structure','Content'],
      includeFields: true,
      nullValues: 'NULL',
      // Axios Cancel Token
      cancelToken: null,
    }
  },
  components: { AgGridVue },
  computed: {
    ...mapFields([
      'objectsHeaders',
      'objectsItems',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('SHOW_BOTTOMBAR_OBJECTS_EXPORT', this.showDialog);
  },
  methods: {
    showDialog() {
      this.tabClick('sql')
      this.include = 'Structure + Content'
      this.nullValues = 'NULL'
      this.dialog = true
    },
    onGridReady(object, params) {
      this.gridApi[object] = params.api
      this.columnApi[object] = params.columnApi
      this.defaultColDef = {
        flex: 1,
        minWidth: 100,
        resizable: true,
        headerCheckboxSelection: this.isFirstColumn,
        checkboxSelection: this.isFirstColumn,
      }
      if (object == 'tables') {
        this.gridApi[object].showLoadingOverlay()
        this.buildObjects()
      }
    },
    isFirstColumn(params) {
      let displayedColumns = params.columnApi.getAllDisplayedColumns();
      let thisIsFirstColumn = displayedColumns[0] === params.column;
      return thisIsFirstColumn;
    },
    onNewColumnsLoaded(object) {
      if (this.gridApi[object] != null) this.resizeTable(object)
    },
    resizeTable(object) {
      var allColumnIds = [];
      this.columnApi[object].getAllColumns().forEach(function(column) {
        allColumnIds.push(column.colId);
      });
      this.columnApi[object].autoSizeColumns(allColumnIds);
      
    },
    tabClick(object) {
      if (object == 'sql') {
        this.sqlColor = 'primary'
        this.csvColor = '#779ecb'
      }
      else if (object == 'csv') {
        this.sqlColor = '#779ecb'
        this.csvColor = 'primary'
      }
      this.tab = object
      this.tabObjectsSelected = 0
    },
    tabObjects(object) {
      this.tabObjectsSelected = object
      this.$nextTick(() => { this.resizeTable(object) })
    },
    buildObjects() {
      let promise = new Promise((resolve, reject) => {
        this.loading = true
        EventBus.$emit('GET_OBJECTS', resolve, reject)
      })
      promise.finally(() => {
        this.gridApi['tables'].hideOverlay()
        this.loading = false 
      })
    },
    exportObjectsSubmit() {
      // Check if all fields are filled
      if (!this.$refs.dialogForm.validate()) {
        EventBus.$emit('SEND_NOTIFICATION', 'Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      this.loading = true
      axios.get('/client/export', { responseType: 'arraybuffer' })
      .then((response) => {
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a')
        link.href = url
        link.setAttribute('download', 'file.sql')
        document.body.appendChild(link)
        link.click()
        link.remove()
      });      
    }
  },
}
</script>