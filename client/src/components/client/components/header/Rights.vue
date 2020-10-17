<template>
  <div>
    <v-dialog v-model="dialog" persistent max-width="85%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text"><v-icon small style="padding-right:10px; padding-bottom:4px">fas fa-shield-alt</v-icon>User Rights</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn :disabled="saveEnabled" color="primary" style="margin-right:10px;">Save</v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="dialog = false" icon><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:0px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <Splitpanes @ready="onSplitPaneReady" style="height:80vh">
                  <Pane size="20" min-size="0" style="align-items:inherit">
                    <Sidebar />
                  </Pane>
                  <Pane size="80" min-size="0" style="background-color:#484848; align-items:inherit;">
                    <v-container fluid style="padding:0px;">
                      <div>
                        <v-tabs v-model="tab" show-arrows dense background-color="#3b3b3b" color="white" slider-color="white" slider-size="1" slot="extension" class="elevation-2">
                          <v-tabs-slider></v-tabs-slider>
                          <v-tab><span class="pl-2 pr-2">Login</span></v-tab>
                          <v-divider class="mx-3" inset vertical></v-divider>
                          <v-tab><span class="pl-2 pr-2">Server Privileges</span></v-tab>
                          <v-divider class="mx-3" inset vertical></v-divider>
                          <v-tab><span class="pl-2 pr-2">Schema Privileges</span></v-tab>
                          <v-divider class="mx-3" inset vertical></v-divider>
                          <v-tab><span class="pl-2 pr-2">Resources</span></v-tab>
                          <v-divider class="mx-3" inset vertical></v-divider>
                          <v-tab><span class="pl-2 pr-2">SQL Syntax</span></v-tab>
                          <v-divider class="mx-3" inset vertical></v-divider>
                        </v-tabs>
                      </div>
                      <Login v-show="tab == 0" />
                      <Server v-show="tab == 1" />
                      <Schema :tab="tab" v-show="tab == 2" />
                      <Resources v-show="tab == 3"/>
                      <Syntax :tab="tab" v-show="tab == 4"/>
                    </v-container>
                  </Pane>
                </Splitpanes>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!------------------>
    <!-- DIALOG: info -->
    <!------------------>
    <v-dialog v-model="infoDialog" persistent max-width="50%">
      <v-card>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <div class="text-h6" style="font-weight:400;">An error occurred</div>
              <v-flex xs12>
                <v-form ref="dialogForm" style="margin-top:10px; margin-bottom:15px;">
                  <div class="body-2" style="font-weight:300; font-size:1.05rem!important; margin-top:12px;">{{ infoDialogText }}</div>
                  <v-card style="margin-top:20px;">
                    <v-card-text style="padding:10px;">
                      <div class="body-1" style="font-weight:300; font-size:1.05rem!important;">{{ infoDialogError }}</div>
                    </v-card-text>
                  </v-card>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn @click="infoDialog = false" color="primary">Close</v-btn>
                    </v-col>
                  </v-row>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped src="@/styles/splitPanes.css"></style>

<script>
import axios from 'axios'

import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'

import { Splitpanes, Pane } from 'splitpanes'
import 'splitpanes/dist/splitpanes.css'

import Sidebar from './rights/Sidebar'
import Login from './rights/Login'
import Server from './rights/Server'
import Schema from './rights/Schema'
import Resources from './rights/Resources'
import Syntax from './rights/Syntax'

