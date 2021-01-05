<template>
  <div>
    <v-data-table v-model="selected" :headers="headers" :items="items" :search="filter.search" :loading="loading" loading-text="Loading... Please wait" item-key="name" show-select class="elevation-1">
      <template v-slot:[`item.servers`]="{ item }">
        <span class="font-weight-medium">{{item.servers}}</span>
      </template>
      <template v-slot:[`item.shared`]="{ item }">
        <v-icon v-if="!item.shared" small title="Personal" color="warning" style="margin-right:6px; margin-bottom:2px;">fas fa-user</v-icon>
        <v-icon v-else small title="Shared" color="error" style="margin-right:6px; margin-bottom:2px;">fas fa-users</v-icon>
        {{ !item.shared ? 'Personal' : 'Shared' }}
      </template>
      <template v-show="filter.group == null" v-slot:[`item.group`]="{ item }">
        {{ item.group }}
      </template>
    </v-data-table>

    <v-dialog v-model="dialog" persistent max-width="896px">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">{{ dialog_title }}</v-toolbar-title>
          <v-divider v-if="mode != 'delete'" class="mx-3" inset vertical></v-divider>
          <v-btn v-if="mode != 'delete'" title="Create the environment only for a user" :color="!shared ? 'primary' : '#779ecb'" @click="shared = false" style="margin-right:10px;"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-user</v-icon>Personal</v-btn>
          <v-btn v-if="mode != 'delete'" title="Create the environment for all users in a group" :color="shared ? 'primary' : '#779ecb'" @click="shared = true"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-users</v-icon>Shared</v-btn>
          <v-spacer></v-spacer>
          <v-btn icon @click="dialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 20px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:20px; margin-bottom:15px;">
                  <v-row v-if="mode!='delete'" no-gutters style="margin-bottom:15px">
                    <v-col>
                      <v-autocomplete ref="group" @change="groupChanged" v-model="group" :items="groups" item-value="id" item-text="name" label="Group" :rules="[v => !!v || '']" hide-details style="padding-top:0px"></v-autocomplete>
                    </v-col>
                    <v-col v-if="!shared" style="margin-left:20px">
                      <v-autocomplete v-model="owner" :items="users" item-value="id" item-text="username" label="Owner" :rules="[v => !!v || '']" hide-details style="padding-top:0px"></v-autocomplete>
                    </v-col>
                  </v-row>
                  <v-text-field ref="name" v-if="mode!='delete'" @keypress.enter.native.prevent="submitEnvironment()" v-model="environment_name" :rules="[v => !!v || '']" label="Name" required></v-text-field>
                  <v-card v-if="mode!='delete'">
                    <v-toolbar flat dense color="#2e3131">
                      <v-toolbar-title class="white--text">SERVERS</v-toolbar-title>
                      <v-divider class="mx-3" inset vertical></v-divider>
                      <v-text-field v-model="treeviewSearch" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
                    </v-toolbar>
                    <v-card-text style="padding: 10px;">
                      <div v-if="treeviewItems.length == 0" class="text-body-2" style="text-align:center">Select a group</div>
                      <v-treeview :active.sync="treeviewSelected" item-key="id" :items="treeviewItems" :open="treeviewOpened" :search="treeviewSearch" hoverable open-on-click multiple-active activatable transition>
                        <template v-slot:prepend="{ item }">
                          <v-icon v-if="!item.children" small>fas fa-database</v-icon>
                        </template>
                        <template v-slot:append="{ item }">
                          <v-chip v-if="!item.children" label><v-icon small :color="item.shared ? 'error' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>{{ item.shared ? 'Shared' : 'Personal' }}</v-chip>
                        </template>
                      </v-treeview>
                    </v-card-text>
                  </v-card>
                  <div v-if="mode=='delete'" class="subtitle-1">Are you sure you want to delete the selected environments?</div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :loading="loading" color="#00b16a" @click="submitEnvironment()">CONFIRM</v-btn>
                  <v-btn :disabled="loading" color="error" @click="dialog=false" style="margin-left:5px;">CANCEL</v-btn>
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
tr:hover {
  background-color: transparent !important;
}
</style>

<script>
import EventBus from '../../js/event-bus'
import axios from 'axios'
import moment from 'moment'

