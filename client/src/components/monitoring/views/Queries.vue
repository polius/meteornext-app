<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">QUERIES</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text title="Define monitoring rules and settings" @click="settings_dialog=true" class="body-2"><v-icon small style="padding-right:10px">fas fa-cog</v-icon>SETTINGS</v-btn>
          <v-btn text title="Select servers to monitor" @click="servers_dialog=true" class="body-2"><v-icon small style="padding-right:10px">fas fa-database</v-icon>SERVERS</v-btn>
          <v-btn text title="Filter queries" @click="filter_dialog=true" class="body-2"><v-icon small style="padding-right:10px">fas fa-sliders-h</v-icon>FILTER</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
        </v-toolbar-items>
        <v-text-field v-model="queries_search" append-icon="search" label="Search" color="white" style="margin-left:10px;" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table :headers="queries_headers" :items="queries_items" :options.sync="queries_options" :server-items-length="queries_total" :hide-default-footer="queries_items.length < 11" multi-sort :loading="loading" class="elevation-1" style="padding-top:5px;">
        <template v-slot:item.first_seen="props">
          <span>{{ dateFormat(props.item.first_seen) }}</span>
        </template>
        <template v-slot:item.last_seen="props">
          <span>{{ dateFormat(props.item.last_seen) }}</span>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="settings_dialog" persistent max-width="50%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">SETTINGS</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="settings_dialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-bottom:15px;">
                  <v-text-field filled v-model="settings.query_execution_time" label="Minimum Execution Time (seconds)" required :rules="[v => v == parseInt(v) && v > 0 || '']" style="margin-bottom:10px;" hide-details></v-text-field>
                  <v-text-field filled v-model="settings.query_data_retention" label="Data Retention Timeframe (days)" required :rules="[v => v == parseInt(v) && v > 0 || '']" style="margin-top:15px; margin-bottom:10px;" hide-details></v-text-field>
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

    <v-dialog v-model="servers_dialog" persistent max-width="896px">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">SERVERS</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="servers_dialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
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
                      <v-treeview :active.sync="treeviewSelected" item-key="id" :items="treeviewItems" :open="treeviewOpened" :search="treeviewSearch" hoverable open-on-click multiple-active activatable transition>
                        <template v-slot:prepend="{ item }">
                          <v-icon v-if="!item.children" small>fas fa-database</v-icon>
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

    <v-dialog v-model="filter_dialog" persistent max-width="50%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">FILTER</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="filter_dialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 15px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-bottom:10px;">
                  <v-row>
                    <v-col cols="8" style="padding-top:5px;">
                      <v-text-field text v-model="filter.query_text" label="Query" required style="padding-top:0px;" hide-details></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-top:5px;">
                      <v-select text v-model="filter.query_text_options" label="Filter" :items="filter_options" :rules="[v => ((filter.query_text === undefined || filter.query_text.length == 0) || (filter.query_text.length > 0 && !!v)) || '']" style="padding-top:0px;" hide-details></v-select>
                    </v-col>
                  </v-row>
                  <v-row>
                    <v-col cols="8" style="padding-top:0px;">
                      <v-text-field text v-model="filter.db" label="Database" required hide-details></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-top:0px;">
                      <v-select text v-model="filter.db_options" label="Filter" :items="filter_options" :rules="[v => ((filter.db === undefined || filter.db.length == 0) || (filter.db.length > 0 && !!v)) || '']" hide-details></v-select>
                    </v-col>
                  </v-row>
                  <v-row>
                    <v-col cols="8" style="padding-top:0px;">
                      <v-text-field text v-model="filter.server" label="Server" required hide-details></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-top:0px;">
                      <v-select text v-model="filter.server_options" label="Filter" :items="filter_options" :rules="[v => ((filter.server === undefined || filter.server.length == 0) || (filter.server.length > 0 && !!v)) || '']" hide-details></v-select>
                    </v-col>
                  </v-row>
                  <v-row>
                    <v-col cols="8" style="padding-top:0px;">
                      <v-text-field text v-model="filter.user" label="User" required hide-details></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-top:0px;">
                      <v-select text v-model="filter.user_options" label="Filter" :items="filter_options" :rules="[v => ((filter.user === undefined || filter.user.length == 0) || (filter.user.length > 0 && !!v)) || '']" hide-details></v-select>
                    </v-col>
                  </v-row>
                  <v-row>
                    <v-col cols="8" style="padding-top:0px;">
                      <v-text-field text v-model="filter.host" label="Host" required hide-details></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-top:0px;">
                      <v-select text v-model="filter.host_options" label="Filter" :items="filter_options" :rules="[v => ((filter.host === undefined || filter.host.length == 0) || (filter.host.length > 0 && !!v)) || '']" hide-details></v-select>
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

    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn color="white" text @click="snackbar = false">Close</v-btn>
    </v-snackbar>
  </div>
