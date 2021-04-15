<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:3px">fas fa-database</v-icon>{{ server_name }}</v-toolbar-title>
        <div v-if="region_name.length > 0" class="subheading font-weight-regular" style="margin-left:5px">({{ region_name }})</div>
        <v-divider class="mx-3" inset vertical></v-divider>
        <div class="subheading font-weight-regular">{{ server_hostname }}</div>
        <v-spacer></v-spacer>
        <div v-if="updated != null" class="subheading font-weight-regular" style="padding-right:10px;">Updated on <b>{{ dateFormat(updated) }}</b></div>
        <v-btn icon @click="goBack()"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
      </v-toolbar>

      <v-card-text style="padding-top:10px;">
        <v-card style="margin-bottom:10px;">
          <v-toolbar flat dense color="#424242">
            <v-toolbar-title v-if="!loading && server_name != ''" class="body-1" style="font-size:15px!important;"><v-icon small :title="available ? 'Available' : 'Unavailable'" :color="available ? 'success' : 'error'" style="margin-bottom:2px; margin-right:15px;">fas fa-circle</v-icon>{{ available ? 'Server up and running' : error }}</v-toolbar-title>
          </v-toolbar>
        </v-card>

        <!-- MONITOR - BAR -->
        <div>
          <v-tabs show-arrows background-color="#263238" color="white" v-model="tabs" slider-color="white" slot="extension" class="elevation-2">
            <v-tabs-slider></v-tabs-slider>
            <v-tab><span class="pl-2 pr-2">GENERAL INFO</span></v-tab>
            <v-divider class="mx-3" inset vertical></v-divider>
            <v-tab><span class="pl-2 pr-2">LOGS</span></v-tab>
            <v-divider class="mx-3" inset vertical></v-divider>
            <v-tab><span class="pl-2 pr-2">CONNECTIONS</span></v-tab>
            <v-divider class="mx-3" inset vertical></v-divider>
            <v-tab><span class="pl-2 pr-2">STATEMENTS</span></v-tab>
            <v-divider class="mx-3" inset vertical></v-divider>
            <v-tab><span class="pl-2 pr-2">INDEX USAGE</span></v-tab> 
            <v-divider class="mx-3" inset vertical></v-divider>
          </v-tabs>
        </div>

        <!-- SUMMARY -->
        <v-card v-show="tabs == 0">
          <v-data-table :headers="summary_headers" :items="summary_items" hide-default-footer class="elevation-1">
            <template v-slot:[`item.available`]="{ item }">
              <span v-if="item.available == 1">Yes</span>
              <span v-else-if="item.available == 0">No</span>
              <span v-else-if="item.available == -1">Loading</span>
            </template>
          </v-data-table>
        </v-card>

        <!-- LOGS -->
        <v-card v-show="tabs == 1">
          <v-data-table :headers="logs_headers" :items="logs_items" hide-default-footer class="elevation-1">
            <template v-slot:[`item.general_log`]="{ item }">
              <span v-if="item.general_log == 'ON'"><v-icon small color="#00b16a" style="margin-right:10px; margin-bottom:2px;">fas fa-circle</v-icon>On</span>
              <span v-else><v-icon small color="error" style="margin-right:10px; margin-bottom:2px;">fas fa-circle</v-icon>Off</span>
            </template>
            <template v-slot:[`item.slow_log`]="{ item }">
              <span v-if="item.slow_log == 'ON'"><v-icon small color="#00b16a" style="margin-right:10px; margin-bottom:2px;">fas fa-circle</v-icon>On</span>
              <span v-else><v-icon small color="error" style="margin-right:10px; margin-bottom:2px;">fas fa-circle</v-icon>Off</span>
            </template>
          </v-data-table>
        </v-card>

        <!-- CONNECTIONS -->
        <v-card v-show="tabs == 2">
          <v-data-table :headers="connections_headers" :items="connections_items" hide-default-footer class="elevation-1">
          </v-data-table>
        </v-card>

        <!-- STATEMENTS -->
        <v-card v-show="tabs == 3">
          <v-data-table :headers="statements_headers" :items="statements_items" hide-default-footer class="elevation-1">
          </v-data-table>
        </v-card>

        <!-- INDEXES -->
        <v-card v-show="tabs == 4">
          <v-data-table :headers="indexes_headers" :items="indexes_items" hide-default-footer class="elevation-1">
          </v-data-table>
        </v-card>

        <!-- PARAMETERS -->
        <v-card style="margin-top:15px; margin-bottom:10px;">
          <v-toolbar dense flat color="#263238">
            <v-toolbar-title class="white--text subtitle-1">PARAMETERS</v-toolbar-title>
            <v-divider class="mx-3" inset vertical></v-divider>
            <v-text-field v-model="params_search" append-icon="search" label="Search" color="white" style="margin-left:10px; margin-bottom:3px;" single-line hide-details></v-text-field>
          </v-toolbar>
          <v-data-table :headers="params_headers" :items="params_items" :search="params_search" :loading="loading" item-key="name" style="padding-top:5px;">
          </v-data-table>
        </v-card>

        <!-- PROCESSLIST -->
        <v-card style="margin-bottom:10px;">
          <v-toolbar dense flat color="#263238">
            <v-toolbar-title class="white--text subtitle-1">PROCESSLIST</v-toolbar-title>
            <v-divider class="mx-3" inset vertical></v-divider>
            <v-text-field v-model="processlist_search" append-icon="search" label="Search" color="white" style="margin-left:10px; margin-bottom:3px;" single-line hide-details></v-text-field>
          </v-toolbar>
          <v-data-table :headers="processlist_headers" :items="processlist_items" :search="processlist_search" :loading="loading" item-key="id" style="padding-top:5px;">
          </v-data-table>
        </v-card>
      </v-card-text>
    </v-card>

    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script>