export default {
  data: () => ({
    // Data Table
    headers: [
      { text: 'Id', align: ' d-none', value: 'id' },
      { text: 'GroupId', align: ' d-none', value: 'group_id' },
      { text: 'OwnerId', align: ' d-none', value: 'owner_id' },
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Servers', align: 'left', value: 'servers' },
      { text: 'Scope', align: 'left', value: 'shared' },
      { text: 'Group', align: 'left', value: 'group' },
      { text: 'Owner', align: 'left', value: 'owner' },
      { text: 'Created By', align: 'left', value: 'created_by' },
      { text: 'Created At', align: 'left', value: 'created_at' },
      { text: 'Updated By', align: 'left', value: 'updated_by' },
      { text: 'Updated At', align: 'left', value: 'updated_at' },
    ],
    environments: [],
    items: [],
    selected: [],
    search: '',
    mode: '',
    loading: true,
    dialog: false,
    dialog_title: '',
    // Dialog items
    shared: false,
    group: '',
    users: [],
    owner: '',
    environment_name: '',
    environment_servers: {},
    treeviewItems: [],
    treeviewSelected: [],
    treeviewOpened: [],
    treeviewSearch: '',
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  props: ['tab','groups','filter'],
  created() {
    this.getEnvironments()
  },
  mounted () {
    EventBus.$on('filter-environments', this.filterEnvironments);
    EventBus.$on('new-environment', this.newEnvironment);
    EventBus.$on('edit-environment', this.editEnvironment)
    EventBus.$on('delete-environment', this.deleteEnvironment);
  },
  methods: {
    groupChanged() {
      this.owner = ''
      this.getUsers()
      this.getServers()
    },
    getUsers() {
      axios.get('/admin/inventory/users', { params: { group: this.group }})
        .then((response) => {
          this.users = response.data.users
        })
        .catch((error) => {
          console.log(error)
        })
    },
    getServers() {
      axios.get('/admin/inventory/environments/servers', { params: { group: this.group }})
        .then((response) => {
          this.environment_servers = this.parseEnvironmentServers(response.data.environment_servers)
          this.treeviewItems = this.parseTreeView(response.data.servers)
          if (this.mode == 'edit') setTimeout(this.updateSelected, 1)
        })
        .catch((error) => {
          console.log(error)
        })
    },
    filterEnvironments() {
      this.selected = []
      this.getEnvironments()
    },
    getEnvironments() {
      axios.get('/admin/inventory/environments', { params: { group: this.filter.group }})
        .then((response) => {
          response.data.environments.map(x => {
            x['created_at'] = this.dateFormat(x['created_at'])
            x['updated_at'] = this.dateFormat(x['created_at'])
          })
          this.environments = response.data.environments
          this.items = this.environments.slice(0)
          this.filterBy(this.filter.scope)
          this.loading = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
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
        if (!found) regions.push({ id: servers[i]['region_id'], name: servers[i]['region_name'] })
      }
      // Sort regions ASC by name
      regions.sort(function(a,b) { 
        if (a.name < b.name) return -1 
        else if (a.name > b.name) return 1
        return 0
      })
      // Fill treeview
      for (let i = 0; i < regions.length; ++i) {
        let region = { id: 'r'+regions[i]['id'], name: regions[i]['name'], children: []}
        for (let j = 0; j < servers.length; ++j) {
          if (regions[i]['name'] == servers[j]['region_name']) {
            region['children'].push({ id: servers[j]['server_id'], name: servers[j]['server_name'], shared: servers[j]['server_shared'] })
          }
        }
        if (region['children'].length == 0) delete region['children']
        else {
          // Sort servers ASC by name
          region['children'].sort(function(a,b) { 
            if (a.name < b.name) return -1 
            else if (a.name > b.name) return 1
            return 0
          })
        }
        treeview.push(region)
      }
      return treeview
    },
    parseEnvironmentServers(environment_servers) {
      var data = {}
      
      for (let i = 0; i < environment_servers.length; ++i) {
        if (environment_servers[i]['environment_id'] in data) {
          let found = false 
          for (let j = 0; j < data[environment_servers[i]['environment_id']]; ++j) {
            if (data[environment_servers[i]['environment_id']][j]['id'] == environment_servers[i]['region_id']) {
              data[environment_servers[i]['environment_id']][j]['children'].push({ id: environment_servers[i]['server_id'], name: environment_servers[i]['server_name'] })
              found = true
              break
            }
          }
          if (!found) data[environment_servers[i]['environment_id']].push({ id: 'r' + environment_servers[i]['region_id'], name: environment_servers[i]['region_name'], children: [{ id: environment_servers[i]['server_id'], name: environment_servers[i]['server_name'] }] })
        }
        else data[environment_servers[i]['environment_id']] = [{ id: 'r' + environment_servers[i]['region_id'], name: environment_servers[i]['region_name'], children: [{ id: environment_servers[i]['server_id'], name: environment_servers[i]['server_name'] }] }]
      }
      return data
    },
    newEnvironment() {
      this.mode = 'new'
      this.shared = false
      this.group = this.filter.group
      this.owner = null
      if (this.filter.group != null) this.groupChanged()
      this.environment_name = ''
      this.treeviewItems = []
      this.treeviewSelected = []
      this.treeviewOpened = []
      this.dialog_title = 'New Environment'
      this.dialog = true
    },
    editEnvironment() {
      setTimeout(() => {
        this.mode = 'edit'
        this.environment_name = this.selected[0]['name']
        this.shared = this.selected[0]['shared']
        this.group = this.selected[0]['group_id']
        this.owner = this.selected[0]['owner_id']
        this.groupChanged()
        this.dialog_title = 'Edit Environment'
        this.dialog = true
      },0)
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
      this.dialog_title = 'Delete Environment'
      this.dialog = true
    },
    submitEnvironment() {
      this.loading = true
      if (this.mode == 'new') this.newEnvironmentSubmit()
      else if (this.mode == 'edit') this.editEnvironmentSubmit()
      else if (this.mode == 'delete') this.deleteEnvironmentSubmit()
    },
    newEnvironmentSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      // Check if new item already exists
      for (var i = 0; i < this.items.length; ++i) {
        if (this.items[i]['name'] == this.environment_name) {
          this.notification('This environment currently exists', 'error')
          this.loading = false
          return
        }
      }
      // Build servers array
      var server_list = []
      for (let i = 0; i < this.treeviewSelected.length; ++i) server_list.push(this.treeviewSelected[i])
      // Add item in the DB
      const payload = { group: this.group, owner: this.owner, shared: this.shared, name: this.environment_name, servers: server_list }
      axios.post('/admin/inventory/environments', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getEnvironments()
          this.dialog = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
        })
    },
    editEnvironmentSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      // Get Item Position
      for (var i = 0; i < this.items.length; ++i) {
        if (this.items[i]['name'] == this.selected[0]['name']) break
      }
      // Check if edited item already exists
      for (var j = 0; j < this.items.length; ++j) {
        if (this.items[j]['name'] == this.environment_name && this.environment_name != this.selected[0]['name']) {
          this.notification('This environment currently exists', 'error')
          this.loading = false
          return
        }
      }
      // Build servers array
      var server_list = []
      for (let i = 0; i < this.treeviewSelected.length; ++i) server_list.push(this.treeviewSelected[i])
      // Edit item in the DB
      const payload = { id: this.selected[0]['id'], group: this.group, owner: this.owner, shared: this.shared, name: this.environment_name, servers: server_list }
      axios.put('/admin/inventory/environments', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          // Edit item in the data table
          this.getEnvironments()
          this.dialog = false
          this.selected = []
          this.treeviewSelected = []
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
        })
    },
    deleteEnvironmentSubmit() {
      const payload = { environments: JSON.stringify(this.selected.map((x) => x.id)) }
      // Delete items to the DB
      axios.delete('/admin/inventory/environments', { params: payload })
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getEnvironments()
          this.selected = []
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
          this.dialog = false
        })
    },
    filterBy(val) {
      if (val == 'all') this.items = this.environments.slice(0)
      else if (val == 'personal') this.items = this.environments.filter(x => !x.shared)
      else if (val == 'shared') this.items = this.environments.filter(x => x.shared)
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
    dialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
        if (this.mode == 'new') {
          if (this.filter.group == null) this.$refs.group.focus()
          else this.$refs.name.focus()
        }
        else if (this.mode == 'edit') {
          if (this.group == null) this.$refs.group.focus()
          else this.$refs.name.focus()
        }
      })
    },
    selected(val) {
      EventBus.$emit('change-selected', val)
    },
    tab() {
      this.selected = []
    }
  },
}
</script>