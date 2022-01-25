<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:3px">fas fa-plus</v-icon>NEW CLONE</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn icon @click="goBack"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
      </v-toolbar>
      <v-container fluid grid-list-lg style="padding:0px; margin-bottom:10px">
        <v-layout row wrap>
          <v-flex xs12 style="padding-bottom:0px">
            <v-stepper v-model="stepper" vertical style="padding-bottom:10px; background-color:#424242">
              <v-stepper-step :complete="stepper > 1" step="1">SOURCE</v-stepper-step>
              <v-stepper-content step="1" style="padding-top:0px; padding-left:10px">
                <v-card style="margin:5px">
                  <v-card-text>
                    <v-form ref="sourceForm" @submit.prevent>
                      <v-autocomplete @change="getDatabases" ref="server" v-model="server" :items="serverItems" item-value="id" item-text="name" label="Server" auto-select-first :rules="[v => !!v || '']" style="padding-top:8px" hide-details autofocus>
                        <template v-slot:[`selection`]="{ item }">
                          <v-icon v-if="!item.active" small color="warning" title="Maximum allowed resources exceeded. Upgrade your license to have more servers." style="margin-right:10px">fas fa-exclamation-triangle</v-icon>
                          <v-icon small :color="item.shared ? '#EB5F5D' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          {{ item.name }}
                        </template>
                        <template v-slot:[`item`]="{ item }">
                          <v-icon v-if="!item.active" small color="warning" title="Maximum allowed resources exceeded. Upgrade your license to have more servers." style="margin-right:10px">fas fa-exclamation-triangle</v-icon>
                          <v-icon small :color="item.shared ? '#EB5F5D' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          {{ item.name }}
                        </template>
                      </v-autocomplete>
                      <v-autocomplete @change="getDatabaseSize" ref="database" :loading="loading" :disabled="server == null" v-model="database" :items="databaseItems" item-value="id" item-text="name" label="Database" auto-select-first :rules="[v => !!v || '']" style="margin-top:20px" hide-details></v-autocomplete>
                      <div v-if="databaseSize != null" class="text-body-1" style="margin-top:20px">Size: <span class="white--text" style="font-weight:500">{{ formatBytes(this.databaseSize) }}</span></div>
                      <v-row no-gutters style="margin-top:20px;">
                        <v-col cols="auto" class="mr-auto">
                          <v-btn :disabled="databaseSize == null" color="primary" @click="nextStep">CONTINUE</v-btn>
                          <v-btn @click="goBack" text style="margin-left:5px">CANCEL</v-btn>
                        </v-col>
                        <v-col cols="auto">
                          <v-btn @click="getServer(server)" :disabled="server == null" text>SERVER DETAILS</v-btn>
                        </v-col>
                      </v-row>
                    </v-form>
                  </v-card-text>
                </v-card>
              </v-stepper-content>
              <v-stepper-step :complete="stepper > 2" step="2">SETUP</v-stepper-step>
              <v-stepper-content step="2" style="padding-top:0px; padding-left:10px">
                <v-card style="margin:5px">
                  <v-card-text>
                    <v-form ref="setupForm" @submit.prevent>
                      <div class="text-body-1 white--text">MODE</div>
                      <v-radio-group v-model="mode" style="margin-top:10px; margin-bottom:15px" hide-details>
                        <v-radio value="full">
                          <template v-slot:label>
                            FULL
                          </template>
                        </v-radio>
                        <v-radio value="partial">
                          <template v-slot:label>
                            PARTIAL
                          </template>
                        </v-radio>
                      </v-radio-group>
                      <div class="text-body-1 white--text">FORMAT</div>
                      <v-radio-group v-model="format" style="margin-top:10px; margin-bottom:15px" hide-details>
                        <v-radio value="sql">
                          <template v-slot:label>
                            SQL
                          </template>
                        </v-radio>
                        <v-radio disabled value="csv">
                          <template v-slot:label>
                            CSV
                          </template>
                        </v-radio>
                      </v-radio-group>
                      <div class="text-body-1 white--text">SETTINGS</div>
                      <v-checkbox v-model="exportSchema" label="Export Schema (Add CREATE TABLE statements)." hide-details style="margin-top:10px"></v-checkbox>
                      <v-checkbox v-model="exportData" label="Export Data (Dump table contents)." hide-details style="margin-top:10px"></v-checkbox>
                      <v-checkbox :disabled="!exportSchema" v-model="addDropTable" label="Add Drop Table (Add DROP TABLE statement before each CREATE TABLE statement)." hide-details style="margin-top:10px"></v-checkbox>
                      <div style="margin-top:20px;">
                        <v-btn color="primary" @click="nextStep">CONTINUE</v-btn>
                        <v-btn @click="stepper -= 1" text style="margin-left:5px">CANCEL</v-btn>
                      </div>
                    </v-form>
                  </v-card-text>
                </v-card>
              </v-stepper-content>
              <v-stepper-step :complete="stepper > 3" step="3">OBJECTS</v-stepper-step>
              <v-stepper-content step="3" style="padding-top:0px; padding-left:10px">
                <v-card style="margin:5px">
                  <v-card-text>
                    <v-form ref="objectsForm" @submit.prevent>
                      <div style="margin-top:-16px; margin-left:-16px; margin-right:-16px">
                        <v-tabs v-model="tab" dense background-color="#303030" color="white" slider-size="0" slot="extension" class="elevation-2">
                          <v-tab><span class="pl-2 pr-2">{{ `Tables (${tablesSelected.length}/${tablesItems.length})` }}</span></v-tab>
                          <v-text-field @input="onSearch" label="Search" append-icon="search" color="white" single-line style="padding-top:4px; margin-left:15px; margin-right:15px" hide-details></v-text-field>
                          <v-btn :disabled="loading" :loading="loading" @click="getTables(true)" title="Refresh" text style="font-size:16px; padding:0px; min-width:36px; height:36px; margin-top:6px; margin-right:8px;"><v-icon small>fas fa-redo-alt</v-icon></v-btn>
                        </v-tabs>
                      </div>
                      <div style="height:50vh; margin-left:-17px; margin-right:-17px">
                        <ag-grid-vue suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection oncontextmenu="return false" @grid-ready="onGridReady" @selection-changed="onSelectionChanged" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="tablesHeaders" :defaultColDef="defaultColDef" :rowData="tablesItems"></ag-grid-vue>
                      </div>
                      <div class="text-body-1" style="margin-top:15px">Size: <span class="white--text" style="font-weight:500">{{ `${formatBytes(this.tableSize)} / ${formatBytes(this.databaseSize)}` }}</span></div>
                      <div class="text-body-1 white--text" style="margin-top:15px">OPTIONS</div>
                      <v-checkbox v-model="exportTriggers" label="Export Triggers" hide-details style="margin-top:10px"></v-checkbox>
                      <v-checkbox v-model="exportRoutines" label="Export Routines (Functions and Procedures)" hide-details style="margin-top:10px"></v-checkbox>
                      <v-checkbox v-model="exportEvents" label="Export Events" hide-details style="margin-top:10px"></v-checkbox>
                    </v-form>
                    <div style="margin-top:20px">
                      <v-btn color="primary" @click="nextStep">CONTINUE</v-btn>
                      <v-btn text @click="stepper -= 1" style="margin-left:5px">CANCEL</v-btn>
                    </div>
                  </v-card-text>
                </v-card>
              </v-stepper-content>
              <v-stepper-step step="4">OVERVIEW</v-stepper-step>
              <v-stepper-content step="4" style="margin:0px; padding:0px 10px 0px 0px">
                <div style="margin-left:10px">
                  <v-card style="margin:5px">
                    <v-toolbar dense flat color="#2e3131">
                      <v-toolbar-title class="subtitle-1">SOURCE</v-toolbar-title>
                    </v-toolbar>
                    <v-card-text>
                      <v-autocomplete readonly v-model="server" :items="serverItems" item-value="id" item-text="name" label="Server" auto-select-first :rules="[v => !!v || '']" style="padding-top:8px" hide-details>
                        <template v-slot:[`selection`]="{ item }">
                          <v-icon v-if="!item.active" small color="warning" title="Maximum allowed resources exceeded. Upgrade your license to have more servers." style="margin-right:10px">fas fa-exclamation-triangle</v-icon>
                          <v-icon small :color="item.shared ? '#EB5F5D' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          {{ item.name }}
                        </template>
                        <template v-slot:[`item`]="{ item }">
                          <v-icon v-if="!item.active" small color="warning" title="Maximum allowed resources exceeded. Upgrade your license to have more servers." style="margin-right:10px">fas fa-exclamation-triangle</v-icon>
                          <v-icon small :color="item.shared ? '#EB5F5D' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          {{ item.name }}
                        </template>
                      </v-autocomplete>
                      <v-autocomplete readonly :loading="loading" v-model="database" :items="databaseItems" item-value="id" item-text="name" label="Database" auto-select-first :rules="[v => !!v || '']" style="margin-top:20px" hide-details></v-autocomplete>
                    </v-card-text>
                  </v-card>
                </div>
                <div style="margin-left:10px">
                  <v-card style="margin:5px; margin-top:10px">
                    <v-toolbar dense flat color="#2e3131">
                      <v-toolbar-title class="subtitle-1">SETUP</v-toolbar-title>
                    </v-toolbar>
                    <v-card-text>
                      <div class="text-body-1 white--text">MODE</div>
                      <v-radio-group readonly v-model="mode" style="margin-top:10px; margin-bottom:15px" hide-details>
                        <v-radio value="full">
                          <template v-slot:label>
                            FULL
                          </template>
                        </v-radio>
                        <v-radio value="partial">
                          <template v-slot:label>
                            PARTIAL
                          </template>
                        </v-radio>
                      </v-radio-group>
                      <div class="text-body-1 white--text">FORMAT</div>
                      <v-radio-group readonly v-model="format" style="margin-top:10px; margin-bottom:15px" hide-details>
                        <v-radio value="sql">
                          <template v-slot:label>
                            SQL
                          </template>
                        </v-radio>
                        <v-radio disabled value="csv">
                          <template v-slot:label>
                            CSV
                          </template>
                        </v-radio>
                      </v-radio-group>
                      <div class="text-body-1 white--text">SETTINGS</div>
                      <v-checkbox readonly v-model="exportSchema" label="Export Schema (Add CREATE TABLE statements)." hide-details style="margin-top:10px"></v-checkbox>
                      <v-checkbox readonly v-model="exportData" label="Export Data (Dump table contents)." hide-details style="margin-top:10px"></v-checkbox>
                      <v-checkbox readonly :disabled="!exportSchema" v-model="addDropTable" label="Add Drop Table (Add DROP TABLE statement before each CREATE TABLE statement)." hide-details style="margin-top:10px"></v-checkbox>
                    </v-card-text>
                  </v-card>
                </div>
                <div v-show="mode == 'partial'" style="margin-left:10px">
                  <v-card style="margin:5px; margin-top:10px">
                    <v-toolbar dense flat color="#2e3131">
                      <v-toolbar-title class="subtitle-1">OBJECTS</v-toolbar-title>
                    </v-toolbar>
                    <v-card-text>
                      <div style="margin-left:1px; margin-right:1px">
                        <v-tabs v-model="tab" dense background-color="#303030" color="white" slider-size="0" slot="extension" class="elevation-2">
                          <v-tab><span class="pl-2 pr-2">{{ `Tables (${tablesSelected.length}/${tablesItems.length})` }}</span></v-tab>
                          <v-text-field @input="onSearch2" label="Search" append-icon="search" color="white" single-line style="padding-top:4px; margin-left:15px; margin-right:15px" hide-details></v-text-field>
                        </v-tabs>
                      </div>
                      <div style="height:50vh">
                        <ag-grid-vue suppressDragLeaveHidesColumns suppressColumnVirtualisation suppressRowClickSelection oncontextmenu="return false" @grid-ready="onGridReady2" style="width:100%; height:100%;" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" rowSelection="multiple" :columnDefs="tablesHeaders" :defaultColDef="defaultColDef2" :rowData="tablesSelected"></ag-grid-vue>
                      </div>
                      <div class="text-body-1" style="margin-top:15px">Size: <span class="white--text" style="font-weight:500">{{ `${formatBytes(this.tableSize)} / ${formatBytes(this.databaseSize)}` }}</span></div>
                      <div class="text-body-1 white--text" style="margin-top:15px">OPTIONS</div>
                      <v-checkbox readonly v-model="exportTriggers" label="Export Triggers" hide-details style="margin-top:10px"></v-checkbox>
                      <v-checkbox readonly v-model="exportRoutines" label="Export Routines (Functions and Procedures)" hide-details style="margin-top:10px"></v-checkbox>
                      <v-checkbox readonly v-model="exportEvents" label="Export Events" hide-details style="margin-top:10px"></v-checkbox>
                    </v-card-text>
                  </v-card>
                </div>
                <div style="margin-left:15px; margin-top:20px; margin-bottom:5px">
                  <v-btn :disabled="loading" :loading="loading" @click="submitClone" color="#00b16a">CLONE</v-btn>
                  <v-btn :disabled="loading" @click="mode == 'full' ? stepper -= 2 : stepper -= 1" color="#EF5354" style="margin-left:5px">CANCEL</v-btn>
                </div>
              </v-stepper-content>
            </v-stepper>
          </v-flex>
        </v-layout>
      </v-container>
    </v-card>
    <!------------------->
    <!-- SERVER DIALOG -->
    <!------------------->
    <v-dialog v-model="serverDialog" max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1">SERVER</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn readonly title="Create the server only for a user" :color="!serverItem.shared ? 'primary' : '#779ecb'" style="margin-right:10px;"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-user</v-icon>Personal</v-btn>
          <v-btn readonly title="Create the server for all users in a group" :color="serverItem.shared ? 'primary' : '#779ecb'"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-users</v-icon>Shared</v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="serverDialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-progress-linear v-show="loading" indeterminate></v-progress-linear>
        <v-card-text style="padding: 0px 15px 15px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:15px">
                  <v-row no-gutters>
                    <v-col cols="6" style="padding-right:10px">
                      <v-text-field readonly v-model="serverItem.name" label="Name"></v-text-field>
                    </v-col>
                    <v-col cols="6" style="padding-left:10px">
                      <v-text-field readonly v-model="serverItem.region" label="Region">
                        <template v-slot:prepend-inner>
                          <v-icon small :color="serverItem.region_shared ? '#EB5F5D' : 'warning'" style="margin-top:4px; margin-right:5px">{{ serverItem.region_shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                        </template>
                      </v-text-field>
                    </v-col>
                  </v-row>
                  <v-row no-gutters>
                    <v-col cols="8" style="padding-right:10px">
                      <v-text-field readonly v-model="serverItem.engine" label="Engine" style="padding-top:0px;"></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-left:10px">
                      <v-text-field readonly v-model="serverItem.version" label="Version" style="padding-top:0px;"></v-text-field>
                    </v-col>
                  </v-row>
                  <div v-if="!(readOnly && inventory_secured)" style="margin-bottom:20px">
                    <v-row no-gutters>
                      <v-col cols="8" style="padding-right:10px">
                        <v-text-field readonly v-model="serverItem.hostname" label="Hostname" style="padding-top:0px;"></v-text-field>
                      </v-col>
                      <v-col cols="4" style="padding-left:10px">
                        <v-text-field readonly v-model="serverItem.port" label="Port" style="padding-top:0px;"></v-text-field>
                      </v-col>
                    </v-row>
                    <v-text-field readonly v-model="serverItem.username" label="Username" style="padding-top:0px;"></v-text-field>
                    <v-text-field readonly v-model="serverItem.password" label="Password" :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'" :type="showPassword ? 'text' : 'password'" @click:append="showPassword = !showPassword" style="padding-top:0px;" hide-details></v-text-field>
                    <v-text-field readonly outlined v-model="serverItem.usage" label="Usage" hide-details style="margin-top:20px"></v-text-field>
                  </div>
                </v-form>
                <v-divider></v-divider>
                <v-row no-gutters style="margin-top:20px;">
                  <v-col>
                    <v-btn :loading="loading" color="info" @click="testConnection()">Test Connection</v-btn>
                  </v-col>
                </v-row>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<style scoped src="@/styles/agGridVue.css"></style>

<style scoped>
@import "../../../../node_modules/ag-grid-community/dist/styles/ag-grid.css";
@import "../../../../node_modules/ag-grid-community/dist/styles/ag-theme-alpine-dark.css";
</style>

<script>
import axios from 'axios';
import {AgGridVue} from "ag-grid-vue";
import pretty from 'pretty-bytes';

export default {
  data() {
    return {
      loading: false,
      stepper: 1,
      // Source
      serverItems: [],
      server: null,
      databaseItems: [],
      database: null,
      databaseSize: null,
      tableSize: 0,
      // Setup
      mode: 'full',
      format: 'sql',
      exportSchema: true,
      exportData: true,
      addDropTable: true,
      // Objects
      tab: 0,
      gridApi: null,
      columnApi: null,
      defaultColDef: {
        flex: 1,
        minWidth: 100,
        resizable: true,
        headerCheckboxSelection: (params) => { return params.columnApi.getAllDisplayedColumns()[0] === params.column },
        checkboxSelection: (params) => { return params.columnApi.getAllDisplayedColumns()[0] === params.column },
      },
      tablesHeaders: [],
      tablesItems: [],
      tablesSelected: [],
      exportTriggers: false,
      exportRoutines: false,
      exportEvents: false,
      // Overview
      gridApi2: null,
      columnApi2: null,
      defaultColDef2: {
        flex: 1,
        editable: false,
        minWidth: 100,
        resizable: true,
      },
      // Server Dialog
      serverDialog: false,
      serverItem: {},
      showPassword: false,
      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarText: '',
      snackbarColor: '',
      // Previous Route
      prevRoute: null
    }
  },
  components: { AgGridVue },
  beforeRouteEnter(to, from, next) {
    next(vm => {
      vm.prevRoute = from
    })
  },
  computed: {
    owner: function() { return this.$store.getters['app/owner'] },
    inventory_secured: function() { return this.$store.getters['app/inventory_secured'] },
    readOnly: function() { return !this.owner && (Object.keys(this.serverItem).length == 0 || this.serverItem.shared == 1) },
  },
  created() {
    this.getServers()
  },
  methods: {
    getServers() {
      this.loading = true
      axios.get('/utils/clones/servers')
        .then((response) => {
          this.serverItems = response.data.servers
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    getDatabases() {
      if (this.server == null) this.databaseItems = []
      else {
        this.loading = true
        const payload = { server_id: this.server }
        axios.get('/utils/clones/databases', { params: payload })
          .then((response) => {
            this.databaseItems = response.data.databases
            this.$nextTick(() => {
              this.$refs.sourceForm.resetValidation()
              this.$refs.server.blur()
              this.$refs.database.focus()
            })
          })
          .catch((error) => {
            this.databaseItems = []
            this.database = null
            if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
            else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
          })
          .finally(() => this.loading = false)
      }
    },
    getDatabaseSize() {
      this.databaseSize = null
      if (this.database == null) return
      this.loading = true
      const payload = { server_id: this.server, database: this.database }
      axios.get('/utils/clones/databases/size', { params: payload })
        .then((response) => {
          this.databaseSize = response.data.size
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    getServer(server_id) {
      // Get Server
      this.loading = true
      this.showPassword = false
      this.serverDialog = true
      const payload = { server_id: server_id }
      axios.get('/inventory/servers', { params: payload })
        .then((response) => {
          // Build usage
          let usage = []
          if (response.data.data[0].usage.includes('D')) usage.push('Deployments')
          if (response.data.data[0].usage.includes('M')) usage.push('Monitoring')
          if (response.data.data[0].usage.includes('U')) usage.push('Utils')
          if (response.data.data[0].usage.includes('C')) usage.push('Client')
          // Add server
          this.serverItem = {...response.data.data[0], usage: usage.join(', ')}
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    testConnection() {
      // Test Connection
      this.notification('Testing Server...', 'info')
      this.loading = true
      const payload = {
        region: this.serverItem.region_id,
        server: this.serverItem.id
      }
      axios.post('/inventory/servers/test', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    getTables(force) {
      if (!force && this.tablesItems.length != 0) return
      this.loading = true
      this.gridApi.showLoadingOverlay()
      const payload = { server_id: this.server, database: this.database }
      axios.get('/utils/clones/tables', { params: payload })
        .then((response) => {
          this.parseTables(response.data.tables)
          this.resizeTable()
          this.gridApi.hideOverlay()
          this.tablesSelected = []
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    parseTables(tables) {
      this.tablesHeaders = []
      this.tablesItems = []
      if (tables.length > 0) {
        for (let [key] of Object.entries(tables[0])) {
          let column = { headerName: this.parseHeaderName(key), colId: key.trim(), field: key.trim(), sortable: true, filter: true, resizable: true, editable: false }
          if (['data_length','index_length','total_length'].includes(key)) {
            column.valueFormatter = (params) => {
              return this.formatBytes(params.data[params.colDef.field])
            }
            column.comparator = this.compareValues
          }
          this.tablesHeaders.push(column)
        }
        this.tablesItems = tables
      }
    },
    parseHeaderName(rawName) {
      return rawName.replaceAll('_',' ').split(' ').map(x => x[0].toUpperCase() + x.substr(1)).join(" ").trim()
    },
    formatBytes(size) {
      if (size == null) return null
      return pretty(size, {binary: true}).replace('i','')
    },
    onGridReady(params) {
      this.gridApi = params.api
      this.columnApi = params.columnApi
    },
    onGridReady2(params) {
      this.gridApi2 = params.api
      this.columnApi2 = params.columnApi
    },
    onSelectionChanged() {
      this.tablesSelected = this.gridApi.getSelectedRows()
      this.tableSize = this.gridApi.getSelectedRows().reduce((acc, val) => acc += val.data_length,0)
    },
    resizeTable() {
      setTimeout(() => {
        var allColumnIds = [];
        this.columnApi.getAllColumns().forEach(function(column) {
          allColumnIds.push(column.colId);
        })
        this.columnApi.autoSizeColumns(allColumnIds);
      },0)
    },
    resizeTable2() {
      setTimeout(() => {
        var allColumnIds = [];
        this.columnApi2.getAllColumns().forEach(function(column) {
          allColumnIds.push(column.colId);
        })
        this.columnApi2.autoSizeColumns(allColumnIds);
      },0)
    },
    submitClone() {
      this.loading = true
      const payload = {
        origin_schema: this.originSchema,
        origin_database: this.originDatabase,
        destination_schema: this.destinationSchema,
        destination_database: this.destinationDatabase,
        mode: this.mode,
        format: this.format,
        tables: this.mode == 'full' ? null : this.gridApi.getSelectedRows().map((val) => ({ n: val.name, r: val.rows, s: val.data_length })),
        export_schema: this.exportSchema,
        export_data: this.exportData,
        add_drop_table: !this.exportSchema ? false : this.addDropTable,
        export_triggers: this.exportTriggers,
        export_routines: this.exportRoutines,
        export_events: this.exportEvents,
        size: this.mode == 'full' ? this.databaseSize : this.tableSize,
        url: window.location.protocol + '//' + window.location.host
      }
      axios.post('/utils/clones', payload)
      .then((response) => {
        this.$router.push('/utils/clones/' + response.data.uri)
      })
      .catch((error) => {
        if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
        else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
      })
      .finally(() => this.loading = false)
    },
    nextStep() {
      if (this.stepper == 1) {
        if (!this.$refs.sourceForm.validate()) return
        this.stepper += 1
      }
      else if (this.stepper == 2) {
        if (this.mode == 'partial') { this.getTables(false); this.stepper += 1 }
        else this.stepper += 2
      }
      else if (this.stepper == 3) {
        if (this.tablesSelected.length == 0) {
          this.notification('Please select at least one table to clone', '#EF5354')
          return
        }
        this.stepper += 1
        this.resizeTable2()
      }
    },
    onSearch(value) {
      this.gridApi.setQuickFilter(value)
    },
    onSearch2(value) {
      this.gridApi2.setQuickFilter(value)
    },
    goBack() {
      if (this.prevRoute.path == '/admin/utils/clones') this.$router.push('/admin/utils/clones')
      else this.$router.push('/utils/clones')
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  }
}
</script>