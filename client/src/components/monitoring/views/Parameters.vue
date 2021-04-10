<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">PARAMETERS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn :disabled="loading" text title="Select servers to monitor" @click="openServers()" class="body-2"><v-icon small style="margin-right:10px">fas fa-database</v-icon>SERVERS</v-btn>
          <v-btn :disabled="loading" text title="Filter parameters" @click="openFilter()" class="body-2"><v-icon small style="margin-right:10px">fas fa-sliders-h</v-icon>FILTER</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
        </v-toolbar-items>
        <v-text-field v-model="parameters_search" append-icon="search" label="Search" color="white" style="margin-left:10px;" single-line hide-details></v-text-field>
        <v-divider v-if="loading || pending_servers || parameters_origin.length > 0" class="mx-3" inset vertical></v-divider>
        <v-progress-circular v-if="loading || pending_servers" indeterminate size="20" width="2" color="white"></v-progress-circular>
        <div v-if="loading || pending_servers" class="subheading font-weight-regular" style="margin-left:10px; padding-right:10px;">Loading servers...</div>
        <div v-else-if="!loading && last_updated != null" class="subheading font-weight-regular" style="padding-right:10px;">Updated on <b>{{ dateFormat(last_updated) }}</b></div>
      </v-toolbar>
      <v-data-table :headers="parameters_headers" :items="parameters_items" :search="parameters_search" :hide-default-header="parameters_headers.length == 1" :hide-default-footer="parameters_items.length < 11" no-data-text="No servers selected" :loading="pending_servers" item-key="id" class="elevation-1" style="padding-top:5px;"></v-data-table>
    </v-card>

    <v-dialog v-model="servers_dialog" max-width="896px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:3px">fas fa-database</v-icon>SERVERS</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="servers_dialog = false" style="width:40px; height:40px"><v-icon style="font-size:23px">fas fa-times-circle</v-icon></v-btn>
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
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:3px">fas fa-sliders-h</v-icon>FILTER</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="filter_dialog = false" style="width:40px; height:40px"><v-icon style="font-size:23px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-bottom:15px;">
                  <v-select filled v-model="filter_item" label="Status" :items="filter_items" :rules="[v => !!v || '']" hide-details></v-select>
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

    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
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
    timer: null,
    pending_servers: true,
    available_servers: true,
    last_updated: null,

    // Parameters
    parameters_headers: [],
    parameters_items: [],
    parameters_origin: [],
    parameters_search: '',

    // Servers Dialog
    servers_dialog: false,
    treeviewItems: [],
    treeviewSelected: [],
    treeviewSelectedRaw: [],
    treeviewOpened: [],
    treeviewOpenedRaw: [],
    treeviewSearch: '',

    // Filter Dialog
    filter_dialog: false,
    filter_items: ['All', 'Matching', 'Not matching'],
    filter_item: 'All',
    filter: 'All',

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  created() {
    this.active = true
    this.getParameters(true)
  },
  beforeDestroy() {
    this.active = false
    clearTimeout(this.timer)
  },
  methods: {
    getParameters(refresh=true) {
      if (refresh || !this.active) clearTimeout(this.timer)
      if (!this.active) return
      else if (refresh && !this.available_servers) setTimeout(this.getParameters, 5000, true)
      else {
        axios.get('/monitoring/parameters')
        .then((response) => {
          this.parseParameters(response.data.data)
          this.parseTreeView(response.data.data)
          this.parseLastUpdated(response.data.data)
          this.available_servers = response.data.data.some(x => x.selected)
          if (refresh) this.timer = setTimeout(this.getParameters, 5000, true)
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
      }
    },
    parseParameters(data) {
      this.parameters_headers = [{ text: 'Variable', align: 'left', value: 'variable' }]
      this.parameters_origin = []
      var pending_servers = false

      for (let i = 0; i < data.length; ++i) {
        if (data[i]['selected']) {
          // Check pending servers
          let pending = (data[i]['updated'] == null || (data[i]['parameters'] == null && data[i]['available']))
          if (pending == 1) pending_servers = true

          // Fill parameter items
          if (data[i]['parameters'] != null) {
            let params = JSON.parse(data[i]['parameters'])
            for (let p in params) {
              let obj = this.parameters_origin.find((o, j) => {
                if (o.variable === p) {
                  this.parameters_origin[j]['s'+data[i]['server_id']] = params[p]
                  return true; // stop searching
                }
              });
              if (obj === undefined) this.parameters_origin.push({variable: p, ['s'+data[i]['server_id']]: params[p]})
            }
            // Fill parameter headers
            this.parameters_headers.push({ text: data[i]['server_name'] + ' (' + data[i]['region_name'] + ')', align: 'left', value: 's'+data[i]['server_id'] })
          }
        }
      }
      this.pending_servers = pending_servers
      this.applyFilter()
    },
    parseTreeView(servers) {
      var data = []
      var selected = []
      var opened = []
      if (servers.length == 0) return

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
    parseLastUpdated(servers) {
      var last_updated = null
      for (let i = 0; i < servers.length; ++i) {
        if (servers[i]['selected']) {
          if (last_updated == null) last_updated = servers[i]['updated']
          else if (moment(servers[i]['updated']) < moment(last_updated)) last_updated = servers[i]['updated']
        }
      }
      this.last_updated = last_updated
    },
    applyFilter() {
      this.parameters_items = []
      for (let i = 0; i < this.parameters_origin.length; ++i) {        
        if (this.filter == 'All') this.parameters_items.push(this.parameters_origin[i])
        else {
          let values = []
          for (let key in this.parameters_origin[i]) {
            if (key != 'variable') values.push(this.parameters_origin[i][key])
          }
          let match = values.every( v => v === values[0] )
          if (this.filter == 'Matching' && match) this.parameters_items.push(this.parameters_origin[i])
          else if (this.filter == 'Not matching' && !match) this.parameters_items.push(this.parameters_origin[i])
        }
      }
    },
    openServers() {
      this.treeviewSelectedRaw = JSON.parse(JSON.stringify(this.treeviewSelected))
      this.treeviewOpenedRaw = JSON.parse(JSON.stringify(this.treeviewOpened))
      this.servers_dialog = true
    },
    submitServers() {
      this.loading = true
      const payload = this.treeviewSelectedRaw
      axios.put('/monitoring/parameters', payload)
        .then((response) => {
          this.treeviewSelected = JSON.parse(JSON.stringify(this.treeviewSelectedRaw))
          this.treeviewOpened = JSON.parse(JSON.stringify(this.treeviewOpenedRaw))
          this.pending_servers = true
          this.parameters_search = ''
          this.notification(response.data.message, '#00b16a')
          this.servers_dialog = false
          this.getParameters(false)
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
    },
    openFilter() {
      this.filter_item = this.filter
      this.filter_dialog = true
    },
    submitFilter() {
      this.filter = this.filter_item
      this.applyFilter()
      this.filter_dialog = false
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