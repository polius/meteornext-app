<template>
  <div>
    <v-dialog v-model="dialog" persistent max-width="70%">
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
                <v-text-field ref="field" :disabled="loading" v-model="search" solo dense label="Filter..." hide-details></v-text-field>
                <ag-grid-vue suppressColumnVirtualisation suppressRowClickSelection @grid-ready="onGridReady" @first-data-rendered="onFirstDataRendered" style="width:100%; height:70vh;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="single" :columnDefs="columns" :rowData="items"></ag-grid-vue>
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
      // Grid Api
      gridApi: null,
      columnApi: null,
      columns: [],
      items: [],
      search: '',
    }
  },
  components: { AgGridVue },
  computed: {
    ...mapFields([
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
        { headerName: 'Value', colId: 'value', field: 'value', sortable: true, filter: true, resizable: true, editable: false }
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
  }
}
</script>