import axios from 'axios';
import moment from 'moment';

export default {
  data: () => ({
    // Information
    server_id: '',
    server_name: '',
    server_hostname: '',
    region_name: '',
    available: true,
    error: null,
    timer: null,
    // Tabs
    tabs: 0,
    // Summary
    summary_headers: [
      { text: 'Available', align: 'left', value: 'available' },
      { text: 'Version', align: 'left', value: 'version' },
      { text: 'Uptime', align: 'left', value: 'uptime' },
      { text: 'Start Time', align: 'left', value: 'start_time' },
      { text: 'SQL Engine', align: 'left', value: 'sql_engine' },
      { text: 'Storage Engine', align: 'left', value: 'engine' },
      { text: 'Allocated Memory', align: 'left', value: 'allocated_memory' },
      { text: 'Timezone', align: 'left', value: 'time_zone' }
    ],
    summary_items: [],
    // Logs
    logs_headers: [
      { text: 'General Log', align: 'left', value: 'general_log' },
      { text: 'General Log File', align: 'left', value: 'general_log_file' },
      { text: 'Slow Query Log', align: 'left', value: 'slow_log' },
      { text: 'Slow Query Log File', align: 'left', value: 'slow_log_file' },
      { text: 'Error Log File', align: 'left', value: 'error_log_file' }
    ],
    logs_items: [],
    // Connections
    connections_headers: [
      { text: 'Current Connections', align: 'left', value: 'current' },
      { text: 'Max Connections Allowed', align: 'left', value: 'max_connections_allowed' },
      { text: 'Max Connections Reached', align: 'left', value: 'max_connections_reached' },
      { text: 'Max Allowed Packed', align: 'left', value: 'max_allowed_packet' },
      { text: 'Transaction Isolation', align: 'left', value: 'transaction_isolation' },
      { text: 'Bytes received', align: 'left', value: 'bytes_received' },
      { text: 'Bytes sent', align: 'left', value: 'bytes_sent' }
    ],
    connections_items: [],
    // Statements
    statements_headers: [
      { text: 'All Statements', align: 'left', value: 'all' },
      { text: 'SELECTs', align: 'left', value: 'select' },
      { text: 'INSERTs', align: 'left', value: 'insert' },
      { text: 'UPDATEs', align: 'left', value: 'update' },
      { text: 'DELETEs', align: 'left', value: 'delete' }
    ],
    statements_items: [],
    // Indexes
    indexes_headers: [
      { text: 'Percentage of queries not using indexes', align: 'left', value: 'percent' },
      { text: 'SELECTs not using indexes', align: 'left', value: 'selects' }
    ],
    indexes_items: [],
    // Parameter Groups
    params_headers: [
      { text: 'Name', align: 'left', value: 'name', width: '25%' },
      { text: 'Value', align: 'left', value: 'value' }
    ],
    params_items: [],
    params_search: '',
    // Processlist
    processlist_headers: [],
    processlist_items: [],
    processlist_search: '',
    // Updated
    updated: null,
    // Loading
    loading: true,
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: '',
  }),
  created() {
    this.init()
  },
  beforeDestroy() {
    clearTimeout(this.timer)
  },
  methods: {
    // -------------
    // BASE METHODS
    // -------------
    init() {
      const id = this.$route.params.id
      if (id === undefined) this.notification('Invalid Monitor Identifier', 'error')
      else {
        this.server_id = id
        this.getMonitor()
      }
    },
    goBack() {
      this.$router.push('/monitoring')
    },
    getMonitor() {
      // Get Deployment Data
      axios.get('/monitoring', { params: { server_id: this.server_id } })
        .then((response) => {
          this.parseData(response.data.server, response.data.settings)
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
    },
    parseData(server, settings) {
      if (server.length == 0) this.notification("This server does not exist", 'error')
      else {
        // Parse Information
        this.server_name = server[0]['name']
        this.server_hostname = server[0]['hostname']
        this.region_name = server[0]['region']
        this.available = server[0]['available']
        this.error = server[0]['error']

        // Parse Summary
        var summary = JSON.parse(server[0]['summary'])
        if (summary == null) {
          this.summary_items = (server[0]['available'] == null) ? [{ available: -1 }] : [{ available: server[0]['available'] }]
        }
        else {
          this.summary_items = [summary.info]
          if ('logs' in summary) this.logs_items = [summary.logs]
          if ('connections' in summary) this.connections_items = [summary.connections]
          if ('statements' in summary) this.statements_items = [summary.statements]
          if ('index' in summary) this.indexes_items = [summary.index]
          this.summary_items[0]['available'] = server[0]['available']
        }

        // Parse Parameters
        this.params_items = []
        var params = JSON.parse(server[0]['parameters'])
        for (let key in params) this.params_items.push({'name': key, 'value': params[key]})

        // Parse Processlist
        this.processlist_headers = []
        this.processlist_items = []
        var threads = JSON.parse(server[0]['processlist'])
        if (threads && threads.length > 0) {
          for (let key in threads[0]) this.processlist_headers.push({ text: key, align: 'left', value: key })
          for (let i = 0; i < threads.length; ++i) this.processlist_items.push(threads[i])
        }

        // Parse Updated
        this.updated = server[0]['updated']

        // Set timeout
        let refreshRate = (settings.length == 0) ? 5000 : parseInt(settings[0]['monitor_interval']) * 1000
        clearTimeout(this.timer)
        this.timer = setTimeout(this.getMonitor, refreshRate)
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
  }
}
</script>