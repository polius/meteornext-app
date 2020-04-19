<template>
  <div>
    <v-card style="margin-bottom:7px;">
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">MONITORING</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text title="Define monitoring rules and settings" @click="settings_dialog=true" class="body-2"><v-icon small style="padding-right:10px">fas fa-cog</v-icon>SETTINGS</v-btn>
          <v-btn text title="Select servers to monitor" @click="servers_dialog=true" class="body-2"><v-icon small style="padding-right:10px">fas fa-database</v-icon>SERVERS</v-btn>
          <v-btn text title="What's going on in all servers" @click="events_dialog=true" class="body-2"><v-icon small style="padding-right:10px">fas fa-rss</v-icon>EVENTS</v-btn>
        </v-toolbar-items>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" style="margin-left:5px;" single-line hide-details></v-text-field>
        <v-divider class="mx-3" inset vertical></v-divider>
        <div v-if="last_updated != null" class="subheading font-weight-regular" style="padding-right:10px;">Updated on <b>{{ dateFormat(last_updated) }}</b></div>
        <v-progress-circular v-if="last_updated == null" indeterminate size="20" width="2" color="white"></v-progress-circular>
        <div v-if="last_updated == null" class="subheading font-weight-regular" style="margin-left:10px; padding-right:10px;">Loading...</b></div>
      </v-toolbar>
    </v-card>

    <div v-if="!loading && servers_origin.length == 0" class="body-2" style="margin-top:10px; text-align:center">No servers selected</div>
    <div v-else-if="!loading && servers.length == 0" class="body-2" style="margin-top:10px; text-align:center">The search returned no results</div>

    <v-layout v-for="(n, i) in Math.ceil(servers.length/align)" :key="i" style="margin-left:-4px; margin-right:-4px;">
      <v-flex :xs3="align==4" :xs4="align==3" :xs6="align==2" :xs12="align==1" v-for="(m, j) in Math.min(servers.length-i*align,align)" :key="j" style="padding:5px; cursor:pointer;">
        <v-hover>
          <v-card @click="monitor(servers[i*align+j])" slot-scope="{ hover }" :class="`elevation-${hover ? 12 : 2}`">
            <v-img height="10px" :class="servers[i*align+j].color"></v-img>
            <v-card-title primary-title style="padding-bottom:10px;">
              <p class="text-xs-center" style="margin-bottom:0px;">
                <span class="title">{{servers[i*align+j].name}}</span>
                <br>
                <span class="body-2">{{servers[i*align+j].region}}</span>
              </p>
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text style="padding-bottom:1px;">
              <p class="font-weight-medium">Hostname<pre>{{servers[i*align+j].hostname}}</pre></p>
              <p class="font-weight-medium">Connections<pre>{{servers[i*align+j].connections}}</pre></p>
            </v-card-text>
          </v-card>
        </v-hover>
      </v-flex>
    </v-layout>

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
                  <v-select filled v-model="settings.align" label="Servers per line" :items="align_items" hide-details></v-select>
                  <v-text-field filled v-model="settings.interval" :rules="[v => !!v || '']" label="Data Collection Interval (seconds)" required style="margin-top:15px; margin-bottom:10px;" hide-details></v-text-field>
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
        loading: true,
        last_updated: '',
        servers: [],
        servers_origin: [],
        search: '',

        // Servers Dialog
        servers_dialog: false,
        treeviewItems: [],
        treeviewSelected: [],
        treeviewOpened: [],
        treeviewSearch: '',

        // Settings Dialog
        settings_dialog: false,        
        settings: { align:'4', interval:'10', source: 'Information Schema' },
        align_items: ['1', '2', '3', '4', '5'],
        source_items: ['Information Schema', 'Performance Schema (recommended)'],
        align: '4',
        interval: '10',

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
      this.getServers(true)
    },
    methods: {
      monitor(item) {
        this.$router.push({ name:'monitor', params: { id: item.id }})
      },
      getServers(repeat) {
        axios.get('/monitoring/servers')
          .then((response) => {
            //this.parseSettings(response.data.settings)
            this.parseServers(response.data.servers)
            this.parseTreeView(response.data.servers)
            this.last_updated = response.data.last_updated
            this.loading = false
            if (repeat) setTimeout(this.getServers, 10000)
          })
          .catch((error) => {
            if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
            else this.notification(error.response.data.message, 'error')
          })
      },
      parseSettings(settings) {
        this.settings = JSON.parse(settings)
        this.interval = this.settings.interval
        this.align = this.settings.align
      },
      parseServers(servers) {
        this.servers_origin = []
        for (let i = 0; i < servers.length; ++i) {
          if (servers[i]['selected']) {
            var summary = JSON.parse(servers[i]['summary'])
            // Get Current Connections
            let conn = (summary != null && summary['info']['available'] && 'connections' in summary) ? summary['connections']['current'] : '?'
            // Get Status Color
            let color = '' 
            if (summary == null) color = 'orange'
            else if (!summary['info']['available']) color = 'red'
            else color = 'teal'
            // Build Item
            let item = {id: servers[i]['server_id'], name: servers[i]['server_name'], region: servers[i]['region_name'], hostname: servers[i]['hostname'], connections: conn, color: color}
            this.servers_origin.push(item)
          }
        }
        if (this.servers.length == 0 && this.search.length == 0) this.servers = this.servers_origin.slice(0)
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
        this.treeviewItems = data
        this.treeviewSelected = selected
        this.treeviewOpened = opened
      },
      submitServers() {
        this.loading = true
        const payload = JSON.stringify(this.treeviewSelected)
        axios.put('/monitoring/servers', payload)
          .then((response) => {
            this.servers = []
            this.search = []
            this.last_updated = ''
            this.notification(response.data.message, '#00b16a')
            this.servers_dialog = false
            this.getServers(false)
          })
          .catch((error) => {
            if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
            else this.notification(error.response.data.message, 'error')
          })
          .finally(() => {
            this.loading = false
          })
      },
      // refreshTreeView() {
      //   var opened = []
      //   for (let i = 0; i < this.treeviewSelected.length; ++i) {
      //     let found = false
      //     for (let j = 0; j < this.treeviewItems.length; ++j) {
      //       for (let k = 0; k < this.treeviewItems[j]['children'].length; ++k) {
      //         if (this.treeviewItems[j]['children'][k]['id'] == this.treeviewSelected[i]) {
      //           if (!opened.includes(this.treeviewItems[j]['id'])) opened.push(this.treeviewItems[j]['id'])
      //           found = true
      //           break
      //         }
      //       }
      //       if (found) break
      //     }
      //   }
      //   this.treeviewOpened = opened
      // },
      submitSettings() {
        this.align = this.settings.align
        this.interval = this.settings.interval
        this.settings_dialog = false
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
        if (newValue.length == 0) this.servers = this.servers_origin.slice(0)
        else {
          this.servers = []
          for (let i = 0; i < this.servers_origin.length; ++i) {
            if (this.servers_origin[i]['name'].includes(newValue)) this.servers.push(this.servers_origin[i])
          }
        }
      }
    }
  }
</script>