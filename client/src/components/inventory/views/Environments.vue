<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">ENVIRONMENTS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items>
          <v-btn text @click="newEnvironment()"><v-icon small style="margin-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn :disabled="selected.length != 1 || selected[0].secured == 1" text @click="editEnvironment()"><v-icon small style="margin-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
          <v-btn :disabled="selected.length != 1 || selected[0].secured == 1" @click="cloneEnvironment()" text><v-icon small style="margin-right:10px">fas fa-clone</v-icon>CLONE</v-btn>
          <v-btn :disabled="selected.length == 0 || selected.some(x => x.secured) || (!owner && selected.some(x => x.shared))" text @click="deleteEnvironment()"><v-icon small style="margin-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn text class="body-2" @click="filterBy('all')" :style="filter == 'all' ? 'font-weight:600' : 'font-weight:400'">ALL</v-btn>
          <v-btn text class="body-2" @click="filterBy('personal')" :style="filter == 'personal' ? 'font-weight:600' : 'font-weight:400'">PERSONAL</v-btn>
          <v-btn text class="body-2" @click="filterBy('shared')" :style="filter == 'shared' ? 'font-weight:600' : 'font-weight:400'">SHARED</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
        </v-toolbar-items>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" @current-items="(items) => current = items" :loading="loading" loading-text="Loading... Please wait" item-key="id" show-select class="elevation-1" style="padding-top:3px;" mobile-breakpoint="0">
        <template v-ripple v-slot:[`header.data-table-select`]="{}">
          <v-simple-checkbox
            :value="items.length == 0 ? false : selected.length == items.length"
            :indeterminate="selected.length > 0 && selected.length != items.length"
            @click="checkboxClick">
          </v-simple-checkbox>
        </template>
        <template v-slot:[`item.name`]="{ item }">
          <v-icon small :title="item.shared ? item.secured ? 'Shared (Secured)' : 'Shared' : item.secured ? 'Personal (Secured)' : 'Personal'" :color="item.shared ? '#EB5F5D' : 'warning'" :style="`margin-bottom:2px; ${!item.secured ? 'padding-right:8px' : ''}`">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
          <v-icon v-if="item.secured" :title="item.shared ? 'Shared (Secured)' : 'Personal (Secured)'" :color="item.shared ? '#EB5F5D' : 'warning'" style="font-size:12px; padding-left:2px; padding-top:2px; padding-right:8px">fas fa-lock</v-icon>
          {{ item.name }}
        </template>
        <template v-slot:[`item.servers`]="{ item }">
          <div v-for="server in item.servers" :key="server.id" style="margin-left:0px; padding-left:0px; float:left; margin-right:5px; padding-top:3px; padding-bottom:3px;">
            <v-chip outlined label :color="server.color" style="margin-left:0px;">
              <v-icon v-if="!server.active" small color="warning" title="Maximum allowed resources exceeded. Upgrade your license to have more servers." style="margin-right:10px">fas fa-exclamation-triangle</v-icon>
              <span class="font-weight-medium" style="padding-right:4px;">{{ server.server }}</span>
              - {{ server.region }}
            </v-chip>
          </div>
        </template>
        <template v-slot:[`footer.prepend`]>
          <div v-if="disabledResources" class="text-body-2 font-weight-regular" style="margin:10px"><v-icon small color="warning" style="margin-right:10px; margin-bottom:2px">fas fa-exclamation-triangle</v-icon>Some environments contain servers that are disabled. Consider the possibility of upgrading your license.</div>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="dialog" persistent max-width="896px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:2px">{{ getIcon(mode) }}</v-icon>{{ dialog_title }}</v-toolbar-title>
          <v-divider v-if="mode != 'delete'" class="mx-3" inset vertical></v-divider>
          <v-btn v-if="mode != 'delete'" :disabled="(item.shared == 1 && !owner)" @click="item.shared = false" title="Create the environment only for you" :color="!item.shared ? 'primary' : '#779ecb'" style="margin-right:10px;"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-user</v-icon>Personal</v-btn>
          <v-btn v-if="mode != 'delete'" :disabled="(item.shared == 0 && !owner)" @click="item.shared = true" title="Create the environment for all users in your group" :color="item.shared ? 'primary' : '#779ecb'"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-users</v-icon>Shared</v-btn>
          <v-spacer></v-spacer>
          <v-btn icon @click="dialog = false"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-alert v-if="mode != 'delete' && !owner && item.shared" color="warning" outlined dense style="margin-bottom:30px"><v-icon color="warning" style="font-size:16px; margin-bottom:3px; margin-right:10px">fas fa-exclamation-triangle</v-icon>This resource cannot be edited. You are not a group owner.</v-alert>
                <v-form v-if="mode != 'delete'" ref="form" style="margin-top:15px; margin-bottom:15px;">
                  <v-text-field :readonly="readonly" ref="field" @keypress.enter.native.prevent="submitEnvironment()" v-model="item.name" :rules="[v => !!v || '']" label="Name" required style="margin-top:0px; padding-top:0px"></v-text-field>
                  <v-card>
                    <v-toolbar flat dense color="#2e3131">
                      <v-toolbar-title class="white--text subtitle-1">SERVERS</v-toolbar-title>
                      <v-divider class="mx-3" inset vertical></v-divider>
                      <v-text-field v-model="treeviewSearch" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
                    </v-toolbar>
                    <v-card-text style="padding: 10px;">
                      <div v-if="treeviewItems.length == 0" class="text-body-2" style="text-align:center;">No servers to be selected</div>
                      <v-treeview :active.sync="treeviewSelected" item-key="id" :items="treeviewFiltered" :open="treeviewOpened" :search="treeviewSearch" hoverable open-on-click multiple-active :activatable="!readonly" transition>
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
                <div v-else>
                  <div class="subtitle-1">Are you sure you want to delete the selected environments?</div>
                  <v-card style="margin-top:15px; margin-bottom:15px">
                    <v-list>
                      <v-list-item v-for="item in selected" :key="item.id" style="min-height:35px">
                        <v-list-item-content style="padding:0px">
                          <v-list-item-title>
                            <v-icon small :title="item.shared ? item.secured ? 'Shared (Secured)' : 'Shared' : item.secured ? 'Personal (Secured)' : 'Personal'" :color="item.shared ? '#EB5F5D' : 'warning'" :style="`margin-bottom:2px; ${!item.secured ? 'padding-right:8px' : ''}`">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                            <v-icon v-if="item.secured" :title="item.shared ? 'Shared (Secured)' : 'Personal (Secured)'" :color="item.shared ? '#EB5F5D' : 'warning'" style="font-size:12px; padding-left:2px; padding-top:2px; padding-right:8px">fas fa-lock</v-icon>
                            {{ item.name }}
                          </v-list-item-title>
                        </v-list-item-content>
                      </v-list-item>
                    </v-list>
                  </v-card>
                  <v-checkbox v-model="dialogConfirm" label="I confirm I want to delete the selected environments." hide-details class="body-1" style="margin-bottom:15px"></v-checkbox>
                </div>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :disabled="mode == 'delete' && !dialogConfirm" :loading="loading" color="#00b16a" @click="submitEnvironment()">CONFIRM</v-btn>
                  <v-btn :disabled="loading" color="#EF5354" @click="dialog=false" style="margin-left:5px;">CANCEL</v-btn>
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

