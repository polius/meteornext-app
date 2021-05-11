<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="body-2 white--text font-weight-medium"><v-icon small style="margin-right:10px">fas fa-bolt</v-icon>CLIENT</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text class="body-2"><v-icon small style="padding-right:10px">fas fa-database</v-icon>SERVERS</v-btn>
          <v-btn @click="filterDialog = true" text class="body-2" :style="{ backgroundColor : filterApplied ? '#4ba1f1' : '' }"><v-icon small style="padding-right:10px">fas fa-sliders-h</v-icon>FILTER</v-btn>
          <v-btn @click="refresh" text class="body-2"><v-icon small style="margin-right:10px">fas fa-sync-alt</v-icon>REFRESH</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
        </v-toolbar-items>
        <v-text-field append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-progress-linear v-show="loading" indeterminate></v-progress-linear>
      <ag-grid-vue ref="agGrid" suppressColumnVirtualisation suppressDragLeaveHidesColumns suppressContextMenu preventDefaultOnContextMenu @grid-ready="onGridReady" @row-data-changed="onRowDataChanged" @cell-key-down="onCellKeyDown" style="width:100%; height:calc(100vh - 185px);" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="headers" :rowData="items"></ag-grid-vue>
    </v-card>

    <v-dialog v-model="filterDialog" max-width="50%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:3px">fas fa-sliders-h</v-icon>FILTER</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="filterDialog = false" style="width:40px; height:40px"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 10px 15px 15px 15px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:10px; margin-bottom:20px;">
                  <v-row>
                    <v-col>
                      <v-autocomplete :loading="loading" text v-model="filter.user" :items="filterUsers" label="User" clearable style="padding-top:0px" hide-details></v-autocomplete>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col>
                      <v-text-field text v-model="filter.server" label="Server" style="padding-top:0px" hide-details></v-text-field>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="8" style="padding-right:5px;">
                      <v-text-field text v-model="filter.database" label="Database" required style="padding-top:0px" hide-details></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-left:5px;">
                      <v-select text v-model="filter.databaseFilter" label="Filter" :items="filters" item-value="id" item-text="name" :rules="[v => ((filter.database === undefined || filter.database.length == 0) || (filter.database.length > 0 && !!v)) || '']" style="padding-top:0px" hide-details></v-select>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="8" style="padding-right:5px;">
                      <v-text-field text v-model="filter.query" label="Query" required style="padding-top:0px" hide-details></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-left:5px;">
                      <v-select text v-model="filter.queryFilter" label="Filter" :items="filters" item-value="id" item-text="name" :rules="[v => ((filter.query === undefined || filter.query.length == 0) || (filter.query.length > 0 && !!v)) || '']" style="padding-top:0px" hide-details></v-select>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col>
                      <v-select v-model="filter.status" :items="[{id: 1, name: 'Success'}, {id: 0, name: 'Failed'}]" item-value="id" item-text="name" label="Status" clearable required style="padding-top:0px" hide-details></v-select>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="6" style="padding-right:8px;">
                      <v-text-field v-model="filter.dateFrom" label="Date From" style="padding-top:0px" hide-details>
                        <template v-slot:append><v-icon @click="dateTimeDialogOpen('from')" small style="margin-top:4px; margin-right:4px">fas fa-calendar-alt</v-icon></template>
                      </v-text-field>
                    </v-col>
                    <v-col cols="6" style="padding-left:8px;">
                      <v-text-field v-model="filter.dateTo" label="Date To" style="padding-top:0px" hide-details>
                        <template v-slot:append><v-icon @click="dateTimeDialogOpen('to')" small style="margin-top:4px; margin-right:4px">fas fa-calendar-alt</v-icon></template>
                      </v-text-field>
                    </v-col>
                  </v-row>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :loading="loading" color="#00b16a" @click="submitFilter">CONFIRM</v-btn>
                  <v-btn :disabled="loading" color="error" @click="filterDialog = false" style="margin-left:5px;">CANCEL</v-btn>
                  <v-btn v-show="filterApplied" :disabled="loading" color="info" @click="clearFilter" style="float:right;">Remove Filter</v-btn>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="dateTimeDialog" persistent width="290px">
      <v-date-picker v-if="dateTimeMode == 'date'" v-model="dateTimeValue.date" color="info" scrollable>
        <v-btn text color="#00b16a" @click="dateTimeSubmit">Confirm</v-btn>
        <v-btn text color="error" @click="dateTimeDialog = false">Cancel</v-btn>
        <v-spacer></v-spacer>
        <v-btn text color="info" @click="dateTimeNow">Now</v-btn>
      </v-date-picker>
      <v-time-picker v-else-if="dateTimeMode == 'time'" v-model="dateTimeValue.time" color="info" format="24hr" use-seconds scrollable>
        <v-btn text color="#00b16a" @click="dateTimeSubmit">Confirm</v-btn>
        <v-btn text color="error" @click="dateTimeDialog = false">Cancel</v-btn>
        <v-spacer></v-spacer>
        <v-btn text color="info" @click="dateTimeNow">Now</v-btn>
      </v-time-picker>
    </v-dialog>

    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<style scoped>
@import "../../../../node_modules/ag-grid-community/dist/styles/ag-grid.css";
@import "../../../../node_modules/ag-grid-community/dist/styles/ag-theme-alpine-dark.css";
</style>
<style scoped src="@/styles/agGridVue.css"></style>

<script>
import axios from 'axios'
import moment from 'moment'
import {AgGridVue} from "ag-grid-vue";

