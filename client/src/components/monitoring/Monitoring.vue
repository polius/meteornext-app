<template>
  <div>
    <v-card style="margin-bottom:7px;">
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">MONITORING</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn :disabled="loading" text title="Define monitoring rules and settings" @click="settings_dialog=true" class="body-2"><v-icon small style="padding-right:10px">fas fa-cog</v-icon>SETTINGS</v-btn>
          <v-btn :disabled="loading" text title="Select servers to monitor" @click="servers_dialog=true" class="body-2"><v-icon small style="padding-right:10px">fas fa-database</v-icon>SERVERS</v-btn>
          <v-btn :disabled="loading" text title="Filter servers" @click="filter_dialog=true" class="body-2"><v-icon small style="padding-right:10px">fas fa-sliders-h</v-icon>FILTER</v-btn>
          <v-btn :disabled="loading" text title="What's going on in all servers" @click="events_dialog=true" class="body-2"><v-icon small style="padding-right:10px">fas fa-rss</v-icon>EVENTS</v-btn>
        </v-toolbar-items>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" style="margin-left:5px;" single-line hide-details></v-text-field>
        <v-divider v-if="loading || pending_servers || servers.length > 0" class="mx-3" inset vertical></v-divider>
        <v-progress-circular v-if="loading || pending_servers" indeterminate size="20" width="2" color="white"></v-progress-circular>
        <div v-if="loading || pending_servers" class="subheading font-weight-regular" style="margin-left:10px; padding-right:10px;">Loading servers...</div>
        <div v-else-if="!loading && !pending_servers && last_updated != null" class="subheading font-weight-regular" style="padding-right:10px;">Updated on <b>{{ dateFormat(last_updated) }}</b></div>
      </v-toolbar>
    </v-card>

    <div v-if="!loading && servers_origin.length == 0" class="body-2" style="margin-top:15px; text-align:center; color:#D3D3D3">No servers selected</div>
    <div v-else-if="!loading && servers.length == 0" class="body-2" style="margin-top:15px; text-align:center; color:#D3D3D3">The search returned no results</div>

    <v-layout v-for="(n, i) in Math.ceil(servers.length/align)" :key="i" style="margin-left:-4px; margin-right:-4px;">
      <v-flex :xs3="align==4" :xs4="align==3" :xs6="align==2" :xs12="align==1" v-for="(m, j) in Math.min(servers.length-i*align,align)" :key="j" style="padding:5px; cursor:pointer;">
        <v-hover>
          <v-card :height="maxHeight" ref="serverRefs" @click="monitor(servers[i*align+j])" slot-scope="{ hover }" :title="servers[i*align+j].color == 'teal' ? 'Server available' : servers[i*align+j].color == 'orange' ? 'Server loading...': 'Server unavailable'" :class="`elevation-${hover ? 12 : 2}`">
            <v-img height="10px" :class="servers[i*align+j].color"></v-img>
            <v-progress-linear v-if="servers[i*align+j].color == 'orange'" indeterminate color="orange" height="3" style="margin-bottom:-3px;"></v-progress-linear>
            <v-card-title primary-title style="padding-bottom:10px;">
              <p class="text-xs-center" style="margin-bottom:0px;">
                <span class="title"><v-icon v-if="!servers[i*align+j].available && servers[i*align+j].error != null" :title="servers[i*align+j].error" small color="orange" style="margin-right:10px;">fas fa-exclamation-triangle</v-icon>{{servers[i*align+j].name}}</span>
                <br>
                <span class="body-2">{{servers[i*align+j].region}}</span>
              </p>
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text style="padding-bottom:1px;">
              <p class="font-weight-medium" style="margin-bottom:0px">Hostname</p>
              <p style="font-family:monospace">{{servers[i*align+j].hostname}}</p>
              <p class="font-weight-medium" style="margin-bottom:0px">Connections</p>
              <p style="font-family:monospace">{{servers[i*align+j].connections}}</p>
            </v-card-text>
          </v-card>
        </v-hover>
      </v-flex>
    </v-layout>

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
                  <v-select filled v-model="settings.monitor_align" label="Servers per line" :items="align_items" :rules="[v => !!v || '']" hide-details></v-select>
                  <v-text-field filled v-model="settings.monitor_interval" :rules="[v => v == parseInt(v) && v > 0 || '']" label="Data Collection Interval (seconds)" required style="margin-top:15px; margin-bottom:10px;" hide-details></v-text-field>
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

    <v-dialog v-model="events_dialog" persistent max-width="50%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">EVENTS</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="events_dialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 20px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-data-table :headers="events_headers" :items="events_items" :search="events_search" :loading="loading" item-key="id" :hide-default-footer="events_items.length < 11" class="elevation-1" style="margin-top:20px;">
                  <!-- <template v-slot:item.aws_enabled="props">
                    <v-icon v-if="props.item.aws_enabled" small color="#00b16a" style="margin-left:20px">fas fa-circle</v-icon>
                    <v-icon v-else small color="error" style="margin-left:20px">fas fa-circle</v-icon>
                  </template> -->
                </v-data-table>
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
    data() {
      return {
        active: true,
        loading: true,
        last_updated: null,
        servers: [],
        servers_origin: [],
        search: '',
        pending_servers: true,
        serverRefs: [],
        maxHeight: '',

        // Settings Dialog
        settings_dialog: false,        
        settings: { monitor_align:'4', monitor_interval:'10' },
        align_items: ['1', '2', '3', '4'],
        source_items: ['Information Schema', 'Performance Schema (recommended)'],
        align: '4',
        interval: '10',

        // Servers Dialog
        servers_dialog: false,
        treeviewItems: [],
        treeviewSelected: [],
        treeviewOpened: [],
        treeviewSearch: '',

        // Filter Dialog
        filter_dialog: false,
        filter_items: ['All', 'Available', 'Unavailable', 'Loading'],
        filter_item: 'All',
        filter: 'All',

        // Events Dialog
        events_dialog: false,
        events_headers: [],
        events_items: [],
        events_search: '',

        // Snackbar
        snackbar: false,
        snackbarTimeout: Number(3000),
        snackbarColor: '',
        snackbarText: ''
      }
    },
    created() {
      this.active = true
      this.getMonitoring(0)
    },
    updated() {
      this.matchHeight()
    },
    destroyed() {
      this.active = false
    },
    methods: {
      monitor(item) {
        this.$router.push({ name:'monitor', params: { id: item.id }})
      },
      getMonitoring(mode) {
        if (!this.active) return
        else if (this.servers_origin.length == 0 && mode == 1 && !this.pending_servers) setTimeout(this.getMonitoring, 5000, 1)
        else {
          axios.get('/monitoring')
          .then((response) => {
            if (mode == 0) this.parseSettings(response.data.settings)
            this.parseServers(response.data.servers)
            this.parseTreeView(response.data.servers)
            this.parseLastUpdated(response.data.servers)
            this.loading = false
            if (mode != 2) setTimeout(this.getMonitoring, 10000, 1)
          })
          .catch((error) => {
            if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
            else this.notification(error.response.data.message, 'error')
          })
        }
      },
      parseSettings(settings) {
        if (settings.length > 0) {
          this.settings.monitor_align = this.align = settings[0]['monitor_align'].toString()
          this.settings.monitor_interval = this.interval = settings[0]['monitor_interval']
        }
      },
      parseServers(servers) {
        this.servers_origin = []
        var pending_servers = false
        for (let i = 0; i < servers.length; ++i) {
          if (servers[i]['selected']) {
            var summary = JSON.parse(servers[i]['summary'])
            // Get Current Connections
            let conn = (summary != null && servers[i]['available']) ? summary['connections']['current'] : '?'
            // Get Pending Servers
            let pending = (servers[i]['updated'] == null || (servers[i]['summary'] == null && servers[i]['available']))
            if (pending == 1) pending_servers = true
            // Get Status Color
            let color = (pending == 1) ? 'orange' : (servers[i]['available']) ? 'teal' : 'red'
            // Build Item
            let item = {id: servers[i]['server_id'], name: servers[i]['server_name'], region: servers[i]['region_name'], hostname: servers[i]['hostname'], available: servers[i]['available'], error: servers[i]['error'], connections: conn, color: color}
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
          if (servers[i]['selected']) {
            if (last_updated == null) last_updated = servers[i]['updated']
            else if (moment(servers[i]['updated']) < moment(last_updated)) last_updated = servers[i]['updated']
          }
        }
        this.last_updated = last_updated
      },
      submitServers() {
        this.loading = true
        const payload = JSON.stringify(this.treeviewSelected)
        axios.put('/monitoring', payload)
          .then((response) => {
            this.pending_servers = true
            this.servers_origin = []
            this.servers = []
            this.search = ''
            this.notification(response.data.message, '#00b16a')
            this.servers_dialog = false
            this.getMonitoring(2)
          })
          .catch((error) => {
            if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
            else this.notification(error.response.data.message, 'error')
          })
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
            this.align = this.settings.monitor_align
            this.interval = this.settings.monitor_interval
            this.notification(response.data.message, '#00b16a')
            this.settings_dialog = false
            this.loading = false
          })
          .catch((error) => {
            if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
            else this.notification(error.response.data.message, 'error')
          })
      },
      submitFilter() {
        this.filter = this.filter_item
        this.applyFilter()
        this.applySearch()
        this.filter_dialog = false
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
      applySearch(value=null) {
        var newValue = value == null ? this.search : value
        var search = []
        for (let i = 0; i < this.servers.length; ++i) {
          if (this.servers[i]['name'].includes(newValue)) search.push(this.servers[i])
        }
        this.servers = search.slice(0)
      },
      matchHeight() {
        var max_height = 0
        for (let i in this.$refs.serverRefs) {
          if (this.$refs.serverRefs[i].$el.clientHeight > max_height) max_height = this.$refs.serverRefs[i].$el.clientHeight
        }
        if (max_height > 0) this.maxHeight = max_height
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
      // eslint-disable-next-line
      search: function (newValue, oldValue) {
        this.applyFilter()
        if (newValue.length > 0) this.applySearch(newValue)
      }
    }
  }
</script>