<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">QUERIES</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn :disabled="loading" text title="Define monitoring rules and settings" @click="openSettings()" class="body-2"><v-icon small style="padding-right:10px">fas fa-cog</v-icon>SETTINGS</v-btn>
          <v-btn :disabled="loading" text title="Select servers to monitor" @click="openServers()" class="body-2"><v-icon small style="padding-right:10px">fas fa-database</v-icon>SERVERS</v-btn>
          <v-btn :disabled="loading" text title="Filter queries" @click="filter_dialog = true" class="body-2" :style="{ backgroundColor : filter_applied ? '#4ba2f1' : '' }"><v-icon small style="padding-right:10px">fas fa-sliders-h</v-icon>FILTER</v-btn>
          <v-btn :disabled="loading" text title="Refresh query list" @click="getQueries()" class="body-2"><v-icon small style="padding-right:10px">fas fa-sync-alt</v-icon>REFRESH</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
        </v-toolbar-items>
        <v-text-field v-model="queries_search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
        <v-divider class="mx-3" inset vertical style="margin-right:4px!important"></v-divider>
        <v-btn @click="filterColumnsClick" icon title="Show/Hide columns" style="margin-right:-10px; width:40px; height:40px;"><v-icon small>fas fa-cog</v-icon></v-btn>
      </v-toolbar>
      <v-data-table :headers="computedHeaders" :items="queries_items" :options.sync="queries_options" :server-items-length="queries_total" :hide-default-footer="queries_total < 11" multi-sort :loading="loading" class="elevation-1" style="padding-top:5px;">
        <template v-slot:[`item.first_seen`]="{ item }">
          {{ dateFormat(item.first_seen) }}
        </template>
        <template v-slot:[`item.last_seen`]="{ item }">
          {{ dateFormat(item.last_seen) }}
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="settings_dialog" max-width="50%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="padding-right:10px; padding-bottom:3px">fas fa-cog</v-icon>SETTINGS</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="settings_dialog = false" style="width:40px; height:40px"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-bottom:15px;">
                  <v-text-field filled v-model="settings.query_execution_time" label="Minimum Execution Time (seconds)" required :rules="[v => v == parseInt(v) && v > 0 || '']" style="margin-bottom:10px;" hide-details></v-text-field>
                  <v-text-field filled v-model="settings.query_data_retention" label="Data Retention Timeframe (hours)" required :rules="[v => v == parseInt(v) && v > 0 || '']" style="margin-top:15px; margin-bottom:10px;" hide-details></v-text-field>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-btn :loading="loading" color="#00b16a" @click="submitSettings()">CONFIRM</v-btn>
                  <v-btn :disabled="loading" color="error" @click="settings_dialog=false" style="margin-left:5px;">CANCEL</v-btn>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="servers_dialog" max-width="896px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="padding-right:10px; padding-bottom:3px">fas fa-database</v-icon>SERVERS</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="servers_dialog = false" style="width:40px; height:40px"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 20px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:15px; margin-bottom:15px;">
                  <v-card>
                    <v-toolbar flat dense color="#2e3131">
                      <v-text-field v-model="treeviewSearch" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
                    </v-toolbar>
                    <v-card-text style="padding: 10px;">
                      <div v-if="treeviewItems.length == 0" class="body-2" style="text-align:center">No servers available</div>
                      <v-treeview v-else :active.sync="treeviewSelectedRaw" item-key="id" :items="treeviewItems" :open="treeviewOpenedRaw" :search="treeviewSearch" hoverable open-on-click multiple-active activatable transition>
                        <template v-slot:prepend="{ item }">
                          <v-icon v-if="!item.children" small>fas fa-database</v-icon>
                        </template>
                        <template v-slot:append="{ item }">
                          <v-chip v-if="!item.children" label><v-icon small :color="item.shared ? 'error' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>{{ item.shared ? 'Shared' : 'Personal' }}</v-chip>
                        </template>
                      </v-treeview>
                    </v-card-text>
                  </v-card>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :loading="loading" color="#00b16a" @click="submitServers()">CONFIRM</v-btn>
                  <v-btn :disabled="loading" color="error" @click="servers_dialog=false" style="margin-left:5px;">CANCEL</v-btn>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="filter_dialog" max-width="50%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="padding-right:10px; padding-bottom:3px">fas fa-sliders-h</v-icon>FILTER</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="filter_dialog = false" style="width:40px; height:40px"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 10px 15px 15px 15px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:10px; margin-bottom:20px;">
                  <v-row>
                    <v-col cols="8" style="padding-right:5px;">
                      <v-text-field text v-model="filter.query_text" label="Query" required style="padding-top:0px;" hide-details></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-left:5px;">
                      <v-select text v-model="filter.query_text_options" label="Filter" :items="filter_options" :rules="[v => ((filter.query_text === undefined || filter.query_text.length == 0) || (filter.query_text.length > 0 && !!v)) || '']" style="padding-top:0px;" hide-details></v-select>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="8" style="padding-right:5px;">
                      <v-text-field text v-model="filter.db" label="Database" required style="padding-top:0px;" hide-details></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-left:5px;">
                      <v-select text v-model="filter.db_options" label="Filter" :items="filter_options" :rules="[v => ((filter.db === undefined || filter.db.length == 0) || (filter.db.length > 0 && !!v)) || '']" style="padding-top:0px;" hide-details></v-select>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="8" style="padding-right:5px;">
                      <v-text-field text v-model="filter.server" label="Server" required style="padding-top:0px;" hide-details></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-left:5px;">
                      <v-select text v-model="filter.server_options" label="Filter" :items="filter_options" :rules="[v => ((filter.server === undefined || filter.server.length == 0) || (filter.server.length > 0 && !!v)) || '']" style="padding-top:0px;" hide-details></v-select>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="8" style="padding-right:5px;">
                      <v-text-field text v-model="filter.user" label="User" required style="padding-top:0px;" hide-details></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-left:5px;">
                      <v-select text v-model="filter.user_options" label="Filter" :items="filter_options" :rules="[v => ((filter.user === undefined || filter.user.length == 0) || (filter.user.length > 0 && !!v)) || '']" style="padding-top:0px;" hide-details></v-select>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="8" style="padding-right:5px;">
                      <v-text-field text v-model="filter.host" label="Host" required style="padding-top:0px;" hide-details></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-left:5px;">
                      <v-select text v-model="filter.host_options" label="Filter" :items="filter_options" :rules="[v => ((filter.host === undefined || filter.host.length == 0) || (filter.host.length > 0 && !!v)) || '']" style="padding-top:0px;" hide-details></v-select>
                    </v-col>
                  </v-row>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :loading="loading" color="#00b16a" @click="submitFilter()">CONFIRM</v-btn>
                  <v-btn :disabled="loading" color="error" @click="cancelFilter()" style="margin-left:5px;">CANCEL</v-btn>
                  <v-btn v-if="filter_applied" :disabled="loading" color="info" @click="clearFilter()" style="float:right;">Remove Filter</v-btn>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!-------------------->
    <!-- COLUMNS DIALOG -->
    <!-------------------->
    <v-dialog v-model="columnsDialog" max-width="600px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1">FILTER COLUMNS</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="selectAllColumns" text title="Select all columns" style="height:100%"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-check-square</v-icon>Select all</v-btn>
          <v-btn @click="deselectAllColumns" text title="Deselect all columns" style="height:100%"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-square</v-icon>Deselect all</v-btn>
          <v-spacer></v-spacer>
          <v-btn icon @click="columnsDialog = false" style="width:40px; height:40px"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 0px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:15px; margin-bottom:20px;">
                  <div class="text-body-1" style="margin-bottom:10px">Select the columns to display:</div>
                  <v-checkbox v-model="columnsRaw" label="Query" value="query_text" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Database" value="db" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Server" value="server" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="User" value="user" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Host" value="host" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="First Seen" value="first_seen" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Last Seen" value="last_seen" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Last Execution Time" value="last_execution_time" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Max Execution Time" value="max_execution_time" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Avg Execution Time" value="avg_execution_time" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Count" value="count" hide-details style="margin-top:5px"></v-checkbox>
                  <v-divider style="margin-top:15px;"></v-divider>
                  <div style="margin-top:20px;">
                    <v-btn @click="filterColumns" :loading="loading" color="#00b16a">Confirm</v-btn>
                    <v-btn :disabled="loading" color="error" @click="columnsDialog = false" style="margin-left:5px;">Cancel</v-btn>
                  </div>
                </v-form>
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

