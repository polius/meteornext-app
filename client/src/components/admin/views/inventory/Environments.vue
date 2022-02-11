<template>
  <div>
    <v-data-table v-model="selected" :headers="computedHeaders" :items="items" :search="filter.search" :loading="loading" loading-text="Loading... Please wait" item-key="id" show-select class="elevation-1" mobile-breakpoint="0">
      <template v-ripple v-slot:[`header.data-table-select`]="{}">
        <v-simple-checkbox
          :value="items.length == 0 ? false : selected.length == items.length"
          :indeterminate="selected.length > 0 && selected.length != items.length"
          @click="selected.length == items.length ? selected = [] : selected = [...items]">
        </v-simple-checkbox>
      </template>
      <template v-slot:[`item.name`]="{ item }">
        <v-icon small :title="item.shared ? item.secured ? 'Shared (Secured)' : 'Shared' : item.secured ? 'Personal (Secured)' : 'Personal'" :color="item.shared ? '#EB5F5D' : 'warning'" :style="`margin-bottom:2px; ${!item.secured ? 'padding-right:8px' : ''}`">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
        <v-icon v-if="item.secured" :title="item.shared ? 'Shared (Secured)' : 'Personal (Secured)'" :color="item.shared ? '#EB5F5D' : 'warning'" style="font-size:12px; padding-left:2px; padding-top:2px; padding-right:8px">fas fa-lock</v-icon>
        {{ item.name }}
      </template>
      <template v-slot:[`item.servers`]="{ item }">
        <span class="font-weight-medium">{{item.servers}}</span>
      </template>
    </v-data-table>

    <v-dialog v-model="dialog" persistent max-width="896px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:2px">{{ getIcon(mode) }}</v-icon>{{ dialog_title }}</v-toolbar-title>
          <v-divider v-if="mode != 'delete'" class="mx-3" inset vertical></v-divider>
          <v-btn v-if="mode != 'delete'" title="Create the environment only for a user" :color="!item.shared ? 'primary' : '#779ecb'" @click="item.shared = false" style="margin-right:10px;"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-user</v-icon>Personal</v-btn>
          <v-btn v-if="mode != 'delete'" title="Create the environment for all users in a group" :color="item.shared ? 'primary' : '#779ecb'" @click="item.shared = true"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-users</v-icon>Shared</v-btn>
          <v-divider v-if="mode != 'delete'" class="mx-3" inset vertical></v-divider>
          <v-checkbox v-if="mode != 'delete'" title="Prevent this resource from being edited and hide sensible data" v-model="item.secured" flat color="white" hide-details>
            <template v-slot:label>
              <div style="color:white">Secured</div>
            </template>
          </v-checkbox>
          <v-spacer></v-spacer>
          <v-btn icon @click="dialog = false"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form v-if="mode != 'delete'" ref="form" style="margin-top:15px; margin-bottom:15px">
                  <v-row no-gutters style="margin-bottom:15px">
                    <v-col>
                      <v-autocomplete ref="group_id" @change="groupChanged" v-model="item.group_id" :items="groups" item-value="id" item-text="name" label="Group" :rules="[v => !!v || '']" hide-details style="padding-top:0px; margin-top:0px"></v-autocomplete>
                    </v-col>
                    <v-col v-if="!item.shared" style="margin-left:20px">
                      <v-autocomplete ref="owner_id" @change="ownerChanged" v-model="item.owner_id" :items="users" item-value="id" item-text="username" label="Owner" :rules="[v => !!v || '']" hide-details style="padding-top:0px; margin-top:0px"></v-autocomplete>
                    </v-col>
                  </v-row>
                  <v-text-field ref="name" @keypress.enter.native.prevent="submitEnvironment()" v-model="item.name" :rules="[v => !!v || '']" label="Name" required></v-text-field>
                  <v-card>
                    <v-toolbar flat dense color="#2e3131">
                      <v-toolbar-title class="white--text subtitle-1">SERVERS</v-toolbar-title>
                      <v-divider class="mx-3" inset vertical></v-divider>
                      <v-text-field v-model="treeviewSearch" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
                    </v-toolbar>
                    <v-card-text style="padding: 10px;">
                      <div v-if="treeviewItems.length == 0" class="text-body-2" style="text-align:center">Select a group</div>
                      <v-treeview :active.sync="treeviewSelected" item-key="id" :items="treeviewFiltered" :open="treeviewOpened" :search="treeviewSearch" hoverable open-on-click multiple-active activatable transition>
                        <template v-slot:label="{ item }">
                          <v-icon v-if="item.children" small :title="item.shared ? 'Shared' : 'Personal'" :color="item.shared ? '#EF5354' : 'warning'" :style="item.shared ? 'margin-right:10px; margin-bottom:2px' : 'margin-left:2px; margin-right:16px; margin-bottom:2px'">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          {{ item.name }}
                        </template>
                        <template v-slot:prepend="{ item }">
                          <v-icon v-if="!item.children" small>fas fa-server</v-icon>
                        </template>
                        <template v-slot:append="{ item }">
                          <v-chip v-if="!item.children" label><v-icon small :color="item.shared ? '#EF5354' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>{{ item.shared ? 'Shared' : 'Personal' }}</v-chip>
                        </template>
                      </v-treeview>
                    </v-card-text>
                  </v-card>
                </v-form>
                <div v-else class="subtitle-1" style="margin-bottom:12px">Are you sure you want to delete the selected environments?</div>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :loading="loading" color="#00b16a" @click="submitEnvironment()">CONFIRM</v-btn>
                  <v-btn :disabled="loading" color="#EF5354" @click="dialog=false" style="margin-left:5px;">CANCEL</v-btn>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!-------------------->
    <!-- COLUMNS DIALOG -->
    <!-------------------->
    <v-dialog v-model="columnsDialog" max-width="600px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="text-subtitle-1 white--text">FILTER COLUMNS</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="selectAllColumns" text title="Select all columns" style="height:100%"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-check-square</v-icon>Select all</v-btn>
          <v-btn @click="deselectAllColumns" text title="Deselect all columns" style="height:100%"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-square</v-icon>Deselect all</v-btn>
          <v-spacer></v-spacer>
          <v-btn icon @click="columnsDialog = false" style="width:40px; height:40px"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 0px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:15px; margin-bottom:20px;">
                  <div class="text-body-1" style="margin-bottom:10px">Select the columns to display:</div>
                  <v-checkbox v-model="columnsRaw" label="Name" value="name" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Servers" value="servers" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Group" value="group" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Owner" value="owner" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Created By" value="created_by" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Created At" value="created_at" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Updated By" value="updated_by" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Updated At" value="updated_at" hide-details style="margin-top:5px"></v-checkbox>
                  <v-divider style="margin-top:15px;"></v-divider>
                  <div style="margin-top:20px;">
                    <v-btn @click="filterColumns" :loading="loading" color="#00b16a">Confirm</v-btn>
                    <v-btn :disabled="loading" color="#EF5354" @click="columnsDialog = false" style="margin-left:5px;">Cancel</v-btn>
                  </div>
                </v-form>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
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
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Servers', align: 'left', value: 'servers' },
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
    item: { group_id: '', owner_id: '', name: '', shared: false, secured: false, },
    environment_servers: {},
    mode: '',
    loading: true,
    dialog: false,
    dialog_title: '',
    users: [],
    // Servers Treeview
    treeviewItems: [],
    treeviewShared: {0: [], 1: []},
    treeviewSelected: [],
    treeviewOpened: [],
    treeviewSearch: '',
    // Filter Columns Dialog
    columnsDialog: false,
    columns: ['name','servers','shared','group','owner'],
    columnsRaw: [],
  }),
  props: ['tab','groups','filter'],
  mounted() {
    EventBus.$on('get-environments', this.getEnvironments);
    EventBus.$on('filter-environments', this.filterEnvironments);
    EventBus.$on('filter-environment-columns', this.filterEnvironmentColumns);
    EventBus.$on('new-environment', this.newEnvironment);
    EventBus.$on('clone-environment', this.cloneEnvironment);
    EventBus.$on('edit-environment', this.editEnvironment);
    EventBus.$on('delete-environment', this.deleteEnvironment);
  },
  computed: {
    computedHeaders() { return this.headers.filter(x => this.columns.includes(x.value)) },
    treeviewFiltered: function() {
      var items = JSON.parse(JSON.stringify(this.treeviewItems))
      if (this.item.shared) {
        for (let i = 0; i < items.length; ++i) {
          for (let j = items[i]['children'].length - 1; j >= 0; --j) {
            if (items[i]['children'][j]['shared'] == 0) {
              items[i]['children'].splice(j, 1)
            }
          }
          if (items[i]['children'].length == 0) items.splice(i, 1)
        }
      }
      else {
        for (let i = 0; i < items.length; ++i) {
          for (let j = items[i]['children'].length - 1; j >= 0; --j) {
            if (items[i]['children'][j]['shared'] == 0 && items[i]['children'][j]['owner'] != this.item.owner_id) {
              items[i]['children'].splice(j, 1)
            }
          }
          if (items[i]['children'].length == 0) items.splice(i, 1)
        }
      }
      return items
    },
  },
  methods: {
    groupChanged() {
      this.treeviewItems = []
      this.treeviewOpened = []
      this.treeviewSelected = []
      this.item.owner_id = null
      if (this.item.shared) {
        if (this.item.group_id != null) {
          this.getServers()
          this.getUsers()
        }
      }
      else {
        requestAnimationFrame(() => {
          if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
          if (!this.item.shared) this.$refs.owner_id.focus()
        })
        this.getUsers()
      }
    },
    ownerChanged() {
      if (!this.item.shared) {
        this.treeviewItems = []
        this.treeviewOpened = []
        this.treeviewSelected = []
        this.getServers()
      }
    },
    getUsers() {
      axios.get('/admin/inventory/users', { params: { group_id: this.item.group_id }})
        .then((response) => {
          this.users = response.data.users
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    getServers() {
      axios.get('/admin/inventory/environments/servers', { params: { group_id: this.item.group_id, owner_id: this.item.owner_id }})
        .then((response) => {
          this.environment_servers = this.parseEnvironmentServers(response.data.environment_servers)
          this.treeviewItems = this.parseTreeView(response.data.servers)
          if (['edit','clone'].includes(this.mode)) setTimeout(this.updateSelected, 1)
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    getEnvironments() {
      this.loading = true
      const payload = (this.filter.by == 'group' && this.filter.group != null) ? { group_id: this.filter.group } : (this.filter.by == 'user' && this.filter.user != null) ? { user_id: this.filter.user } : {}
      axios.get('/admin/inventory/environments', { params: payload})
        .then((response) => {
          response.data.environments.map(x => {
            x['created_at'] = this.dateFormat(x['created_at'])
            x['updated_at'] = this.dateFormat(x['updated_at'])
          })
          this.environments = response.data.environments
          this.items = this.environments.slice(0)
          this.filterBy()
          this.loading = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
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
        if (!found) regions.push({ id: servers[i]['region_id'], name: servers[i]['region_name'], shared: servers[i]['region_shared'] })
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
            region['children'].push({ id: servers[j]['server_id'], name: servers[j]['server_name'], shared: servers[j]['server_shared'], owner: servers[j]['server_owner'] })
            this.treeviewShared[servers[j]['server_shared']].push(servers[j]['server_id'])
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
      this.users = []
      this.item = { group_id: this.filter.group, owner_id: '', name: '', shared: false, secured: false }
      if (this.filter.group != null) { this.getUsers(); this.getServers() }
      this.treeviewItems = []
      this.treeviewSelected = []
      this.treeviewOpened = []
      this.dialog_title = 'NEW ENVIRONMENT'
      this.dialog = true
    },
    cloneEnvironment() {
      this.mode = 'clone'
      this.users = []
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.getUsers()
      this.getServers()
      this.dialog_title = 'CLONE ENVIRONMENT'
      this.dialog = true
    },  
    editEnvironment() {
      this.mode = 'edit'
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.getUsers()
      this.getServers()
      this.dialog_title = 'EDIT ENVIRONMENT'
      this.dialog = true
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
      this.dialog_title = 'DELETE ENVIRONMENT'
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
      axios.post('/admin/inventory/environments', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getEnvironments()
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
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
      axios.put('/admin/inventory/environments', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          // Edit item in the data table
          this.getEnvironments()
          this.selected = []
          this.treeviewSelected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    deleteEnvironmentSubmit() {
      const payload = { environments: JSON.stringify(this.selected.map((x) => x.id)) }
      // Delete items to the DB
      axios.delete('/admin/inventory/environments', { params: payload })
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getEnvironments()
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    filterBy() {
      let environments = JSON.parse(JSON.stringify(this.environments))
      // Filter by scope
      if (this.filter.scope == 'personal') environments = environments.filter(x => !x.shared)
      else if (this.filter.scope == 'shared') environments = environments.filter(x => x.shared)
      // Filter by secured
      if (this.filter.secured == 'secured') environments = environments.filter(x => x.secured)
      else if (this.filter.secured == 'not_secured') environments = environments.filter(x => !x.secured)
      // Assign filter
      this.items = environments
    },
    filterEnvironments() {
      this.selected = []
      if (this.filter.group != null) this.columns = this.columns.filter(x => x != 'group')
      else if (!this.columns.some(x => x == 'group')) this.columns.push('group')
      this.getEnvironments()
    },
    filterEnvironmentColumns() {
      this.columnsRaw = [...this.columns]
      this.columnsDialog = true
    },
    selectAllColumns() {
      this.columnsRaw = ['name','servers','shared','group','owner','created_by','created_at','updated_by','updated_at']
    },
    deselectAllColumns() {
      this.columnsRaw = []
    },
    filterColumns() {
      this.columns = [...this.columnsRaw]
      this.columnsDialog = false
    },
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
    getIcon(mode) {
      if (mode == 'new') return 'fas fa-plus'
      if (mode == 'edit') return 'fas fa-feather-alt'
      if (mode == 'delete') return 'fas fa-minus'
      if (mode == 'clone') return 'fas fa-clone'
    },
    notification(message, color, persistent=false) {
      EventBus.$emit('notification', message, color, persistent)
    }
  },
  watch: {
    dialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
        if (this.mode == 'new') {
          if (this.filter.group == null) this.$refs.group_id.focus()
          else this.$refs.name.focus()
        }
        else if (['clone','edit'].includes(this.mode)) this.$refs.name.focus()
      })
    },
    selected(val) {
      EventBus.$emit('change-selected', val)
    },
    tab(val) {
      this.selected = []
      if (val == 2) this.getEnvironments()
    },
    treeviewFiltered() {
      if (this.item.shared && this.treeviewItems.length > 0) {
        // Remove shared from treeview selected elements
        this.treeviewSelected = this.treeviewSelected.filter(x => !this.treeviewShared[0].includes(x))
      }
    },
  },
}
</script>