</template>

<script>
import axios from 'axios'
import moment from 'moment'

export default {
  data: () => ({
    loading: true,

    // Queries
    queries_headers: [
      { text: 'Query', align: 'left', value: 'query_text' },
      { text: 'Database', align: 'left', value: 'db' },
      { text: 'Server', align: 'left', value: 'server' },
      { text: 'User', align: 'left', value: 'user' },
      { text: 'Host', align: 'left', value: 'host' },
      { text: 'First Seen', align: 'left', value: 'first_seen' },
      { text: 'Last Seen', align: 'left', value: 'last_seen' },
      { text: 'Last Execution Time', align: 'left', value: 'last_execution_time' },
      { text: 'Max Execution Time', align: 'left', value: 'max_execution_time' },
      { text: 'Avg Execution Time', align: 'left', value: 'avg_execution_time' },
      { text: 'Count', align: 'left', value: 'count' }
    ],
    queries_origin: [],
    queries_items: [],
    queries_search: '',
    queries_total: 0,
    queries_options: {},

    // Settings Dialog
    settings_dialog: false,        
    settings: { query_execution_time:'10', query_data_retention:'1' },
    execution_time: '10',
    data_retention: '1',

    // Servers Dialog
    servers_dialog: false,
    treeviewItems: [],
    treeviewSelected: [],
    treeviewOpened: [],
    treeviewSearch: '',
    submit_servers: false,

    // Filter Dialog
    filter_dialog: false,
    filter: {},
    filter_options: ['Equal', 'Not equal', 'Starts', 'Not starts'],
    filter_applied: false,

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarColor: '',
    snackbarText: ''
  }),
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
          if (this.submit_servers || (Object.keys(filter).length == 0 && Object.keys(sort).length == 0)) {
            this.parseSettings(response.data.settings)
            this.parseTreeView(response.data.servers)
            this.submit_servers = false
          }
          let items = response.data.queries

          if (itemsPerPage > 0) {
            items = items.slice((page - 1) * itemsPerPage, page * itemsPerPage)
          }
          this.queries_origin = items
          this.queries_items = items
          this.queries_total = items.length
          // Apply search
          this.applySearch(this.queries_search)
          this.loading = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
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
          data.push({ id: 'r' + servers[i]['region_id'], name: servers[i]['region_name'], children: [{ id: servers[i]['server_id'], name: servers[i]['server_name'] }] })
          current_region = 'r' + servers[i]['region_id']
        } else {
          let row = data.pop()
          row['children'].push({ id: servers[i]['server_id'], name: servers[i]['server_name'] })
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
    submitSettings() {
      this.loading = true
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      // Update settings        
      const payload = JSON.stringify(this.settings)
      axios.put('/monitoring/settings', payload)
        .then((response) => {
          this.execution_time = this.settings.query_execution_time
          this.data_retention = this.settings.query_data_retention
          this.notification(response.data.message, '#00b16a')
          this.settings_dialog = false
          this.loading = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    cancelFilter() {
      if (!this.filter_applied) this.filter = {}
      this.filter_dialog = false
    },
    submitServers() {
      this.loading = true
      const payload = JSON.stringify(this.treeviewSelected)
      axios.put('/monitoring/queries', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.servers_dialog = false
          this.submit_servers = true
          this.getQueries()
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
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