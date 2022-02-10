<template>
  <div>
    <v-card style="margin-bottom:15px;">
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">PROCESSLIST</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items>
          <v-btn :disabled="loading" text title="Select servers to monitor" @click="openServers()"><v-icon small style="margin-right:10px">fas fa-database</v-icon>SERVERS</v-btn>
          <v-btn :disabled="loading" text title="Filter processes" @click="openFilter()"><v-icon small style="margin-right:10px">fas fa-sliders-h</v-icon>FILTER</v-btn>
          <v-divider v-if="!loading && last_updated != null" class="mx-3" inset vertical></v-divider>
          <v-btn v-if="!loading && last_updated != null" :disabled="loading" text :title="stopped ? 'Start processlist retrieval' : 'Stop processlist retrieval'" @click="submitStop()" class="body-2"><v-icon small style="margin-right:10px">{{ stopped ? 'fas fa-play' : 'fas fa-stop'}}</v-icon>{{ stopped ? 'START' : 'STOP' }}</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
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
          <v-toolbar-title class="subtitle-1">{{ processlist_metadata[i]['server_name'] + ' - ' + processlist_metadata[i]['region_name'] }}</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-text-field v-model="processlist_search[i]" append-icon="search" label="Search" color="white" style="margin-left:10px; margin-bottom:2px;" single-line hide-details></v-text-field>
        </v-toolbar>
        <v-data-table :headers="processlist_headers[i]" :items="processlist_items[i]" :search="processlist_search[i]" :no-data-text="!processlist_metadata[i]['server_active'] ? 'Server disabled' : (!pending_servers && processlist_items[i].length == 0 && filter == 'All' ) ? 'Server unavailable' : 'No data available'" :loading="pending_servers" class="elevation-1" style="padding-top:3px;" mobile-breakpoint="0">
          <template v-slot:[`footer.prepend`]>
            <div v-if="!processlist_metadata[i]['server_active']" class="text-body-2 font-weight-regular" style="margin:10px"><v-icon small color="warning" style="margin-right:10px; margin-bottom:2px">fas fa-exclamation-triangle</v-icon>This server is disabled. Consider the possibility of upgrading your license.</div>
          </template>
        </v-data-table>
      </v-card>
    </div>

    <v-dialog v-model="servers_dialog" max-width="896px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:3px">fas fa-database</v-icon>SERVERS</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="servers_dialog = false" style="width:40px; height:40px"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-bottom:15px">
                  <v-card>
                    <v-toolbar flat dense color="#2e3131">
                      <v-text-field v-model="treeviewSearch" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
                    </v-toolbar>
                    <v-card-text style="padding: 10px;">
                      <div v-if="treeviewItems.length == 0" class="body-2" style="text-align:center">No servers available</div>
                      <v-treeview v-else :active.sync="treeviewSelectedRaw" item-key="id" :items="treeviewItems" :open="treeviewOpenedRaw" :search="treeviewSearch" hoverable open-on-click multiple-active activatable transition>
                        <template v-slot:label="{ item }">
                          <v-icon v-if="item.children" small :title="item.shared ? 'Shared' : 'Personal'" :color="item.shared ? '#EF5354' : 'warning'" :style="item.shared ? 'margin-right:10px; margin-bottom:2px' : 'margin-left:2px; margin-right:16px; margin-bottom:2px'">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          {{ item.name }}
                        </template>
                        <template v-slot:prepend="{ item }">
                          <v-icon v-if="!item.children && !item.active" small color="warning" title="Maximum allowed resources exceeded. Upgrade your license to have more servers." style="margin-right:10px">fas fa-exclamation-triangle</v-icon>
                          <v-icon v-if="!item.children" small>fas fa-server</v-icon>
                        </template>
                        <template v-slot:append="{ item }">
                          <v-chip v-if="!item.children" label><v-icon small :color="item.shared ? '#EF5354' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>{{ item.shared ? 'Shared' : 'Personal' }}</v-chip>
                        </template>
                      </v-treeview>
                    </v-card-text>
                  </v-card>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px">
                  <v-btn :loading="loading" color="#00b16a" @click="submitServers()">CONFIRM</v-btn>
                  <v-btn :disabled="loading" color="#EF5354" @click="servers_dialog=false" style="margin-left:5px;">CANCEL</v-btn>
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
          <v-btn icon @click="filter_dialog = false" style="width:40px; height:40px"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-bottom:15px;">
                  <v-select filled v-model="filter_item" label="Command" :items="filter_items" :rules="[v => !!v || '']" hide-details></v-select>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-btn :loading="loading" color="#00b16a" @click="submitFilter()">CONFIRM</v-btn>
                  <v-btn :disabled="loading" color="#EF5354" @click="filter_dialog=false" style="margin-left:5px;">CANCEL</v-btn>
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
    treeviewSelectedRaw: [],
    treeviewOpened: [],
    treeviewOpenedRaw: [],
    treeviewSearch: '',

    // Filter Dialog
    filter_dialog: false,
    filter_items: ['All', 'Query', 'Sleep'],
    filter_item: 'All',
    filter: 'All',

    // Stop Processlist
    stopped: false,

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  created() {
    this.active = true
    this.startProcesslist()
    this.getProcesslist(true)
  },
  beforeDestroy() {
    this.active = false
    clearTimeout(this.timer)
    axios.put('/monitoring/processlist/stop')
  },
  methods: {
    getProcesslist(refresh=true) {
      if (refresh || !this.active) clearTimeout(this.timer)
      if (!this.active) return
      else if (refresh && !this.available_servers) setTimeout(this.getProcesslist, this.treeviewItems.length == 0 ? 10000 : 5000, true)
      else {
        axios.get('/monitoring/processlist')
          .then((response) => {
            this.parseProcesslist(response.data.data)
            this.parseTreeView(response.data.data)
            this.parseLastUpdated(response.data.data)
            this.available_servers = response.data.data.some(x => x.selected)
            if (refresh && !this.stopped) this.timer = setTimeout(this.getProcesslist, this.treeviewItems.length == 0 ? 10000 : 5000, true)
          })
          .catch((error) => {
            if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
            else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
          })
          .finally(() => this.loading = false)
      }
    },
    parseProcesslist(data) {
      this.processlist_metadata = {}
      this.processlist_headers = {}
      this.processlist_origin = {}
      var pending_servers = false
      for (let i = 0; i < data.length; ++i) {
        if (data[i]['selected']) {
          // Check pending servers
          let pending = (data[i]['updated'] == null || (data[i]['processlist'] == null && data[i]['available']))
          if (pending == 1) pending_servers = true

          // Fill processlist 
          let threads = JSON.parse(data[i]['processlist'])
          this.processlist_metadata[data[i]['server_id']] = { server_name: data[i]['server_name'], region_name: data[i]['region_name'], server_active: data[i]['server_active']}
          this.processlist_headers[data[i]['server_id']] = []
          this.processlist_origin[data[i]['server_id']] = []

          if (threads != null && threads.length > 0) {
            for (let t in threads[0]) this.processlist_headers[data[i]['server_id']].push({ text: t, align: 'left', value: t })
            if (data[i]['server_active']) for (let t in threads) this.processlist_origin[data[i]['server_id']].push(threads[t])
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
      if (servers.length == 0) return data

      // Parse Servers
      for (let i = 0; i < servers.length; ++i) {
        let index = data.findIndex(x => x.id == 'r' + servers[i]['region_id'])
        if (index == -1) data.push({ id: 'r' + servers[i]['region_id'], name: servers[i]['region_name'], shared: servers[i]['region_shared'], children: [{ id: servers[i]['server_id'], name: servers[i]['server_name'], shared: servers[i]['server_shared'], active: servers[i]['server_active'] }] })
        else data[index]['children'].push({ id: servers[i]['server_id'], name: servers[i]['server_name'], shared: servers[i]['server_shared'], active: servers[i]['server_active']})

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
    openServers() {
      this.treeviewSelectedRaw = JSON.parse(JSON.stringify(this.treeviewSelected))
      this.treeviewOpenedRaw = JSON.parse(JSON.stringify(this.treeviewOpened))
      this.servers_dialog = true
    },
    submitServers() {
      this.loading = true
      const payload = this.treeviewSelectedRaw
      axios.put('/monitoring/processlist', payload)
        .then((response) => {
          this.treeviewSelected = JSON.parse(JSON.stringify(this.treeviewSelectedRaw))
          this.treeviewOpened = JSON.parse(JSON.stringify(this.treeviewOpenedRaw))
          this.pending_servers = true
          this.processlist_origin = {}
          this.processlist_items = {}
          this.processlist_search = {}
          this.notification(response.data.message, '#00b16a')
          this.servers_dialog = false
          this.getProcesslist(false)
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
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
    applyFilter() {
      this.processlist_items = {}
      var threads = JSON.parse(JSON.stringify(this.processlist_origin))
      for (let i in threads) {
        this.processlist_items[i] = []
        for (let j = 0; j < threads[i].length; ++j) {
          if (this.filter == 'All') this.processlist_items[i].push(threads[i][j])
          else if (this.filter == 'Query' && ['Query', 'Execute'].includes(threads[i][j]['COMMAND'])) this.processlist_items[i].push(threads[i][j])
          else if (this.filter == 'Sleep' && threads[i][j]['COMMAND'] == 'Sleep') this.processlist_items[i].push(threads[i][j])
        }
      }
    },
    submitStop() {
      if (this.stopped) this.startProcesslist(true)
      else this.stopProcesslist()
      this.stopped = !this.stopped
    },
    startProcesslist(notification=false) {
      clearTimeout(this.timer)
      axios.put('/monitoring/processlist/start')
        .then((response) => {
          if (notification) this.notification(response.data.message, '#00b16a')
          this.getProcesslist(true)
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    stopProcesslist() {
      clearTimeout(this.timer)
      axios.put('/monitoring/processlist/stop')
        .then((response) => { 
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
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