<template>
  <div>
    <v-dialog v-model="dialog" max-width="70%">
      <v-card>
        <v-toolbar flat dense color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="padding-right:10px; padding-bottom:4px">fas fa-cog</v-icon>SERVER VARIABLES</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-text-field ref="field" :disabled="loading" v-model="search" label="Search" append-icon="search" color="white" single-line hide-details></v-text-field>
          <v-divider class="ml-3" inset vertical></v-divider>
          <v-btn :disabled="loading" @click="dialog = false" icon style="margin-left:5px"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:0px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <ag-grid-vue suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection oncontextmenu="return false" @grid-ready="onGridReady" @first-data-rendered="onFirstDataRendered" @cell-key-down="onCellKeyDown" @cell-editing-started="cellEditingStarted" @cell-editing-stopped="cellEditingStopped" :stopEditingWhenGridLosesFocus="true" style="width:100%; height:70vh;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="single" :columnDefs="columns" :rowData="items"></ag-grid-vue>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!-------------------->
    <!-- CONFIRM DIALOG -->
    <!-------------------->
    <v-dialog v-model="confirmDialog" max-width="50%">
      <v-card>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <div class="text-h6" style="font-weight:400;">Confirmation</div>
              <v-flex xs12>
                <div class="body-1" style="font-weight:300; font-size:1.05rem!important; margin-top:10px;">Are you sure you want to change this server variable?</div>
                <v-text-field v-model="currentCellValues.current" filled readonly label="Current Value" hide-details style="margin-top:15px;"></v-text-field>
                <v-text-field v-model="currentCellValues.new" filled readonly label="New Value" hide-details style="margin-top:15px; margin-bottom:15px;"></v-text-field>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loading" @click="confirmDialogSubmit" color="#00b16a">Confirm</v-btn>
                    </v-col>
                    <v-col style="margin-bottom:10px;">
                      <v-btn :disabled="loading" @click="confirmDialogCancel" color="error">Cancel</v-btn>
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
<style scoped>
::v-deep .v-label {
  font-size: 14px;
}
</style>

<script>
import axios from 'axios'
import EventBus from '../../../js/event-bus'
import { mapFields } from '../../../js/map-fields'
import {AgGridVue} from "ag-grid-vue";

export default {
  data() {
    return {
      loading: false,
      // Dialog
      dialog: false,
      // AG Grid
      gridApi: null,
      columnApi: null,
      currentCellEditNode: {},
      currentCellValues: {'variable': '', 'current': '', 'new': ''},
      columns: [],
      items: [],
      search: '',
      // Confirm Dialog
      confirmDialog: false,
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
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('show-bottombar-objects-variables', this.showDialog);
  },
  watch: {
    search: function(val) {
      this.gridApi.setQuickFilter(val)
    },
    dialog: function(val) {
      this.dialogOpened = val
      this.buildVariables()
      if (this.gridApi != null) this.gridApi.sizeColumnsToFit()
    },
  },
  methods: {
    showDialog() {
      this.search = ''
      this.dialog = true
    },
    buildVariables() {
      if (this.gridApi != null) this.gridApi.showLoadingOverlay()
      this.loading = true
      const payload = {
        connection: this.id + '-shared',
        server: this.server.id
      }
      axios.get('/client/variables', { params: payload })
        .then((response) => {
          this.parseVariables(response.data.variables)
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
    },
    parseVariables(variables) {
      this.columns = [
        { headerName: 'Variable', colId: 'variable', field: 'variable', sortable: true, filter: true, resizable: true, editable: false },
        { headerName: 'Value', colId: 'value', field: 'value', sortable: true, filter: true, resizable: true, editable: true }
      ]
      this.items = variables
      if (this.gridApi != null) {
        this.loading = false
        this.$nextTick(() => { this.$refs.field.focus() })      
        this.gridApi.hideOverlay()  
      }
    },
    onGridReady(params) {
      this.gridApi = params.api
      this.columnApi = params.columnApi
      this.gridApi.showLoadingOverlay()
      this.loading = false
      this.$refs.field.focus()
    },
    onFirstDataRendered(params) {
      params.api.sizeColumnsToFit()
    },
    onCellKeyDown(e) {
      if (e.event.key == "c" && (e.event.ctrlKey || e.event.metaKey)) {
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
    },
    cellEditingStarted(event) {
      // Store row node
      this.currentCellEditNode = event.node
      // Store current value
      this.currentCellValues = {'variable': event.data['variable'], 'current': event.data['value']}
    },
    cellEditingStopped(event) {
      // Store new value
      this.currentCellValues['new'] = event.value
      // Open confirmation dialog
      if (this.currentCellValues['current'] != this.currentCellValues['new']) this.confirmDialog = true
    },
    confirmDialogSubmit() {
      this.loading = true
      let query = "SET GLOBAL " + this.currentCellValues['variable'] + ' = ' + this.currentCellValues['new']
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', [query], resolve, reject)
      }).then(() => { 
        // Change Variable
        this.currentCellEditNode.setDataValue('value', this.currentCellValues['new'])
        // Hide Confirm Dialog
        this.confirmDialog = false
        // Send notification
        EventBus.$emit('send-notification', 'Server variable changed successfully', 'success')
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    confirmDialogCancel() {
      this.currentCellEditNode.setDataValue('value', this.currentCellValues['current'])
      this.confirmDialog = false
    },
  }
}
</script>