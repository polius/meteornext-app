<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title class="white--text">ENVIRONMENTS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text @click="newEnvironment()"><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn v-if="selected.length == 1" text @click="editEnvironment()"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
          <v-btn v-if="selected.length > 0" text @click="deleteEnvironment()"><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
        </v-toolbar-items>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" style="margin-left:10px;" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="name" show-select class="elevation-1" style="padding-top:3px;">
      </v-data-table>
    </v-card>

    <v-dialog v-model="dialog" persistent max-width="896px">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">{{ dialog_title }}</v-toolbar-title>
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
                      <v-treeview loading :active.sync="treeviewSelected" :open-all="mode=='edit'" selection-type="independent" :items="treeviewItems" :search="treeviewSearch" hoverable open-on-click multiple-active return-object activatable transition>
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

<script>
import axios from 'axios'

export default {
  data: () => ({
    // Data Table
    headers: [
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
    treeviewItems: [],
    treeviewSelected: [],
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
          this.items = response.data.environments
          this.treeviewItems = this.parseTreeView(response.data.servers)
          this.loading = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    getEnvironment() {
      axios.get('/inventory/environments', { params: { environment_id: this.selected[0]['id'] } })
        .then((response) => {
          this.treeviewSelected = this.parseTreeView(response.data.servers)
          this.loading = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    parseTreeView(servers) {
      var treeview = []
      var regions = []
      // Fill regions
      for (let i = 0; i < servers.length; ++i) {
        if (!regions.includes(servers[i]['region_name'])) regions.push({ id: servers[i]['region_id'], name: servers[i]['region_name'] })
      }
      // Fill treeview
      for (let i = 0; i < regions.length; ++i) {
        let region = { id: regions[i]['id'], name: regions[i]['name'], children: []}
        for (let j = 0; j < servers.length; ++j) {
          if (regions[i]['name'] == servers[j]['region_name']) {
            region['children'].push({ id: servers[j]['server_id'], name: servers[j]['server_name'] })
          }
        }
        if (region['children'].length == 0) delete region['children']
        treeview.push(region)
      }
      return treeview
    },
    newEnvironment() {
      this.mode = 'new'
      this.environment_name = ''
      this.dialog_title = 'New Environment'
      this.dialog = true
    },
    editEnvironment() {
      this.getEnvironment()
      this.mode = 'edit'
      this.environment_name = this.selected[0]['name']
      this.dialog_title = 'Edit Environment'
      this.dialog = true
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
      // Add item in the DB
      const payload = JSON.stringify({ name: this.environment_name, servers: this.treeviewSelected })
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
      // Edit item in the DB
      const payload = JSON.stringify({ name: this.environment_name, servers: this.treeviewSelected })
      axios.put('/inventory/environments', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          // Edit item in the data table
          this.items.splice(i, 1, {'name': this.environment_name })
          this.dialog = false
          this.selected = []
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
          // Delete items from the data table
          while(this.selected.length > 0) {
            var s = this.selected.pop()
            for (var i = 0; i < this.items.length; ++i) {
              if (this.items[i]['name'] == s['name']) {
                // Delete Item
                this.items.splice(i, 1)
                break
              }
            }
          }
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