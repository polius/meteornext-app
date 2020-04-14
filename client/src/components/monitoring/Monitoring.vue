<template>
  <div>
    <v-card style="margin-bottom:7px;">
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">MONITORING</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text title="Settings" @click="settings_dialog=true" class="body-2"><v-icon small style="padding-right:10px">fas fa-cog</v-icon>SETTINGS</v-btn>
          <v-btn text title="Events" class="body-2"><v-icon small style="padding-right:10px">fas fa-rss</v-icon>EVENTS</v-btn>
        </v-toolbar-items>
        <v-spacer></v-spacer>
        <div class="subheading font-weight-regular" style="padding-right:10px;">Updated on <b>{{ dateFormat(last_updated) }}</b></div>
      </v-toolbar>
    </v-card>

    <v-layout style="margin-left:-4px; margin-right:-4px;">
      <v-flex xs3 v-for="item in links" :key="item.id" style="margin:5px; cursor:pointer;" @click="monitor(item)">
        <v-hover>
          <v-card slot-scope="{ hover }" :class="`elevation-${hover ? 12 : 2}`">
            <v-img height="10px" :class="item.color"></v-img>
            <v-card-title primary-title style="padding-bottom:10px;">
              <p class="text-xs-center" style="margin-bottom:0px;">
                <span class="title">{{item.title}}</span>
                <br>
                <span class="body-2">{{item.region}}</span>
              </p>
            </v-card-title>
            <v-divider></v-divider>
            <v-card-text style="padding-bottom:1px;">
              <p class="font-weight-medium">Hostname<pre>127.0.0.1</pre></p>
              <p class="font-weight-medium">Connections<pre>23</pre></p>
            </v-card-text>
          </v-card>
        </v-hover>
      </v-flex>      
    </v-layout>

    <v-dialog v-model="settings_dialog" persistent max-width="896px">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">SETTINGS</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="settings_dialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 20px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:15px; margin-bottom:15px;">                  
                  <v-card>
                    <v-toolbar flat dense color="#2e3131">
                      <v-toolbar-title class="white--text">SERVERS</v-toolbar-title>
                      <v-divider class="mx-3" inset vertical></v-divider>
                      <v-text-field v-model="treeviewSearch" append-icon="search" label="Search" color="white" style="margin-left:10px;" single-line hide-details></v-text-field>
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
                  <v-btn :disabled="loading" color="error" @click="settings_dialog=false" style="margin-left:5px;">CANCEL</v-btn>
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
    data() {
      return {
        loading: true,
        last_updated: '2020-01-01 20:12:23',
        links: [
          { id: '1', title: 'Templates EU', region: 'AWS-EU', color: 'teal' },
          { id: '2', title: 'Templates US', region: 'AWS-US', color: 'red' },
          { id: '3', title: 'Templates JP', region: 'AWS-JP', color: 'orange' },
          { id: '4', title: 'Aurora Apps', region: 'AWS-EU', color: 'teal' }      
        ],

        // Settings Dialog
        settings_dialog: false,
        treeviewItems: [],
        treeviewSelected: [],
        treeviewOpened: [],
        treeviewSearch: '',

        // Snackbar
        snackbar: false,
        snackbarTimeout: Number(3000),
        snackbarColor: '',
        snackbarText: ''
      }
    },
    created() {
      this.getServers()
    },
    methods: {
      monitor(item) {
        this.$router.push({ name:'monitor', params: { id: item.id }})
      },
      getServers() {
        axios.get('/monitoring/servers')
          .then((response) => {
            this.parseTreeView(response.data.servers)
            this.loading = false
          })
          .catch((error) => {
            if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
            else this.notification(error.response.data.message, 'error')
          })
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
            this.refreshTreeView()
            this.notification(response.data.message, '#00b16a')
            this.settings_dialog = false
          })
          .catch((error) => {
            if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
            else this.notification(error.response.data.message, 'error')
          })
          .finally(() => {
            this.loading = false
          })
      },
      refreshTreeView() {
        var opened = []
        for (let i = 0; i < this.treeviewSelected.length; ++i) {
          let found = false
          for (let j = 0; j < this.treeviewItems.length; ++j) {
            for (let k = 0; k < this.treeviewItems[j]['children'].length; ++k) {
              if (this.treeviewItems[j]['children'][k]['id'] == this.treeviewSelected[i]) {
                if (!opened.includes(this.treeviewItems[j]['id'])) opened.push(this.treeviewItems[j]['id'])
                found = true
                break
              }
            }
            if (found) break
          }
        }
        this.treeviewOpened = opened
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