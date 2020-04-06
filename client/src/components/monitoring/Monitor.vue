<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title class="white--text">Templates EU</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <div class="subheading font-weight-regular">AWS-EU</div>
        <v-divider class="mx-3" inset vertical></v-divider>
        <div class="subheading font-weight-regular">127.0.0.1</div>
        <v-spacer></v-spacer>
        <v-btn icon title="Go back" @click="goBack()"><v-icon>fas fa-arrow-alt-circle-left</v-icon></v-btn>
      </v-toolbar>

      <v-card-text>
        <!-- <p class="font-weight-medium" style="margin-bottom:10px;">Hostname<pre>127.0.0.1</pre></p> -->
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
              <span v-if="props.item.available"><v-icon small color="#00b16a" style="margin-right:10px; margin-bottom:2px;">fas fa-circle</v-icon>Yes</span>
              <span v-else><v-icon small color="error" style="margin-right:10px; margin-bottom:2px;">fas fa-circle</v-icon>No</span>
            </template>
          </v-data-table>
        </v-card>

        <!-- LOGS -->
        <v-card v-show="tabs == 1">
          <v-data-table :headers="logs_headers" :items="logs_items" hide-default-footer class="elevation-1">
            <template v-slot:item.general_log="props">
              <span v-if="props.item.general_log"><v-icon small color="#00b16a" style="margin-right:10px; margin-bottom:2px;">fas fa-circle</v-icon>On</span>
              <span v-else><v-icon small color="error" style="margin-right:10px; margin-bottom:2px;">fas fa-circle</v-icon>Off</span>
            </template>
            <template v-slot:item.slow_query_log="props">
              <span v-if="props.item.slow_query_log"><v-icon small color="#00b16a" style="margin-right:10px; margin-bottom:2px;">fas fa-circle</v-icon>On</span>
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
        <!-- <div class="title font-weight-regular" style="padding-left:1px; margin-bottom:10px;">PARAMETERS</div> -->
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
    // Monitor Data
    monitor: {},

    // Tabs
    tabs: 0,

    // Summary
    summary_headers: [
      { text: 'Available', align: 'left', value: 'available' },
      { text: 'Version', align: 'left', value: 'version' },
      { text: 'Uptime', align: 'left', value: 'uptime' },
      { text: 'Start Time', align: 'left', value: 'start_time' },
      { text: 'SQL Engine', align: 'left', value: 'sql_engine' },
      { text: 'Storage Engine', align: 'left', value: 'storage_engine' },
      { text: 'Allocated Memory', align: 'left', value: 'allocated_memory' },
      { text: 'Timezone', align: 'left', value: 'timezone' }
    ],
    summary_items: [{ available: true, version: '5.6.10', uptime: '5d 2h 2m 3s', start_time: '2020-01-01 12:00:00', sql_engine: 'MySQL', storage_engine: 'InnoDB', allocated_memory: '24 GB', timezone: 'SERVER' }],

    // Logs
    logs_headers: [
      { text: 'General Log', align: 'left', value: 'general_log' },
      { text: 'General Log File', align: 'left', value: 'general_log_file' },
      { text: 'Slow Query Log', align: 'left', value: 'slow_query_log' },
      { text: 'Slow Query Log File', align: 'left', value: 'slow_query_log_file' },
      { text: 'Error Log File', align: 'left', value: 'error_log_file' }
    ],
    logs_items: [{ general_log: 'ON', general_log_file: '/opt/lampp/var/mysql/awseu-sql01.log', slow_query_log: 'ON', slow_query_log_file: '/opt/lampp/var/mysql/awseu-sql01-inbenta-com.slow-queries.log', error_log_file: '/opt/lampp/var/mysql/awseu-sql01.err' }],

    // Connections
    connections_headers: [
      { text: 'Max Connections Allowed', align: 'left', value: 'max_connections_allowed' },
      { text: 'Max Connections Reached', align: 'left', value: 'max_connections_reached' },
      { text: 'Max Allowed Packed', align: 'left', value: 'max_allowed_packet' },
      { text: 'Transaction Isolation', align: 'left', value: 'tx_isolation' },
      { text: 'Bytes received', align: 'left', value: 'bytes_received' },
      { text: 'Bytes sent', align: 'left', value: 'bytes_sent' }
    ],
    connections_items: [{ max_connections_allowed: '3000', max_connections_reached: '250 (12%)', max_allowed_packet: '16 MB', tx_isolation: 'REPETEABLE-READ', bytes_received: '12312984', bytes_sent: '12894353' }],

    // Statements
    statements_headers: [
      { text: 'All Statements', align: 'left', value: 'all_statements' },
      { text: 'SELECTs', align: 'left', value: 'selects' },
      { text: 'INSERTs', align: 'left', value: 'inserts' },
      { text: 'UPDATEs', align: 'left', value: 'updates' },
      { text: 'DELETEs', align: 'left', value: 'deletes' },
      { text: 'DMLs', align: 'left', value: 'dmls' }
    ],
    statements_items: [{ all_statements: '3000', selects: '23', inserts: '10', updates: '11', deletes: '12', dmls: '12' }],

    // Indexes
    indexes_headers: [
      { text: 'Percentage of queries not using indexes', align: 'left', value: 'full_table_scans' },
      { text: 'SELECTs not using indexes', align: 'left', value: 'full_table_scans_selects' }
    ],
    indexes_items: [{ full_table_scans: '43%', full_table_scans_selects: 2000 }],

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
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Value', align: 'left', value: 'value' }
    ],
    params_items: [],
    params_search: '',

    // Processlist
    processlist_headers: [],
    processlist_items: [],
    processlist_search: '',

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
      // else this.getMonitor(id)
    },
    goBack() {
      this.$router.go(-1)
    },
    getMonitor(id) {
      // Get Deployment Data
      const path = '/monitoring'
      axios.get(path, { params: { monitor_id: id } })
        .then((response) => {
          const data = response.data.data
          this.monitor = data
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
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