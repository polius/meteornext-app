<template>
  <div>
    <v-card style="margin-bottom:7px;">
      <v-toolbar dense flat color="primary">
        <v-toolbar-items class="hidden-sm-and-down" style="margin-left:-16px">
          <v-btn :disabled="loading" text title="Define monitoring rules and settings" @click="openSettings()" class="body-2"><v-icon small style="padding-right:10px">fas fa-cog</v-icon>SETTINGS</v-btn>
          <v-btn :disabled="loading" text title="Select servers to monitor" @click="openServers()" class="body-2"><v-icon small style="padding-right:10px">fas fa-database</v-icon>SERVERS</v-btn>
          <v-btn :disabled="loading" text title="Filter servers" @click="openFilter()" class="body-2"><v-icon small style="padding-right:10px">fas fa-sliders-h</v-icon>FILTER</v-btn>
          <v-btn :disabled="loading" text title="Sort servers by number of connections" @click="sortClick()" class="body-2" :style="{ backgroundColor : sort_active ? '#4ba2f1' : '' }"><v-icon small style="padding-right:10px">fas fa-sort-amount-down</v-icon>SORT</v-btn>
          <v-btn :disabled="loading" text title="What's going on in all servers" @click="events_dialog=true" class="body-2"><v-icon small style="padding-right:10px">fas fa-rss</v-icon>EVENTS</v-btn>
        </v-toolbar-items>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-text-field @change="applyFilter" v-model="search" append-icon="search" label="Search" color="white" style="margin-left:5px;" single-line hide-details></v-text-field>
        <v-divider v-if="available_servers" class="mx-3" inset vertical></v-divider>
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
          <v-card :height="maxHeight" @click="monitor(servers[i*align+j])" slot-scope="{ hover }" :title="servers[i*align+j].color == 'teal' ? 'Server available' : servers[i*align+j].color == 'orange' ? 'Server loading...': 'Server unavailable'" :class="`elevation-${hover ? 12 : 2}`">
            <v-img height="10px" :class="servers[i*align+j].color"></v-img>
            <v-progress-linear v-if="servers[i*align+j].color == 'orange'" indeterminate color="orange" height="3" style="margin-bottom:-3px;"></v-progress-linear>
            <div style="padding:16px">
              <p class="title" style="display:block; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; margin-bottom:8px; font-weight:400"><v-icon v-if="!servers[i*align+j].available && servers[i*align+j].error != null" :title="servers[i*align+j].error" small color="orange" style="margin-right:10px;">fas fa-exclamation-triangle</v-icon>{{servers[i*align+j].name}}</p>
              <p class="body-2" style="display:block; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; margin-bottom:0px;">{{servers[i*align+j].region}}</p>
            </div>
            <v-divider></v-divider>
            <v-card-text style="padding-bottom:1px;">
              <p class="font-weight-medium" style="margin-bottom:0px">Hostname</p>
              <p style="font-family:monospace; display:block; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{{ servers[i*align+j].hostname }}</p>
              <p class="font-weight-medium" style="margin-bottom:0px">Connections</p>
              <p style="font-family:monospace; display:block; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;">{{servers[i*align+j].connections}}</p>
            </v-card-text>
          </v-card>
        </v-hover>
      </v-flex>
    </v-layout>

    <v-dialog v-model="settings_dialog" max-width="50%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text body-1"><v-icon small style="padding-right:10px; padding-bottom:3px">fas fa-cog</v-icon>SETTINGS</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="settings_dialog = false" style="width:40px; height:40px"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-bottom:15px;">
                  <v-row no-gutters>
                    <v-col style="margin-right:5px">
                      <v-text-field filled v-model="settings.monitor_interval" :rules="[v => v == parseInt(v) && v > 9 || '']" label="Data Collection Interval (seconds)" required hide-details></v-text-field>
                    </v-col>
                    <v-col style="margin-left:5px">
                      <v-select filled v-model="settings.monitor_align" label="Servers per line" :items="align_items" :rules="[v => !!v || '']" hide-details></v-select>
                    </v-col>
                  </v-row>
                  <div class="subtitle-1 font-weight-regular white--text" style="margin-top:15px">
                    SLACK
                    <v-tooltip right>
                      <template v-slot:activator="{ on }">
                        <v-icon small style="margin-left:5px; margin-bottom:3px;" v-on="on">fas fa-question-circle</v-icon>
                      </template>
                      <span>
                        Send a <span class="font-weight-medium" style="color:rgb(250, 130, 49);">Slack</span> message everytime a server changes its status (available, unavailable, ...)
                      </span>
                    </v-tooltip>
                  </div>
                  <v-switch v-model="settings.monitor_slack_enabled" label="Enable Notifications" color="info" style="margin-top:5px;" hide-details></v-switch>
                  <div v-if="settings.monitor_slack_enabled" style="margin-top:10px">
                    <v-text-field ref="slack" v-model="settings.monitor_slack_url" label="Webhook URL" :rules="[v => !!v && (v.startsWith('http://') || v.startsWith('https://')) || '']" hide-details></v-text-field>
                    <v-btn :loading="loading" @click="testSlack" color="info" style="margin-top:15px">Test Slack</v-btn>
                  </div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-btn :disabled="loading" color="#00b16a" @click="submitSettings()">CONFIRM</v-btn>
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
          <v-toolbar-title class="white--text body-1"><v-icon small style="padding-right:10px; padding-bottom:3px">fas fa-database</v-icon>SERVERS</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="selectAllServers" text title="Select all servers" style="height:100%"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-check-square</v-icon>Select all</v-btn>
          <v-btn @click="deselectAllServers" text title="Deselect all servers" style="height:100%"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-square</v-icon>Deselect all</v-btn>
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
          <v-toolbar-title class="white--text body-1"><v-icon small style="padding-right:10px; padding-bottom:3px">fas fa-sliders-h</v-icon>FILTER</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="filter_dialog = false" style="width:40px; height:40px"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
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

    <v-dialog v-model="events_dialog" max-width="90%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text body-1"><v-icon small style="padding-right:10px; padding-bottom:3px">fas fa-rss</v-icon>EVENTS</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-text-field v-model="events_search" append-icon="search" label="Search" color="white" style="margin-left:5px; width:calc(100% - 170px)" single-line hide-details></v-text-field>
          <v-divider class="mx-3" inset vertical style="margin-right:5px!important;"></v-divider>
          <v-btn icon @click="events_dialog = false" style="width:40px; height:40px"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:0px;">
          <v-container style="padding:0px; max-width:100%!important">
            <v-layout wrap>
              <v-flex xs12>
                <v-data-table :headers="events_headers" :items="events_items" :search="events_search" :loading="loading" item-key="id" :hide-default-footer="events_items.length < 11" class="elevation-1" style="margin-top:0px;">
                  <template v-slot:[`item.event`]="{ item }">
                    <v-row no-gutters align="center">
                      <v-col cols="auto" :style="`width:5px; height:47px; margin-right:10px; background-color:` + getEventColor(item.event)">
                      </v-col>
                      <v-col cols="auto" class="mr-auto">
                        {{ item.event.toUpperCase() }}
                      </v-col>
                      <v-col v-if="item.event == 'parameters'" cols="auto" style="margin-left:10px">
                        <v-btn small @click="eventDetails(item)">Details</v-btn>
                      </v-col>
                    </v-row>
                  </template>
                  <template v-slot:[`item.message`]="{ item }">
                    {{ getEventMessage(item) }}
                  </template>
                  <template v-slot:[`item.time`]="{ item }">
                    {{ dateFormat(item.time) }}
                  </template>
                </v-data-table>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="event_details_dialog" max-width="65%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text body-1"><v-icon small style="padding-right:10px; padding-bottom:3px">fas fa-info</v-icon>PARAMETERS</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <div class="white--text body-1">{{ event_details_item.server }}</div>
          <v-divider class="mx-3" inset vertical></v-divider>
          <div class="white--text body-1">{{ dateFormat(event_details_item.time) }}</div>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-text-field v-model="events_details_search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
          <v-divider class="ml-3 mr-1" inset vertical></v-divider>
          <v-btn icon @click="event_details_dialog = false" style="width:40px; height:40px"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-bottom:15px;">
                  <v-data-table :headers="event_details_headers" :items="event_details_items" :search="events_details_search" :hide-default-footer="event_details_items.length < 11" class="elevation-1" style="margin-top:0px;"></v-data-table>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-btn color="primary" @click="event_details_dialog = false">CLOSE</v-btn>
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
    data() {
      return {
        active: true,
        loading: true,
        timer: null,
        last_updated: null,
        servers: [],
        servers_origin: [],
        available_servers: true,
        search: '',
        pending_servers: true,
        maxHeight: '',

        // Settings Dialog
        settings_dialog: false,        
        settings: { monitor_align: '4', monitor_interval: '10', monitor_slack_enabled: false, monitor_slack_url: '' },
        align_items: ['1', '2', '3', '4'],
        align: '4',
        interval: '10',
        slack_enabled: false,
        slack_url: '',

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
        filter_items: ['All', 'Available', 'Unavailable', 'Loading'],
        filter_item: 'All',
        filter: 'All',

        // Sort
        sort_active: false,

        // Events Dialog
        events_dialog: false,
        events_headers: [
          { text: 'Server', align: 'left', value: 'server' },
          { text: 'Event', align: 'left', value: 'event' },
          { text: 'Message', align: 'left', value: 'message' },
          { text: 'Time', align: 'left', value: 'time' },
        ],
        events_items: [],
        events_search: '',

        // Event Details Dialog
        event_details_dialog: false,
        event_details_item: {},
        event_details_headers: [
          { text: 'Variable Name', align: 'left', value: 'variable' },
          { text: 'Previous Value', align: 'left', value: 'previous' },
          { text: 'Current Value', align: 'left', value: 'current' },
        ],
        event_details_items: [],
        events_details_search: '',

        // Snackbar
        snackbar: false,
        snackbarTimeout: Number(3000),
        snackbarColor: '',
        snackbarText: ''
      }
    },
    created() {
      this.active = true
      this.getSettings()
      this.getMonitoring(true)
    },
    beforeDestroy() {
      this.active = false
      clearTimeout(this.timer)
    },
    watch: {
      search() {
        this.applyFilter()
      },
      'settings.monitor_slack_enabled': function (val) {
        if (val) {
          requestAnimationFrame(() => {
            if (typeof this.$refs.slack !== 'undefined') this.$refs.slack.focus()
          })
        }
      }
    },
    methods: {
      monitor(item) {
        this.$router.push({ name:'monitor', params: { id: item.id }})
      },
      getMonitoring(refresh=true) {
        if (refresh || !this.active) clearTimeout(this.timer)
        if (!this.active) return
        else if (refresh && !this.available_servers) setTimeout(this.getMonitoring, parseInt(this.settings.monitor_interval) * 1000, true)
        else {
          axios.get('/monitoring')
          .then((response) => {
            this.parseServers(response.data.servers)
            this.parseEvents(response.data.events)
            this.parseTreeView(response.data.servers)
            this.parseLastUpdated(response.data.servers)
            this.available_servers = response.data.servers.some(x => x.selected)
            if (refresh) setTimeout(this.getMonitoring, parseInt(this.settings.monitor_interval) * 1000, true)
          })
          .catch((error) => {
            if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
            else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
          })
          .finally(() => this.loading = false)
        }
      },
      openSettings() {
        this.settings = { monitor_align: this.align, monitor_interval: this.interval, monitor_slack_enabled: this.slack_enabled, monitor_slack_url: this.slack_url },
        this.settings_dialog = true
      },
      getSettings() {
        axios.get('/monitoring/settings')
        .then((response) => {
          this.parseSettings(response.data.settings)
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
      },
      parseSettings(settings) {
        if (settings.length > 0) {
          this.settings.monitor_align = this.align = settings[0]['monitor_align'].toString()
          this.settings.monitor_interval = this.interval = settings[0]['monitor_interval']
          this.settings.monitor_slack_enabled = this.slack_enabled = settings[0]['monitor_slack_enabled']
          this.settings.monitor_slack_url = this.slack_url = settings[0]['monitor_slack_url']
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
        this.applyFilter()
      },
      parseEvents(events) {
        this.events_items = events
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
          this.treeviewSelectedRaw = selected
          this.treeviewOpened = opened
          this.treeviewOpenedRaw = opened
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
        axios.put('/monitoring', payload)
          .then((response) => {
            this.treeviewSelected = JSON.parse(JSON.stringify(this.treeviewSelectedRaw))
            this.treeviewOpened = JSON.parse(JSON.stringify(this.treeviewOpenedRaw))
            this.pending_servers = true
            this.search = ''
            this.notification(response.data.message, '#00b16a')
            this.servers_dialog = false
            this.getMonitoring(false)
          })
          .catch((error) => {
            if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
            else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
          })
          .finally(() => this.loading = false)
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
        this.settings.monitor_slack_url = this.settings.monitor_slack_url != null && this.settings.monitor_slack_url.trim().length == 0 ? null : this.settings.monitor_slack_url
        this.settings.monitor_base_url = window.location.origin
        const payload = this.settings
        axios.put('/monitoring/settings', payload)
          .then((response) => {
            this.align = this.settings.monitor_align
            this.interval = this.settings.monitor_interval
            this.slack_enabled = this.settings.monitor_slack_enabled
            this.slack_url = this.settings.monitor_slack_url
            this.notification(response.data.message, '#00b16a')
            this.settings_dialog = false
          })
          .catch((error) => {
            if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
            else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
          })
          .finally(() => this.loading = false)
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
        let servers = []
        // Apply Filter
        for (let i = 0; i < this.servers_origin.length; ++i) {
          if (this.filter == 'All') servers.push(this.servers_origin[i])
          else if (this.filter == 'Available' && this.servers_origin[i]['color'] == 'teal') servers.push(this.servers_origin[i])
          else if (this.filter == 'Unavailable' && this.servers_origin[i]['color'] == 'red') servers.push(this.servers_origin[i])
          else if (this.filter == 'Loading' && this.servers_origin[i]['color'] == 'orange') servers.push(this.servers_origin[i])
        }
        // Apply Search
        servers = servers.filter(x => x['name'].toLowerCase().includes(this.search.toLowerCase()) || x['region'].toLowerCase().includes(this.search.toLowerCase()) || x['hostname'].toLowerCase().includes(this.search.toLowerCase()))
        // Apply Sort
        servers.sort((a, b) => a.name.localeCompare(b.name))
        if (this.sort_active) servers.sort((a, b) => parseInt(b.connections == '?' ? '0' : b.connections) - parseInt(a.connections == '?' ? '0' : a.connections));
        this.servers = JSON.parse(JSON.stringify(servers))
      },
      sortClick() {
        this.sort_active = !this.sort_active
        this.applyFilter()
      },
      testSlack() {
        // Check if all fields are filled
        if (!this.$refs.form.validate()) {
          this.notification('Please make sure all required fields are filled out correctly', 'error')
          return
        }
        // Test Slack Webhook URL
        this.loading = true
        const payload = { webhook_url: this.settings.monitor_slack_url }
        axios.get('/monitoring/slack', { params: payload })
          .then((response) => {
            this.notification(response.data.message, '#00b16a')
          })
          .catch((error) => {
            if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
            else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
          })
          .finally(() => this.loading = false)
      },
      getEventColor(event) {
        if (['available','connections_stable'].includes(event)) return '#4caf50'
        else if (['restarted','connections_warning'].includes(event)) return '#ff9800'
        else if (event == 'parameters') return '#3e9bef'
        else return '#e74c3c'
      },
      getEventMessage(item) {
        var message = ''
        if (item.event == 'unavailable') message = 'Server is unavailable. Error: ' + item.data
        else if (item.event == 'available') message = 'Server is available.'
        else if (item.event == 'restarted') message = 'Server has restarted.'
        else if (item.event == 'parameters') message = 'Server configuration change detected.'
        else if (item.event == 'connections_critical') message = 'Server entered in a critical state (Current Connections: ' + item.data + ').'
        else if (item.event == 'connections_warning') message = 'Server entered in a warning state (Current Connections: ' + item.data + ').'
        else if (item.event == 'connections_stable') message = 'Server recovered (Current Connections: ' + item.data + ').'
        return message
      },
      eventDetails(item) {
        this.event_details_item = item
        this.event_details_items = []
        for (const [key, value] of Object.entries(JSON.parse(item.data))) {
          this.event_details_items.push({'variable': key, 'previous': value.previous, 'current': value.current})
        }
        this.event_details_dialog = true
      },
      selectAllServers() {
        this.treeviewOpenedRaw = this.treeviewItems.map(x => x.id) 
        this.treeviewSelectedRaw = this.treeviewItems.reduce((acc, val) => { acc = acc.concat(val.children.map(x => x.id)); return acc },[])
      },
      deselectAllServers() {
        this.treeviewOpenedRaw = []
        this.treeviewSelectedRaw = []
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
  }
</script>