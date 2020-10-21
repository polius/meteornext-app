<template>
  <div>
    <v-dialog v-model="dialog" persistent max-width="85%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text"><v-icon small style="padding-right:10px; padding-bottom:4px">fas fa-shield-alt</v-icon>User Rights</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn :disabled="!saveEnabled" @click="saveClick" color="primary" style="margin-right:10px;">Save</v-btn>
          <v-btn v-if="errors['login'].length > 0 || errors['server'].length > 0 || errors['schema'].length > 0 || errors['resources'].length > 0" @click="errorDialog = true" outlined style="margin-right:10px;" title="Show errors"><v-icon small style="padding-right:10px">fas fa-exclamation-triangle</v-icon>Show errors</v-btn>
          <v-progress-circular v-if="loading" indeterminate size="20" width="2" style="margin-left:5px"></v-progress-circular>
          <v-spacer></v-spacer>
          <v-btn @click="dialog = false" icon><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:0px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <Splitpanes @ready="onSplitPaneReady" style="height:80vh">
                  <Pane size="20" min-size="0" style="align-items:inherit">
                    <Sidebar :dialog="dialog" />
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
                <v-form style="margin-top:10px; margin-bottom:15px;">
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
    <!------------------->
    <!-- DIALOG: check -->
    <!------------------->
    <v-dialog v-model="checkDialog" persistent max-width="85%">
      <v-card>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form style="margin-top:10px; margin-bottom:15px;">
                  <div class="body-2" style="font-weight:400; font-size:1.05rem!important; margin-top:12px; margin-left:2px;">{{ "Preview changes for: '" + rightsSelected['user'] + "'@'" + rightsSelected['name'] + "'" }}</div>
                  <ag-grid-vue suppressDragLeaveHidesColumns suppressContextMenu preventDefaultOnContextMenu suppressColumnVirtualisation @grid-ready="onGridReady" style="width:100%; height:69vh; margin-top:20px" class="ag-theme-alpine-dark" rowHeight="35" headerHeight="35" :columnDefs="checkHeaders" :rowData="checkItems"></ag-grid-vue>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :disabled="loading" :loading="loading" @click="checkSubmit" color="primary">Confirm</v-btn>
                    </v-col>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :disabled="loading" @click="checkDialog = false" outlined color="#e74d3c">Cancel</v-btn>
                    </v-col>
                  </v-row>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!------------------->
    <!-- DIALOG: error -->
    <!------------------->
    <v-dialog v-model="errorDialog" persistent max-width="70%">
      <v-card>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <div class="text-h6" style="font-weight:400;">Some errors have occurred</div>
              <v-flex xs12>
                <v-form style="margin-bottom:15px;">
                  <div v-for="key in Object.keys(errors)" :key="key">
                    <div v-for="(item, index) in errors[key]" :key="index" style="margin-top:15px;">
                      <div class="body-1" style="font-size:1.05rem; font-weight:400; color:#fa8131">{{ key.toUpperCase() }}</div>
                      <v-card style="margin-top:10px; margin-bottom:10px">
                        <v-card-text style="padding: 11px 10px 10px 10px">
                          {{ item.query }}
                        </v-card-text>
                      </v-card>
                      <div class="body-2" style="font-weight:400; margin-top:15px; margin-bottom:10px; margin-left:2px;">{{ item.error }}</div>
                    </div>
                  </div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn @click="errorDialog = false" color="primary">Close</v-btn>
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

<style scoped src="@/styles/agGridVue.css"></style>
<style scoped src="@/styles/splitPanes.css"></style>

<script>
import axios from 'axios'

import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'

