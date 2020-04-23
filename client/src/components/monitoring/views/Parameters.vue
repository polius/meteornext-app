<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">PARAMETERS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text title="Settings" @click="servers_dialog=true" class="body-2"><v-icon small style="padding-right:10px">fas fa-cog</v-icon>SETTINGS</v-btn>
          <v-btn text title="Filter parameters" @click="filter_dialog=true" class="body-2"><v-icon small style="padding-right:10px">fas fa-sliders-h</v-icon>FILTER</v-btn>
        </v-toolbar-items>
        <v-text-field v-model="parameters_search" append-icon="search" label="Search" color="white" style="margin-left:10px;" single-line hide-details></v-text-field>
        <v-divider v-if="!loading && last_updated != null" class="mx-3" inset vertical></v-divider>
        <div v-if="!loading && last_updated != null" class="subheading font-weight-regular" style="padding-right:10px;">Updated on <b>{{ dateFormat(last_updated) }}</b></div>
      </v-toolbar>
      <v-data-table :headers="parameters_headers" :items="parameters_items" :search="parameters_search" :hide-default-footer="parameters_items.length < 11" :loading="loading" item-key="id" class="elevation-1" style="padding-top:5px;">
      </v-data-table>
    </v-card>

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
        <v-card-text style="padding:15px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-bottom:15px;">
                  <v-select filled v-model="filter" label="Status" :items="filter_items" :rules="[v => !!v || '']" hide-details></v-select>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-btn :loading="loading" color="#00b16a" @click="submitFilter()">CONFIRM</v-btn>
                  <v-btn :disabled="loading" color="error" @click="filter_dialog=false" style="margin-left:5px;">CANCEL</v-btn>
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

    // Parameters
    parameters_headers: [
      { text: 'Variables', align: 'left', value: 'variables' },
      { text: 'Templates EU', align: 'left', value: '1' },
      { text: 'Templates US', align: 'left', value: '2' },
      { text: 'Templates JP', align: 'left', value: '3' }
    ],
    parameters_items: [],
    parameters_origin: [],
    parameters_search: '',

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
    this.getParameters(0)
  },
  destroyed() {
    this.active = false
  },
  methods: {
    getParameters(mode) {
      if (!this.active) return
      else if (this.servers_origin.length == 0 && mode == 1) setTimeout(this.getMonitoring, 5000, 1)
      else {
        axios.get('/monitoring')
        .then((response) => {
          this.parseParameters(response.data.servers)
          this.parseTreeView(response.data.servers)
          this.parseLastUpdated(response.data.servers)
          this.loading = false
          if (mode != 2) setTimeout(this.getMonitoring, 5000, 1)
        })
        .catch((error) => {
          console.log(error)
          // if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          // else this.notification(error.response.data.message, 'error')
        })
      }
    },
    parseParameters(servers) {
      this.parameters_origin = []
      var pending_servers = false
      for (let i = 0; i < servers.length; ++i) {
        if (servers[i]['selected']) {
          var summary = JSON.parse(servers[i]['summary'])
          // Get Current Connections
          let conn = (summary != null && summary['info']['available'] && 'connections' in summary) ? summary['connections']['current'] : '?'
          // Get Status Color
          let color = '' 
          if (summary == null) {
            color = 'orange'
            pending_servers = true
          }
          else if (!summary['info']['available']) color = 'red'
          else color = 'teal'
          // Build Item
          let item = {id: servers[i]['server_id'], name: servers[i]['server_name'], region: servers[i]['region_name'], hostname: servers[i]['hostname'], connections: conn, color: color}
          this.servers_origin.push(item)
        }
      }
      this.pending_servers = pending_servers
      // Apply filter
      if (this.search.length == 0) {
        this.applyFilter()
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
    parseLastUpdated(servers) {
      var last_updated = null
      for (let i = 0; i < servers.length; ++i) {
        if (last_updated == null) last_updated = servers[i]['updated']
        else if (moment(servers[i]['updated']) < moment(last_updated)) last_updated = servers[i]['updated']
      }
      this.last_updated = last_updated
    },
    applyFilter() {
      this.servers = []
      for (let i = 0; i < this.servers_origin.length; ++i) {
        if (this.filter == 'All') this.servers.push(this.servers_origin[i])
        else if (this.filter == 'Available' && this.servers_origin[i]['color'] == 'teal') this.servers.push(this.servers_origin[i])
        else if (this.filter == 'Unavailable' && this.servers_origin[i]['color'] == 'red') this.servers.push(this.servers_origin[i])
        else if (this.filter == 'Loading' && this.servers_origin[i]['color'] == 'orange') this.servers.push(this.servers_origin[i])
      }
    },
    submitServers() {

    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  }
}
</script>