<style>

</style>

<script>
import axios from 'axios'
import moment from 'moment'

export default {
  data: () => ({
    loading: true,

    // Queries
    queries_headers: [
      { text: 'Query', align: 'left', value: 'query_text', sortable: false },
      { text: 'Database', align: 'left', value: 'db', width: '1%' },
      { text: 'Server', align: 'left', value: 'server', width: '1%' },
      { text: 'User', align: 'left', value: 'user', width: '1%' },
      { text: 'Host', align: 'left', value: 'host', width: '1%' },
      { text: 'First Seen', align: 'left', value: 'first_seen', width: '1%' },
      { text: 'Last Seen', align: 'left', value: 'last_seen', width: '1%' },
      { text: 'Last Execution Time', align: 'left', value: 'last_execution_time', width: '1%' },
      { text: 'Max Execution Time', align: 'left', value: 'max_execution_time', width: '1%' },
      { text: 'Avg Execution Time', align: 'left', value: 'avg_execution_time', width: '1%' },
      { text: 'Count', align: 'left', value: 'count', width: '1%' }
    ],
    queries_origin: [],
    queries_items: [],
    queries_search: '',
    queries_total: 0,
    queries_options: {},

    // Settings Dialog
    settings_dialog: false,        
    settings: { query_execution_time: '10', query_data_retention: '24' },
    execution_time: '10',
    data_retention: '24',

    // Servers Dialog
    servers_dialog: false,
    treeviewItems: [],
    treeviewSelected: [],
    treeviewSelectedRaw: [],
    treeviewOpened: [],
    treeviewOpenedRaw: [],
    treeviewSearch: '',
    submit_servers: true,

    // Filter Dialog
    filter_dialog: false,
    filter: {},
    filter_options: ['Equal', 'Not equal', 'Starts', 'Not starts'],
    filter_applied: false,

    // Filter Columns Dialog
    columnsDialog: false,
    columns: ['query_text','db','server','user','last_seen','last_execution_time','count'],
    columnsRaw: [],

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarColor: '',
    snackbarText: ''
  }),
  computed: {
    computedHeaders() { return this.queries_headers.filter(x => this.columns.includes(x.value)) }
  },
  methods: {
    getQueries() {
      // Init vars
      this.loading = true

      // Build query options
      const { sortBy, sortDesc, page, itemsPerPage } = this.queries_options

      // Build filter    
      const filter = this.filter

      // Build sort
      const sort = (sortBy.length > 0) ? [sortBy, sortDesc] : []

      // Get queries
      axios.get('/monitoring/queries', { params: { filter: JSON.stringify(filter), sort: JSON.stringify(sort) }})
        .then((response) => {
          // First time
          if (this.submit_servers) {
            this.parseSettings(response.data.settings)
            this.parseTreeView(response.data.servers)
            this.submit_servers = false
          }
          let items = response.data.queries
          this.queries_total = items.length
          if (itemsPerPage > 0) items = items.slice((page - 1) * itemsPerPage, page * itemsPerPage)
          this.queries_origin = items
          this.queries_items = items
          // Apply search
          this.applySearch(this.queries_search)
          this.loading = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
    },
    parseSettings(settings) {
      if (settings.length > 0) {
        this.settings.query_execution_time = this.execution_time = settings[0]['query_execution_time']
        this.settings.query_data_retention = this.data_retention = settings[0]['query_data_retention']
      }
    },
    parseTreeView(servers) {
      var data = []
      var selected = []
      var opened = []
      if (servers.length == 0) return data

      // Parse Servers
      var current_region = null
      for (let i = 0; i < servers.length; ++i) {
        if ('r' + servers[i]['region_id'] != current_region) {
          data.push({ id: 'r' + servers[i]['region_id'], name: servers[i]['region_name'], children: [{ id: servers[i]['server_id'], name: servers[i]['server_name'], shared: servers[i]['server_shared'] }] })
          current_region = 'r' + servers[i]['region_id']
        } else {
          let row = data.pop()
          row['children'].push({ id: servers[i]['server_id'], name: servers[i]['server_name'], shared: servers[i]['server_shared'] })
          data.push(row)
        }
        // Check selected
        if (servers[i]['selected']) {
          selected.push(servers[i]['server_id'])
          opened.push('r' + servers[i]['region_id'])
        }
      }
      if (!this.servers_dialog) {
        this.treeviewItems = data
        this.treeviewSelected = selected
        this.treeviewOpened = opened
      }
    },
    openSettings() {
      this.settings = { query_execution_time: this.execution_time, query_data_retention: this.data_retention },
      this.settings_dialog = true
    },
    submitSettings() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        return
      }
      // Update settings        
      this.loading = true
      const payload = this.settings
      axios.put('/monitoring/settings', payload)
        .then((response) => {
          this.execution_time = this.settings.query_execution_time
          this.data_retention = this.settings.query_data_retention
          this.notification(response.data.message, '#00b16a')
          this.settings_dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
    },
    cancelFilter() {
      if (!this.filter_applied) this.filter = {}
      this.filter_dialog = false
    },
    openServers() {
      this.treeviewSelectedRaw = JSON.parse(JSON.stringify(this.treeviewSelected))
      this.treeviewOpenedRaw = JSON.parse(JSON.stringify(this.treeviewOpened))
      this.servers_dialog = true
    },
    submitServers() {
      this.loading = true
      const payload = this.treeviewSelectedRaw
      axios.put('/monitoring/queries', payload)
        .then((response) => {
          this.treeviewSelected = JSON.parse(JSON.stringify(this.treeviewSelectedRaw))
          this.treeviewOpened = JSON.parse(JSON.stringify(this.treeviewOpenedRaw))
          this.notification(response.data.message, '#00b16a')
          this.servers_dialog = false
          this.submit_servers = true
          this.getQueries()
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
    },
    submitFilter() {
      this.loading = true
      // Check if all fields are filled
      if (
        (this.filter.query_text === undefined || this.filter.query_text.length == 0) &&
        (this.filter.db === undefined || this.filter.db.length == 0) &&
        (this.filter.server === undefined || this.filter.server.length == 0) &&
        (this.filter.user === undefined || this.filter.user.length == 0) &&
        (this.filter.host === undefined || this.filter.host.length == 0)
      ) {
        this.notification('Please enter at least one filter', 'error')
        this.loading = false
        return
      }
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      // Apply filter
      this.filter_applied = true
      this.getQueries()
      this.filter_dialog = false
    },
    clearFilter() {
      this.loading = true
      this.filter = {}
      this.filter_applied = false
      this.getQueries()
      this.filter_dialog = false
    },
    applySearch(newValue) {
      if (newValue.length == 0) this.queries_items = this.queries_origin.slice(0)
      else {
        let items = []
        for (let i in this.queries_origin) {
          let keys = Object.keys(this.queries_origin[i])
          for (let k in keys) {
            if (this.queries_origin[i][keys[k]].toString().includes(newValue)) { items.push(this.queries_origin[i]); break; }
          }
        }
        this.queries_items = items
      }
    },
    filterColumnsClick() {
      this.columnsRaw = [...this.columns]
      this.columnsDialog = true
    },
    filterColumns() {
      this.columns = [...this.columnsRaw]
      this.columnsDialog = false
    },
    selectAllColumns() {
      this.columnsRaw = ['query_text','db','server','user','host','first_seen','last_seen','last_execution_time','max_execution_time','avg_execution_time','count']
    },
    deselectAllColumns() {
      this.columnsRaw = []
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
  },
  watch: {
    queries_options: {
      handler () { this.getQueries() },
      deep: true
    },
    // eslint-disable-next-line
    queries_search: function (newValue, oldValue) {
      this.applySearch(newValue)
    }
  }
}
</script>