export default {
  data() {
    return {
      loading: true,
      gridApi: null,
      columnApi: null,
      items: [],
      headers: [
        { headerName: 'Date', colId: 'date', field: 'date', sortable: true, resizable: true },
        { headerName: 'User', colId: 'user', field: 'user', sortable: true, resizable: true },
        { headerName: 'Server', colId: 'server', field: 'server', sortable: true, resizable: true },
        { headerName: 'Database', colId: 'database', field: 'database', sortable: true, resizable: true },
        { headerName: 'Query', colId: 'query', field: 'query', sortable: true, resizable: true },
        {
          headerName: 'Status', colId: 'status', field: 'status', sortable: true, resizable: true,
          cellRenderer: function(params) {
            if (params.value) return '<i class="fas fa-check-circle" title="Success" style="color:#00b16a; margin-right:8px;"></i>Success'
            else return '<i class="fas fa-times-circle" title="Failed" style="color:#e74d3c; margin-right:8px;"></i>Failed'
          }
         },
        { headerName: 'Records', colId: 'records', field: 'records', sortable: true, resizable: true },
        {
          headerName: 'Elapsed', colId: 'elapsed', field: 'elapsed', sortable: true, resizable: true,
          valueGetter: function(params) {
            return params.data.elapsed + 's'
          }
        },
        { headerName: 'Error', colId: 'error', field: 'error', sortable: true, resizable: true },
      ],
      // Dialogs
      filterDialog: false,
      filters: [
        {id: 'equal', name: 'Equal'},
        {id: 'not_equal', name: 'Not equal'},
        {id: 'starts', name: 'Starts'},
        {id: 'not_starts', name: 'Not starts'},
        {id: 'contains', name: 'Contains'}
      ],
      filter: {},
      filterUsers: [],
      filterApplied: false,
      dateTimeDialog: false,
      dateTimeField: '',
      dateTimeMode: 'date',
      dateTimeValue: { date: null, time: null },
      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarText: '',
      snackbarColor: ''
    }
  },
  components: { AgGridVue },
  created() {
    this.getClient()
  },
  methods: {
    getClient() {
      this.loading = true
      let payload = this.filterApplied ? JSON.parse(JSON.stringify(this.filter)) : {}
      // Parse date to utc
      if ('dateFrom' in payload) payload.dateFrom = moment(this.filter.dateFrom).utc().format("YYYY-MM-DD HH:mm:ss")
      if ('dateTo' in payload) payload.dateTo = moment(this.filter.dateTo).utc().format("YYYY-MM-DD HH:mm:ss")
      // Get Client queries
      axios.get('/admin/client', { params: payload })
        .then((response) => {
          this.items = response.data.queries.map(x => ({...x, date: this.dateFormat(x.date)}))
          this.filterUsers = response.data.users
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
    },
    onGridReady(params) {
      this.gridApi = params.api
      this.columnApi = params.columnApi
    },
    onRowDataChanged() {
      if (this.columnApi != null) this.resizeTable()
    },
    resizeTable() {
      let allColumnIds = this.columnApi.getAllColumns().map(v => v.colId)
      this.columnApi.autoSizeColumns(allColumnIds)
    },
    onCellKeyDown(e) {
      if (e.event.key == "c" && (e.event.ctrlKey || e.event.metaKey)) {
        let selectedRows = this.gridApi.getSelectedRows()
        if (selectedRows.length > 1) {
          // Copy values
          let header = Object.keys(selectedRows[0])
          let value = selectedRows.map(row => header.map(fieldName => row[fieldName] == null ? 'NULL' : row[fieldName]).join('\t')).join('\n')
          navigator.clipboard.writeText(value)
          // Apply effect
          // this.gridApi.flashCells({
          //   rowNodes: this.gridApi.getSelectedNodes(),
          //   flashDelay: 200,
          //   fadeDelay: 200,
          // })
        }
        else {
          // Copy value
          navigator.clipboard.writeText(e.value)
          // Apply effect
          this.gridApi.flashCells({
            rowNodes: this.gridApi.getSelectedNodes(),
            columns: [this.gridApi.getFocusedCell().column.colId],
            flashDelay: 200,
            fadeDelay: 200,
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
      else if (e.event.key == 'a' && (e.event.ctrlKey || e.event.metaKey)) {
        this.gridApi.selectAll()
      }
    },
    refresh() {
      this.getClient()
    },
    dateTimeDialogOpen(field) {
      this.dateTimeField = field
      this.dateTimeMode = 'date'
      this.dateTimeValue = { date: moment().format("YYYY-MM-DD"), time: moment().format("HH:mm") }
      this.dateTimeDialog = true
    },
    dateTimeSubmit() {
      if (this.dateTimeMode == 'date') this.dateTimeMode = 'time'
      else {
        if (this.dateTimeField == 'from') this.filter.dateFrom = this.dateTimeValue.date + ' ' + this.dateTimeValue.time
        else if (this.dateTimeField == 'to') this.filter.dateTo = this.dateTimeValue.date + ' ' + this.dateTimeValue.time
        this.dateTimeDialog = false
      }
    },
    dateTimeNow() {
      this.dateTimeValue = { date: moment().format("YYYY-MM-DD"), time: moment().format("HH:mm") }
    },
    submitFilter() {
      // Check if some filter was applied
      if (!Object.keys(this.filter).some(x => this.filter[x] != null && this.filter[x].length != 0)) {
        this.notification('Enter at least one filter', 'error')
        return
      }
      this.filterDialog = false
      this.filterApplied = true
      this.getClient()
    },
    clearFilter() {
      this.filterDialog = false
      this.filter = {}
      this.filterApplied = false
      this.getClient()
    },
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  }
}
</script>