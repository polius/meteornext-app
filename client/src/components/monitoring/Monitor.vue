<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title class="white--text">{{ server_name }}</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <div class="subheading font-weight-regular">{{ region_name }}</div>
        <v-divider class="mx-3" inset vertical></v-divider>
        <div class="subheading font-weight-regular">{{ server_hostname }}</div>
        <v-spacer></v-spacer>
        <div v-if="updated != null" class="subheading font-weight-regular" style="padding-right:10px;">Updated on <b>{{ dateFormat(updated) }}</b></div>
        <v-btn icon title="Go back" @click="goBack()"><v-icon>fas fa-arrow-alt-circle-left</v-icon></v-btn>
      </v-toolbar>

      <v-card-text>
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
            <v-tab><span class="pl-2 pr-2">RDS METRICS</span></v-tab>    
          </v-tabs>
        </div>

        <!-- SUMMARY -->
        <v-card v-show="tabs == 0">
          <v-data-table :headers="summary_headers" :items="summary_items" hide-default-footer class="elevation-1">
            <template v-slot:item.available="props">
              <span v-if="props.item.available == true"><v-icon small color="#00b16a" style="margin-right:10px; margin-bottom:2px;">fas fa-circle</v-icon>Yes</span>
              <span v-else-if="props.item.available == false"><v-icon small color="error" style="margin-right:10px; margin-bottom:2px;">fas fa-circle</v-icon>No</span>
              <span v-else-if="props.item.available == -1"><v-icon small color="orange" style="margin-right:10px; margin-bottom:2px;">fas fa-circle</v-icon>Loading</span>
            </template>
          </v-data-table>
        </v-card>

        <!-- LOGS -->
        <v-card v-show="tabs == 1">
          <v-data-table :headers="logs_headers" :items="logs_items" hide-default-footer class="elevation-1">
            <template v-slot:item.general_log="props">
              <span v-if="props.item.general_log == 'ON'"><v-icon small color="#00b16a" style="margin-right:10px; margin-bottom:2px;">fas fa-circle</v-icon>On</span>
              <span v-else><v-icon small color="error" style="margin-right:10px; margin-bottom:2px;">fas fa-circle</v-icon>Off</span>
            </template>
            <template v-slot:item.slow_log="props">
              <span v-if="props.item.slow_log == 'ON'"><v-icon small color="#00b16a" style="margin-right:10px; margin-bottom:2px;">fas fa-circle</v-icon>On</span>
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

        <!-- RDS METRICS -->
        <v-card v-show="tabs == 5">
          <v-data-table :headers="rds_headers" :items="rds_items" hide-default-footer class="elevation-1">
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

    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn color="white" text @click="snackbar = false">Close</v-btn>
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

    // RDS Metrics
    rds_headers: [
      { text: 'CPU Utilization', align: 'left', value: 'cpu_utilization' },
      { text: 'Freeable Memory', align: 'left', value: 'freeable_memory' },
      { text: 'DB Connections', align: 'left', value: 'db_connections' },
      { text: 'Network Receive Throughput (MB/Second)', align: 'left', value: 'network_receive' },
      { text: 'Network Transmit Throughput (MB/Second)', align: 'left', value: 'network_transmit' },
    ],
    rds_items: [{ cpu_utilization: '12%', freeable_memory: '12 GB', db_connections: '54', network_receive: '54.3', network_transmit: '43.1' }],

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
    loading: false,

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: '',
  }),
  created() {
    this.init()
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
      this.$router.go(-1)
    },
    getMonitor() {
      // Get Deployment Data
      const path = '/monitoring'
      axios.get(path, { params: { server_id: this.server_id } })
        .then((response) => {
          this.parseData(response.data.data)
          setTimeout(this.getMonitor, 10000)
        })
        .catch((error) => {
          console.log(error)
          // if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          // else this.notification(error.response.data.message, 'error')
        })
    },
    parseData(data) {
      if (data.length == 0) this.notification("The server does not exist", 'error')
      else {
        // Parse Information
        this.server_name = data[0]['name']
        this.server_hostname = data[0]['hostname']
        this.region_name = data[0]['region']

        // Parse Summary
        var summary = JSON.parse(data[0]['summary'])
        if (summary == null) {
          this.summary_items = [{available: -1}]
        }
        else {
          this.summary_items = [summary.info]
          if ('logs' in summary) this.logs_items = [summary.logs]
          if ('connections' in summary) this.connections_items = [summary.connections]
          if ('statements' in summary) this.statements_items = [summary.statements]
          if ('index' in summary) this.indexes_items = [summary.index]
        }

        // Parse Parameters
        this.params_items = []
        var params = JSON.parse(data[0]['parameters'])
        for (let key in params) this.params_items.push({'name': key, 'value': params[key]})

        // Parse Processlist
        this.processlist_headers = []
        this.processlist_items = []
        var threads = JSON.parse(data[0]['processlist'])
        if (threads && threads.length > 0) {
          for (let key in threads[0]) this.processlist_headers.push({ text: key, align: 'left', value: key })
          for (let i = 0; i < threads.length; ++i) this.processlist_items.push(threads[i])
        }

        // Parse Updated
        this.updated = data[0]['updated']
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