<style>
td {
  padding-top:5px!important;
  padding-bottom:5px!important;
}
</style>

<script>
import axios from 'axios'
export default {
  data: () => ({
    // Data Table
    disabledResources: false,
    filter: 'all',
    headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Servers', align: 'left', value: 'servers' },
    ],
    environments: [],
    items: [],
    current: [],
    selected: [],
    item: { name: '', shared: true },
    environment_servers: {},
    search: '',
    mode: '',
    loading: true,
    dialog: false,
    dialog_title: '',
    dialogConfirm: false,
    // Servers Treeview
    treeviewItems: [],
    treeviewShared: {0: [], 1: []},
    treeviewSelected: [],
    treeviewOpened: [],
    treeviewSearch: '',
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  computed: {
    owner: function() { return this.$store.getters['app/owner'] },
    readonly: function() { return this.item.shared == 1 && !this.owner },
    treeviewFiltered: function() {
      if (this.item.shared && this.treeviewItems.length > 0) {
        var items = JSON.parse(JSON.stringify(this.treeviewItems))
        for (let i = 0; i < items.length; ++i) {
          for (let j = items[i]['children'].length - 1; j >= 0; --j) {
            if (items[i]['children'][j]['shared'] == 0) {
              items[i]['children'].splice(j, 1)
            }
          }
          if (items[i]['children'].length == 0) items.splice(i, 1)
        }
        return items
      }
      else return this.treeviewItems
    },
  },
  created() {
    this.getEnvironments()
  },
  methods: {
    getEnvironments() {
      this.loading = true
      axios.get('/inventory/environments')
        .then((response) => {
          this.treeviewItems = this.parseTreeView(response.data.servers)
          this.environment_servers = this.parseEnvironmentServers(response.data.environment_servers)
          this.environments = this.parseEnvironments(response.data.environments)
          this.items = this.environments.slice(0)
          this.filterBy(this.filter)
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    parseTreeView(servers) {
      var treeview = []
      var regions = []
      // Fill regions
      for (let i = 0; i < servers.length; ++i) {
        let found = false
        for (let j = 0; j < regions.length; ++j) {
          found = (servers[i]['region_id'] == regions[j]['id'])
          if (found) break
        }
        if (!found && servers[i]['region_id'] != null) regions.push({ id: servers[i]['region_id'], name: servers[i]['region_name'], shared: servers[i]['region_shared'] })
      }
      // Sort regions ASC by name
      regions.sort(function(a,b) { 
        if (a.name < b.name) return -1 
        else if (a.name > b.name) return 1
        return 0
      })
      // Fill treeview
      for (let i = 0; i < regions.length; ++i) {
        let region = { id: 'r'+regions[i]['id'], name: regions[i]['name'], shared: regions[i]['shared'], children: []}
        for (let j = 0; j < servers.length; ++j) {
          if (regions[i]['name'] == servers[j]['region_name']) {
            region['children'].push({ id: servers[j]['server_id'], name: servers[j]['server_name'], shared: servers[j]['server_shared'], active: servers[j]['server_active'] })
            this.treeviewShared[servers[j]['server_shared']].push(servers[j]['server_id'])
          }
        }
        // Sort servers ASC by name
        region['children'].sort(function(a,b) { 
          if (a.name < b.name) return -1 
          else if (a.name > b.name) return 1
          return 0
        })
        treeview.push(region)
      }
      return treeview
    },
    parseEnvironments(environments) {
      var data = []
      var regions = []
      var colors = ['#eb5f5d', '#fa8231', '#00b16a', '#9c59b6', '#2196f3']
      // Fill regions
      for (let i = 0; i < this.treeviewItems.length; ++i) regions.push(this.treeviewItems[i]['name'])
      regions.sort()
      
      // Parse Environments
      for (let i = 0; i < environments.length; ++i) {
        let row = { id: environments[i]['id'], name: environments[i]['name'], shared: environments[i]['shared'], secured: environments[i]['secured'], servers: []}
        if (environments[i]['id'] in this.environment_servers) {
          for (let j = 0; j < this.environment_servers[environments[i]['id']].length; ++j) {
            for (let k = 0; k < this.environment_servers[environments[i]['id']][j]['children'].length; ++k) {
              let region_name = this.environment_servers[environments[i]['id']][j]['name']
              let server_name = this.environment_servers[environments[i]['id']][j]['children'][k]['name']
              let server_active = this.environment_servers[environments[i]['id']][j]['children'][k]['active']
              let color_next = regions.indexOf(region_name) < colors.length ? colors[regions.indexOf(region_name)] : ''
              row['servers'].push({ region: region_name, server: server_name, active: server_active, color: color_next })
            }
          }
        }
        // Sort servers ASC by region_name
        row['servers'].sort(function(a,b) { 
          if (a.region < b.region) return -1
          else if (a.region > b.region) return 1
          else {
            if (a.server < b.server) return -1
            else if (a.server > b.server) return 1
            else return 0
          }
        })
        // Add row to array
        data.push(row)
      }
      return data
    },
    parseEnvironmentServers(environment_servers) {
      var data = {}
      
      for (let i = 0; i < environment_servers.length; ++i) {
        if (environment_servers[i]['environment_id'] in data) {
          let found = false 
          for (let j = 0; j < data[environment_servers[i]['environment_id']]; ++j) {
            if (data[environment_servers[i]['environment_id']][j]['id'] == environment_servers[i]['region_id']) {
              data[environment_servers[i]['environment_id']][j]['children'].push({ id: environment_servers[i]['server_id'], name: environment_servers[i]['server_name'], active: environment_servers[i]['server_active'] })
              found = true
              break
            }
          }
          if (!found) data[environment_servers[i]['environment_id']].push({ id: 'r' + environment_servers[i]['region_id'], name: environment_servers[i]['region_name'], children: [{ id: environment_servers[i]['server_id'], name: environment_servers[i]['server_name'], active: environment_servers[i]['server_active'] }] })
        }
        else data[environment_servers[i]['environment_id']] = [{ id: 'r' + environment_servers[i]['region_id'], name: environment_servers[i]['region_name'], children: [{ id: environment_servers[i]['server_id'], name: environment_servers[i]['server_name'], active: environment_servers[i]['server_active'] }] }]
      }
      return data
    },
    newEnvironment() {
      this.mode = 'new'
      this.item = { name: '', shared: false }
      this.treeviewSelected = []
      this.treeviewOpened = []
      this.dialog_title = 'NEW ENVIRONMENT'
      this.dialog = true
    },
    cloneEnvironment() {
      this.mode = 'clone'
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.item.shared = (!this.owner) ? false : this.item.shared
      this.dialog_title = 'CLONE ENVIRONMENT'
      this.dialog = true
      setTimeout(this.updateSelected, 1)
    },
    editEnvironment() {
      this.mode = 'edit'
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.dialog_title = 'EDIT ENVIRONMENT'
      this.dialog = true
      setTimeout(this.updateSelected, 1)
    },
    updateSelected() {
      var treeviewSelected = []
      var treeviewOpened = []
      if (Object.keys(this.environment_servers) == 0) this.treeviewSelected = []
      else {
        if (this.selected[0]['id'] in this.environment_servers) {
          for (let i = 0; i < this.environment_servers[this.selected[0]['id']].length; ++i) {
            for (let j = 0; j < this.environment_servers[this.selected[0]['id']][i]['children'].length; ++j) {
              treeviewSelected.push(this.environment_servers[this.selected[0]['id']][i]['children'][j]['id'])
              if (!treeviewOpened.includes(this.environment_servers[this.selected[0]['id']][i]['id'])) {
                treeviewOpened.push(this.environment_servers[this.selected[0]['id']][i]['id'])
              }
            }
          }
        }
        this.treeviewSelected = [...treeviewSelected]
        this.treeviewOpened = [...treeviewOpened]
      }
    },
    deleteEnvironment() {
      this.mode = 'delete'
      this.dialog_title = 'DELETE ENVIRONMENTS'
      this.dialogConfirm = false
      this.selected.sort((a, b) => a.name.localeCompare(b.name))
      this.dialog = true
    },
    submitEnvironment() {
      this.loading = true
      if (['new','clone'].includes(this.mode)) this.newEnvironmentSubmit()
      else if (this.mode == 'edit') this.editEnvironmentSubmit()
      else if (this.mode == 'delete') this.deleteEnvironmentSubmit()
    },
    newEnvironmentSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
        this.loading = false
        return
      }
      // Add item in the DB
      const payload = { ...this.item, servers: [...this.treeviewSelected] }
      axios.post('/inventory/environments', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getEnvironments()
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    editEnvironmentSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
        this.loading = false
        return
      }
      // Edit item in the DB
      const payload = { ...this.item, servers: [...this.treeviewSelected] }
      axios.put('/inventory/environments', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getEnvironments()
          this.selected = []
          this.treeviewSelected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    deleteEnvironmentSubmit() {
      const payload = { environments: JSON.stringify(this.selected.map((x) => x.id)) }
      // Delete items to the DB
      axios.delete('/inventory/environments', { params: payload })
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getEnvironments()
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    filterBy(val) {
      this.filter = val
      if (val == 'all') this.items = this.environments.slice(0)
      else if (val == 'personal') this.items = this.environments.filter(x => !x.shared)
      else if (val == 'shared') this.items = this.environments.filter(x => x.shared)
      this.disabledResources = this.items.some(x => x.servers.some(y => !y.active))
    },
    getIcon(mode) {
      if (mode == 'new') return 'fas fa-plus'
      if (mode == 'edit') return 'fas fa-feather-alt'
      if (mode == 'delete') return 'fas fa-minus'
      if (mode == 'clone') return 'fas fa-clone'
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    },
    checkboxClick() {
      if (this.search.trim().length == 0) this.selected.length == this.items.length ? this.selected = [] : this.selected = [...this.items]
      else {
        const allSelected = this.current.every(x => this.selected.find(y => y.id == x.id))
        if (allSelected) this.selected = this.selected.filter(x => !this.current.find(y => y.id == x.id))
        else this.selected = this.selected.filter(x => !this.current.find(y => y.id == x.id)).concat(this.current)
      }
    },
  },
  watch: {
    dialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
        if (typeof this.$refs.field !== 'undefined' && !this.readonly) this.$refs.field.focus()
      })
    },
    treeviewFiltered() {
      if (this.item.shared && this.treeviewItems.length > 0) {
        // Remove shared from treeview selected elements
        this.treeviewSelected = this.treeviewSelected.filter(x => !this.treeviewShared[0].includes(x))
      }
    }
  }
}
</script>