import {AgGridVue} from "ag-grid-vue"
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
      loading: true,
      mode: '',
      dialog: false,
      saveEnabled: false,
      // Tab
      tab: 0,
      // Info Dialog
      infoDialog: false,
      infoDialogText: '',
      infoDialogError: '',
      // Check Dialog
      checkDialog: false,
      checkHeaders: [
        { headerName: 'Section', colId: 'section', field: 'section', sortable: false, filter: false, resizable: true, editable: false,
          valueGetter: (params) => {
            return params.data.section.toUpperCase()
          }
        },
        { headerName: 'Action', colId: 'action', field: 'action', sortable: false, filter: false, resizable: true, editable: false, 
          cellStyle: function(params) {
            if (params.value == 'Grant') return { color: '#00b16a' }
            else if (params.value == 'Revoke') return { color: '#e74d3c' }
            else return { color: '#fa8131' }
          }
        },
        { headerName: 'Object', colId: 'object', field: 'object', sortable: false, filter: false, resizable: true, editable: false },
        { headerName: 'Right', colId: 'right', field: 'right', sortable: false, filter: false, resizable: true, editable: false },
        { headerName: 'Before', colId: 'before', field: 'before', sortable: false, filter: false, resizable: true, editable: false },
        { headerName: 'After', colId: 'after', field: 'after', sortable: false, filter: false, resizable: true, editable: false },
        { headerName: 'Query', colId: 'query', field: 'query', sortable: false, filter: false, resizable: true, editable: false }
      ],
      checkItems: [],
      gridApi: null,
      columnApi: null,
      // Error Dialog
      errorDialog: false,
      errors: { login: [], server: [], schema: [], resources: [] }
    }
  },
  components: { Splitpanes, Pane, AgGridVue, Sidebar, Login, Server, Schema, Resources, Syntax },
  computed: {
    ...mapFields([
      'index',
      'server',
      'database',
      'headerTab',
      'headerTabSelected',
      'rights',
      'rightsItem',
      'rightsSelected',
      'rightsLoginForm',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('show-rights', this.showDialog);
    EventBus.$on('reload-rights', this.reloadRights);
    EventBus.$on('get-rights', this.getRights);
  },
  watch: {
    dialog: function(value) {
      if (!value) {
        const tab = {'client': 0, 'structure': 1, 'content': 2, 'info': 3, 'objects': 6}
        this.headerTab = tab[this.headerTabSelected]
        this.tab = 0
      }
    },
    checkDialog: function(val) {
      if (val) this.resizeTable()
    },
    rightsItem: {
      handler(val) {
        if (
          Object.keys(val['login']).length == 0 && 
          val['server']['grant'].length == 0 && val['server']['revoke'].length == 0 &&
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
    onGridReady(params) {
      this.gridApi = params.api
      this.columnApi = params.columnApi
      this.resizeTable()
    },
    resizeTable() {
      this.$nextTick(() => {
        if (this.gridApi != null) {
          // this.gridApi.sizeColumnsToFit()
          let allColIds = this.columnApi.getAllColumns().map(column => column.colId)
          this.columnApi.autoSizeColumns(allColIds)
        }
      })
    },
    onSplitPaneReady() {
    },
    getRights(user, host) {
      this.loading = true
      const payload = {
        connection: this.index,
        server: this.server.id,
        user,
        host
      }
      axios.get('/client/rights', { params: payload })
        .then((response) => {
          this.errors = { login: [], server: [], schema: [], resources: [] }
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
        .finally(() => { this.loading = false })
    },
    parseRightsSidebar(data) {
      if ('rights' in data) {
        var rights = []
        for (let right of data['rights']) {
          let index = rights.findIndex(k => k['name'] == right['user'])
          if (index == -1) rights.push({ id: right['user'], name: right['user'], children: [{ id: right['user'] + '|' + right['host'], user: right['user'], name: right['host'] }] })
          else rights[index]['children'].push({ id: right['user'] + '|' + right['host'], user: right['user'], name: right['host'] })
        }
        this.rights = { sidebar: rights.slice(0), login: {}, server: {}, schema: [], resources: {}, syntax: '' }
        this.rightsSelected = {}
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
      }
      // Reload Rights
      EventBus.$emit('reload-rights', 'edit')
    },
    reloadRights(mode) {
      this.mode = mode
      if (mode == 'new') this.tab = 0
    },
    saveClick() {
      // Check if all login fields are filled
      if (!this.rightsLoginForm.validate()) {
        EventBus.$emit('send-notification', 'Please make sure all required fields are filled out correctly', 'error')
        return
      }
      // Build check dialog
      this.checkItems = []
      // - Login -
      if (Object.keys(this.rightsItem['login']).length != 0) {
        let passwordType = 'passwordType' in this.rightsItem['login'] ? this.rightsItem['login']['passwordType'] : this.rights['login']['passwordType']
        let query = "GRANT USAGE ON *.* TO '" + this.rightsSelected['user'] + "'@'" + this.rightsSelected['name'] + "' IDENTIFIED " + (passwordType == 'Hash' ? 'BY PASSWORD' : 'BY') + " '" + this.rightsItem['login']['password'] + "';"
        this.checkItems.push({ section: 'login', action: 'Modify', object: 'Password', right: '', before: this.rights['login']['password'], after: this.rightsItem['login']['password'], query })        
      }
      // - Server -
      let serverRights = Object.keys(this.rights['server']).reduce((acc, val) => { if (this.rights['server'][val]) acc.push(val); return acc; }, [])
      let newServerRights = serverRights.concat(this.rightsItem['server']['grant'])
      if (this.rightsItem['server']['grant'].length > 0) {
        let query = "GRANT " + this.parseRights(this.rightsItem['server']['grant']) + " ON *.* TO '" + this.rightsSelected['user'] + "'@'" + this.rightsSelected['name'] + "';"
        this.checkItems.push({ section: 'server', action: 'Grant', object: '*', right: this.parseRights(this.rightsItem['server']['grant']), before: this.parseRights(serverRights), after: this.parseRights(newServerRights), query })        
      }
      if (this.rightsItem['server']['revoke'].length > 0) {
        let query = "REVOKE " + this.parseRights(this.rightsItem['server']['revoke']) + " ON *.* FROM '" + this.rightsSelected['user'] + "'@'" + this.rightsSelected['name'] + "';"
        this.checkItems.push({ section: 'server', action: 'Revoke', object: '*', right: this.parseRights(this.rightsItem['server']['revoke']), before: this.parseRights(newServerRights), after: this.parseRights(newServerRights.filter(x => !this.rightsItem['server']['revoke'].includes(x))), query })        
      }
      // - Schema -
      for (let item of this.rightsItem['schema']['grant']) {
        let old = 'old' in item ? item['old'] : []
        let query = "GRANT " + this.parseSchemaRights(item) + " TO '" + this.rightsSelected['user'] + "'@'" + this.rightsSelected['name'] + "';"
        this.checkItems.push({ section: 'schema', action: 'Grant', object: item['schema'], right: this.parseRights(item['rights']), before: this.parseRights(old), after: this.parseRights(old.concat(item['rights'])), query })        
      }
      for (let item of this.rightsItem['schema']['revoke']) {
        let old = 'old' in item ? item['old'] : []
        let query = "REVOKE " + this.parseSchemaRights(item) + " FROM '" + this.rightsSelected['user'] + "'@'" + this.rightsSelected['name'] + "';"
        this.checkItems.push({ section: 'schema', action: 'Revoke', object: item['schema'], right: this.parseRights(item['rights']), before: this.parseRights(old), after: this.parseRights(old.filter(x => !item.rights.includes(x))), query })        
      }
      // - Resources -
      if ('max_queries' in this.rightsItem['resources']) {
        let query = "GRANT USAGE ON *.* TO '" + this.rightsSelected['user'] + "'@'" + this.rightsSelected['name'] + "' WITH MAX_QUERIES_PER_HOUR " + this.rightsItem['resources']['max_queries'] + ";"
        this.checkItems.push({ section: 'resources', action: 'Modify', object: 'Max Queries', right: '', before: this.rights['resources']['max_queries'], after: this.rightsItem['resources']['max_queries'], query })
      }
      if ('max_updates' in this.rightsItem['resources']) {
        let query = "GRANT USAGE ON *.* TO '" + this.rightsSelected['user'] + "'@'" + this.rightsSelected['name'] + "' WITH MAX_UPDATES_PER_HOUR " + this.rightsItem['resources']['max_updates'] + ";"
        this.checkItems.push({ section: 'resources', action: 'Modify', object: 'Max Updates', right: '', before: this.rights['resources']['max_updates'], after: this.rightsItem['resources']['max_updates'], query })
      }
      if ('max_connections' in this.rightsItem['resources']) {
        let query = "GRANT USAGE ON *.* TO '" + this.rightsSelected['user'] + "'@'" + this.rightsSelected['name'] + "' WITH MAX_CONNECTIONS_PER_HOUR " + this.rightsItem['resources']['max_connections'] + ";"
        this.checkItems.push({ section: 'resources', action: 'Modify', object: 'Max Connections', right: '', before: this.rights['resources']['max_connections'], after: this.rightsItem['resources']['max_connections'], query })
      }
      if ('max_simultaneous' in this.rightsItem['resources']) {
        let query = "GRANT USAGE ON *.* TO '" + this.rightsSelected['user'] + "'@'" + this.rightsSelected['name'] + "' WITH MAX_USER_CONNECTIONS " + this.rightsItem['resources']['max_simultaneous'] + ";"
        this.checkItems.push({ section: 'resources', action: 'Modify', object: 'Max Simultaneous Connections', right: '', before: this.rights['resources']['max_simultaneous'], after: this.rightsItem['resources']['max_simultaneous'], query })
      }
      this.checkDialog = true
    },
    checkSubmit() {
      // Execute generated queries
      this.loading = true
      const payload = {
        connection: this.index,
        server: this.server.id,
        database: null,
        queries: this.checkItems.map((x) => { return x.query }),
        executeAll: true,
      }
      axios.post('/client/execute', payload)
        .then(() => {
          this.checkDialog = false
          EventBus.$emit('send-notification', 'Rights saved successfully', 'success')
          this.getRights(this.rightsSelected['user'], this.rightsSelected['name'])
        })
        .catch((error) => {
          this.checkDialog = false
          // Build error dialog
          this.errors = { login: [], server: [], schema: [], resources: [] }
          let data = JSON.parse(error.response.data.data)
          for (let obj of data) {
            let item = this.checkItems.find(x => x.query == obj.query )
            this.errors[item['section']].push(obj)
          }
          this.errorDialog = true
        })
        .finally(() => { this.loading = false })
    },
    parseRights(rights) {
      return rights.map((x) => { return x.charAt(0).toUpperCase() + x.slice(1).replaceAll('_', ' ') }).join(', ')
    },
    parseSchemaRights(resource) {
      if (resource.type == 'database') {
        return this.parseRights(resource.rights) + ' ON `' + resource.schema + '`.*'
      }
      else if (resource.type == 'table') {
        return this.parseRights(resource.rights) + ' ON `' + resource.schema.split('.')[0] + '`.' + resource.schema.split('.')[1]
      }
      else if (resource.type == 'column') {
        let rights = resource.rights.map((x) => { return x.charAt(0).toUpperCase() + x.slice(1).replaceAll('_', ' ') + ' (`' + resource.schema.split('.')[2] + '`)' }).join(', ')
        return rights + ' ON `' + resource.schema.split('.')[0] + '`.' + resource.schema.split('.')[1]
      }
    },
    capitalizeFirstLetter(string) {
      return string.charAt(0).toUpperCase() + string.slice(1);
    },
  }
}
</script>