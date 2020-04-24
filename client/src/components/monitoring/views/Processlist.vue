<template>
  <div>
    <v-card style="margin-bottom:15px;">
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">PROCESSLIST</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text title="Select servers to monitor" @click="servers_dialog=true" class="body-2"><v-icon small style="padding-right:10px">fas fa-database</v-icon>SERVERS</v-btn>
          <v-btn text title="Filter processes" @click="filter_dialog=true" class="body-2"><v-icon small style="padding-right:10px">fas fa-sliders-h</v-icon>FILTER</v-btn>
        </v-toolbar-items>
        <v-spacer></v-spacer>
        <v-divider v-if="loading || pending_servers || Object.keys(processlist_origin).length > 0" class="mx-3" inset vertical></v-divider>
        <v-progress-circular v-if="loading || pending_servers" indeterminate size="20" width="2" color="white"></v-progress-circular>
        <div v-if="loading || pending_servers" class="subheading font-weight-regular" style="margin-left:10px; padding-right:10px;">Loading servers...</div>
        <div v-else-if="!loading && last_updated != null" class="subheading font-weight-regular" style="padding-right:10px;">Updated on <b>{{ dateFormat(last_updated) }}</b></div>
      </v-toolbar>
    </v-card>

    <div v-if="!loading && Object.keys(processlist_origin).length == 0" class="body-2" style="margin-top:10px; text-align:center; color:#D3D3D3">No servers selected</div>
    <div v-for="i in Object.keys(processlist_items)" :key="i" style="margin-bottom:15px;">
      <v-card>
        <v-toolbar flat dense color="#263238">
          <v-toolbar-title class="subtitle-1">{{ processlist_metadata[i]['server_name'] + ' [' + processlist_metadata[i]['region_name'] + ']' }}</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-text-field v-model="processlist_search[i]" append-icon="search" label="Search" color="white" style="margin-left:10px; margin-bottom:2px;" single-line hide-details></v-text-field>
        </v-toolbar>
        <v-data-table :headers="processlist_headers[i]" :items="processlist_items[i]" :search="processlist_search[i]" :hide-default-footer="processlist_items[i].length < 11" :no-data-text="(!pending_servers && processlist_items[i].length == 0 ) ? 'Server unavailable' : 'No data available'" :loading="pending_servers" class="elevation-1" style="padding-top:3px;">
        </v-data-table>
      </v-card>
    </div>

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
    active: true,
    loading: true,
    pending_servers: true, 
    last_updated: null,

    // Processlist
    processlist_metadata: {},
    processlist_headers: {},
    processlist_items: {},
    processlist_origin: {},
    processlist_selected: {},
    processlist_search: {},

    // Servers Dialog
    servers_dialog: false,
    treeviewItems: [],
    treeviewSelected: [],
    treeviewOpened: [],
    treeviewSearch: '',

    // Filter Dialog
    filter_dialog: false,
    filter_items: ['All', 'Matching', 'Not matching'],
    filter: 'All',

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  created() {
    this.active = true
    this.getProcesslist(0)
  },
  destroyed() {
    this.active = false
    axios.delete('/monitoring/processlist')
      .then(() => {})
      .catch(() => {})
  },
  methods: {
    getProcesslist(mode) {
      if (!this.active) return
      else if (Object.keys(this.processlist_origin).length == 0 && mode == 1 && !this.pending_servers) setTimeout(this.getProcesslist, 5000, 1)
      else {
        axios.get('/monitoring/processlist')
          .then((response) => {
            this.parseParameters(response.data.data)
            this.parseTreeView(response.data.data)
            this.parseLastUpdated(response.data.data)
            this.loading = false
            if (mode != 2) setTimeout(this.getProcesslist, 1000, 1)
          })
          .catch((error) => {
            if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
            else this.notification(error.response.data.message, 'error')
          })
      }
    },
    parseParameters(data) {
      this.processlist_metadata = {}
      this.processlist_headers = {}
      this.processlist_origin = {}
      var pending_servers = false
      for (let i = 0; i < data.length; ++i) {
        if (data[i]['selected']) {
          // Check pending servers
          pending_servers = data[i]['updated'] == null

          // Fill processlist 
          let threads = JSON.parse(data[i]['processlist'])
          this.processlist_metadata[data[i]['server_id']] = { server_name: data[i]['server_name'], region_name: data[i]['region_name']}
          this.processlist_headers[data[i]['server_id']] = []
          this.processlist_origin[data[i]['server_id']] = []

          if (threads != null && threads.length > 0) {
            for (let t in threads[0]) this.processlist_headers[data[i]['server_id']].push({ text: t, align: 'left', value: t })
            for (let t in threads) this.processlist_origin[data[i]['server_id']].push(threads[t])
          }
        }
      }
      this.pending_servers = pending_servers
      // this.applyFilter()
      this.processlist_items = JSON.parse(JSON.stringify(this.processlist_origin))
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
    parseLastUpdated(servers) {
      var last_updated = null
      for (let i = 0; i < servers.length; ++i) {
        if (last_updated == null) last_updated = servers[i]['updated']
        else if (moment(servers[i]['updated']) < moment(last_updated)) last_updated = servers[i]['updated']
      }
      this.last_updated = last_updated
    },
    submitServers() {
      this.loading = true
      const payload = JSON.stringify(this.treeviewSelected)
      axios.put('/monitoring/processlist', payload)
        .then((response) => {
          this.pending_servers = true
          this.processlist_origin = {}
          this.processlist_items = {}
          this.processlist_search = {}
          this.notification(response.data.message, '#00b16a')
          this.servers_dialog = false
          this.getProcesslist(2)
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