export default {
  data() {
    return {
      dialog: false,
      saveEnabled: false,
      // Tab
      tab: 0,
      // Info Dialog
      infoDialog: false,
      infoDialogText: '',
      infoDialogError: '',
    }
  },
  components: { Splitpanes, Pane, Sidebar, Login, Server, Schema, Resources, Syntax },
  computed: {
    ...mapFields([
      'index',
      'server',
      'headerTab',
      'headerTabSelected',
      'rights',
      'rightsItem',
      'rightsLoading',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('show-rights', this.showDialog);
    EventBus.$on('get-rights', this.getRights);
  },
  watch: {
    dialog: function(value) {
      if (!value) {
        const tab = {'client': 0, 'structure': 1, 'content': 2, 'info': 3, 'objects': 6}
        this.headerTab = tab[this.headerTabSelected]
      }
    },
    rightsItem: {
      handler(val) {
        console.log(this.rightsItem)
        if (
          Object.keys(val['login']).length == 0 && 
          Object.keys(val['server']).length == 0 && 
          val['schema']['grant'].length == 0 && val['schema']['revoke'].length == 0 &&
          Object.keys(val['resources']).length == 0
        ) this.saveEnabled = false
        else this.saveEnabled = true
      },
      deep: true
    },
  },
  methods: {
    showDialog() {
      this.dialog = true
      if (this.rights['sidebar'].length == 0) this.getRights()
    },
    onSplitPaneReady() {
    },
    getRights(user, host) {
      const payload = {
        connection: this.index,
        server: this.server.id,
        user,
        host
      }
      axios.get('/client/rights', { params: payload })
        .then((response) => {
          this.parseRightsSidebar(response.data)
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else {
            // Show Dialog
            this.infoDialogText = error.response.data.message
            this.infoDialogError = error.response.data.error
            this.infoDialog = true
          }
        })
        .finally(() => {
          this.$nextTick(() => { })          
        })
    },
    parseRightsSidebar(data) {
      if ('rights' in data) {
        var rights = []
        for (let right of data['rights']) {
          let index = rights.findIndex(k => k['name'] == right['user'])
          if (index == -1) rights.push({ id: right['user'], name: right['user'], children: [{ id: right['user'] + '|' + right['host'], user: right['user'], name: right['host'] }] })
          else rights[index]['children'].push({ id: right['user'] + '|' + right['host'], user: right['user'], name: right['host'] })
        }
        this.rights['sidebar']= rights.slice(0)
      }
      else {
        // Login
        const login = {
          username: data['server'][0]['User'],
          password: data['server'][0]['authentication_string'],
          passwordType: 'Hash',
          hostname: data['server'][0]['Host']
        }
        this.rights['login'] = login
        // Server
        let server = {}
        for (const [key, val] of Object.entries(data['server'][0])) {
          if (key.endsWith('_priv')) server[key.toLowerCase().slice(0,-5)] = val == 'Y'
        }
        this.rights['server'] = server
        // Schema
        let schema = []
        for (let database of data['database']) {
          let row = { type: 'database', schema: database['Db'], rights: [] }
          for (const [key, val] of Object.entries(database)) {
            if (key.endsWith('_priv') && val == 'Y') row['rights'].push(key.toLowerCase().slice(0,-5))
          }
          schema.push(row)
        }
        for (let table of data['table']) {
          let row = { type: 'table', schema: table['db'] + '.' + table['table_name'], rights: table['table_priv'].split(',').map((item) => { return item.toLowerCase().trim() }) }
          schema.push(row)
        }
        for (let column of data['column']) {
          let row = { type: 'column', schema: column['db'] + '.' + column['table_name'] + '.' + column['column_name'], rights: column['column_priv'].split(',').map((item) => { return item.toLowerCase().trim() }) }
          schema.push(row)
        }
        for (let proc of data['proc']) {
          let row = { type: 'column', schema: '[' + proc['routine_type'] + '] ' + proc['db'] + '.' + proc['routine_name'], rights: proc['proc_priv'].split(',').map((item) => { return item.toLowerCase().trim() }) }
          schema.push(row)
        }
        this.rights['schema'] = schema.slice(0)
        // Resources
        const resources = {
          max_queries: data['server'][0]['max_questions'],
          max_updates: data['server'][0]['max_updates'],
          max_connections: data['server'][0]['max_connections'],
          max_simultaneous: data['server'][0]['max_user_connections']
        }
        this.rights['resources'] = resources
        // Syntax
        let syntax = data['syntax'].map(x => Object.values(x)).join(';\n') + ';'
        this.rights['syntax'] = syntax
        // Reload Rights
        EventBus.$emit('reload-rights')
      }
    },
  }
}
</script>