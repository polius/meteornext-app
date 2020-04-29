<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">ENVIRONMENTS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text @click="newEnvironment()" class="body-2"><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn v-if="selected.length == 1" text @click="editEnvironment()" class="body-2"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
          <v-btn v-if="selected.length > 0" text @click="deleteEnvironment()" class="body-2"><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
        </v-toolbar-items>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" style="margin-left:10px;" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="name" show-select class="elevation-1" style="padding-top:3px;">
        <template v-slot:item.servers="props">
          <div v-for="item in props.item.servers" :key="item.region + '|' + item.server" style="margin-left:0px; padding-left:0px; float:left; margin-right:5px; padding-top:3px; padding-bottom:3px;">
            <v-chip outlined :color="item.color" style="margin-left:0px;"><span class="font-weight-medium" style="padding-right:4px;">{{ item.server }}</span> - {{ item.region }}</v-chip>
          </div>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="dialog" persistent max-width="896px">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">{{ dialog_title }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="dialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 20px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:15px; margin-bottom:15px;">
                  <v-text-field v-if="mode!='delete'" ref="field" @keypress.enter.native.prevent="submitEnvironment()" v-model="environment_name" :rules="[v => !!v || '']" label="Name" required></v-text-field>
                  
                  <v-card v-if="mode!='delete'">
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

                  <div style="padding-bottom:10px" v-if="mode=='delete'" class="subtitle-1">Are you sure you want to delete the selected environments?</div>
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

    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn color="white" text @click="snackbar = false">Close</v-btn>
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
    headers: [
      { text: 'Id', align: ' d-none', value: 'id' },
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Servers', align: 'left', value: 'servers' }
    ],
    items: [],
    selected: [],
    search: '',
    mode: '',
    loading: true,
    dialog: false,
    dialog_title: '',
    // Dialog items
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
  created() {
    this.getEnvironments()
  },
  methods: {
    getEnvironments() {
      axios.get('/inventory/environments')
        .then((response) => {
          this.parseTreeView(response.data.servers)
          // this.parseEnvironments(response.data.environments)
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
      if (servers.length == 0) return

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
    parseEnvironments(environments) {
      var data = []
      var regions = []
      var colors = ['#eb5f5d', '#fa8231', '#00b16a', '#9c59b6', '#2196f3']

      // Fill regions
      for (let i = 0; i < this.treeviewItems.length; ++i) regions.push(this.treeviewItems[i]['name'])
      regions.sort()
      
      // Parse Environments
      for (let i = 0; i < environments.length; ++i) {
        let row = {}
        row['id'] = environments[i]['id']
        row['name'] = environments[i]['name']
        row['servers'] = []
        if (environments[i]['id'] in this.environment_servers) {
          for (let j = 0; j < this.environment_servers[environments[i]['id']].length; ++j) {
            for (let k = 0; k < this.environment_servers[environments[i]['id']][j]['children'].length; ++k) {
              let region_name = this.environment_servers[environments[i]['id']][j]['name']
              let server_name = this.environment_servers[environments[i]['id']][j]['children'][k]['name']
              let color_next = regions.indexOf(region_name) < colors.length ? colors[regions.indexOf(region_name)] : ''
              row['servers'].push({ region: region_name, server: server_name, color: color_next })
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
              data[environment_servers[i]['environment_id']][j]['children'].push({ id: environment_servers[i]['server_id'], name: environment_servers[i]['server_name'] })
              found = true
              break
            }
          }
          if (!found) data[environment_servers[i]['environment_id']].push({ id: environment_servers[i]['region_id'], name: environment_servers[i]['region_name'], children: [{ id: environment_servers[i]['server_id'], name: environment_servers[i]['server_name'] }] })
        }
        else data[environment_servers[i]['environment_id']] = [{ id: environment_servers[i]['region_id'], name: environment_servers[i]['region_name'], children: [{ id: environment_servers[i]['server_id'], name: environment_servers[i]['server_name'] }] }]
      }
      return data
    },
    newEnvironment() {
      this.mode = 'new'
      this.environment_name = ''
      this.treeviewSelected = []
      this.dialog_title = 'New Environment'
      this.dialog = true
    },
    editEnvironment() {
      this.mode = 'edit'
      this.environment_name = this.selected[0]['name']
      this.dialog_title = 'Edit Environment'
      this.dialog = true
      setTimeout(this.updateSelected, 1);
    },
    updateSelected() {
      var treeviewSelected = []
      if (Object.keys(this.environment_servers) == 0) this.treeviewSelected = []
      else {
        for (let i = 0; i < this.environment_servers[this.selected[0]['id']].length; ++i) {
          for (let j = 0; j < this.environment_servers[this.selected[0]['id']][i]['children'].length; ++j) {
            treeviewSelected.push(this.environment_servers[this.selected[0]['id']][i]['id'] + '|' + this.environment_servers[this.selected[0]['id']][i]['children'][j]['id'])
          }
        }
        this.treeviewSelected = [...treeviewSelected]
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
      console.log(this.treeviewSelected)

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
      for (let i = 0; i < this.treeviewSelected.length; ++i) server_list.push(this.treeviewSelected[i].substring(this.treeviewSelected[i].indexOf('|')+1, this.treeviewSelected[i].length))

      // Add item in the DB
      const payload = JSON.stringify({ name: this.environment_name, servers: server_list })
      axios.post('/inventory/environments', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getEnvironments()
          this.dialog = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
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
      for (let i = 0; i < this.treeviewSelected.length; ++i) server_list.push(this.treeviewSelected[i].substring(this.treeviewSelected[i].indexOf('|')+1, this.treeviewSelected[i].length))

      // Edit item in the DB
      const payload = JSON.stringify({ id: this.selected[0]['id'], name: this.environment_name, servers: server_list })
      axios.put('/inventory/environments', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          // Edit item in the data table
          this.getEnvironments()
          this.dialog = false
          this.selected = []
          this.treeviewSelected = []
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
        })
    },
    deleteEnvironmentSubmit() {
      // Get Selected Items
      var payload = []
      for (var i = 0; i < this.selected.length; ++i) payload.push(this.selected[i]['id'])
      // Delete items to the DB
      axios.delete('/inventory/environments', { data: payload })
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getEnvironments()
          this.selected = []
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
          this.dialog = false
        })
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
        if (typeof this.$refs.field !== 'undefined') this.$refs.field.focus()
      })
    }
  }
}
</script>