<template>
  <div>
    <v-dialog v-model="dialog" max-width="70%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">Server Variables</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="dialog = false" icon><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:0px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-text-field ref="field" :disabled="loading" v-model="search" label="Filter..." solo dense clearable hide-details></v-text-field>
                <ag-grid-vue suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection @grid-ready="onGridReady" @first-data-rendered="onFirstDataRendered" @cell-editing-started="cellEditingStarted" @cell-editing-stopped="cellEditingStopped" :stopEditingWhenGridLosesFocus="true" style="width:100%; height:70vh;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="single" :columnDefs="columns" :rowData="items"></ag-grid-vue>
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
                      <v-btn :loading="loading" @click="confirmDialogSubmit" color="primary">Confirm</v-btn>
                    </v-col>
                    <v-col style="margin-bottom:10px;">
                      <v-btn :disabled="loading" @click="confirmDialogCancel" outlined color="#e74d3c">Cancel</v-btn>
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
      'index',
      'server',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('SHOW_BOTTOMBAR_OBJECTS_VARIABLES', this.showDialog);
  },
  watch: {
    search: function(val) {
      this.gridApi.setQuickFilter(val)
    }
  },
  methods: {
    showDialog() {
      this.search = ''
      this.dialog = true
      this.buildVariables()
      if (this.gridApi != null) {
        this.gridApi.sizeColumnsToFit()
      }
    },
    buildVariables() {
      if (this.gridApi != null) this.gridApi.showLoadingOverlay()
      this.loading = true
      const payload = {
        connection: this.index,
        server: this.server.id
      }
      axios.get('/client/variables', { params: payload })
        .then((response) => {
          this.parseVariables(response.data.variables)
        })
        .catch((error) => {
          console.log(error)
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('SEND_NOTIFICATION', error.response.data.message, 'error')
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
        EventBus.$emit('EXECUTE_SIDEBAR', [query], resolve, reject)
      }).then(() => { 
        // Change Variable
        this.currentCellEditNode.setDataValue('value', this.currentCellValues['new'])
        // Hide Confirm Dialog
        this.confirmDialog = false
        // Send notification
        EventBus.$emit('SEND_NOTIFICATION', 'Server variable changed successfully', 'success')
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    confirmDialogCancel() {
      this.currentCellEditNode.setDataValue('value', this.currentCellValues['current'])
      this.confirmDialog = false
    },
  }
}
</script>