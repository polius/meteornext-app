<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title class="white--text">SERVERS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text @click="newServer()"><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn v-if="selected.length == 1" text @click="editServer()"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
          <v-btn v-if="selected.length > 0" text @click="deleteServer()"><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
        </v-toolbar-items>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" style="margin-left:10px;" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="id" show-select class="elevation-1" style="padding-top:3px;">
      </v-data-table>
    </v-card>

    <v-dialog v-model="dialog" persistent max-width="768px">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">{{ dialog_title }}</v-toolbar-title>
        </v-toolbar>
        <v-card-text>
          <v-container style="padding:0px 10px 0px 10px">
            <v-layout wrap>
              <v-flex xs12 v-if="mode!='delete'">
                <v-form ref="form" v-model="dialog_valid">
                  <!-- METADATA -->
                  <div class="title font-weight-regular">Metadata</div>
                  <v-text-field ref="field" v-model="item.name" :rules="[v => !!v || '']" label="Name" required></v-text-field>
                  <v-select v-model="item.environment" :rules="[v => !!v || '']" :items="environments" label="Environment" v-on:change="getRegions()" required style="margin-top:0px; padding-top:0px;"></v-select>
                  <v-select v-model="item.region" :disabled="item.environment == ''" :rules="[v => !!v || '']" :items="regions" label="Region" required style="margin-top:0px; padding-top:0px;"></v-select>
                  <!-- SQL -->
                  <div class="title font-weight-regular">SQL</div>
                  <v-select v-model="item.engine" :items="engines_items" label="Engine" :rules="[v => !!v || '']" required></v-select>
                  <v-text-field v-model="item.hostname" :rules="[v => !!v || '']" label="Hostname" required style="padding-top:0px;"></v-text-field>
                  <v-text-field v-model="item.username" :rules="[v => !!v || '']" label="Username" required style="padding-top:0px;"></v-text-field>
                  <v-text-field v-model="item.password" :rules="[v => !!v || '']" label="Password" required style="padding-top:0px;"></v-text-field>
                </v-form>
              </v-flex>
              <v-flex xs12 style="padding-bottom:10px" v-if="mode=='delete'">
                <div class="subtitle-1">Are you sure you want to delete the selected servers?</div>
              </v-flex>
              <v-btn :loading="loading" color="success" @click="submitServer()">Confirm</v-btn>
              <v-btn :disabled="loading" color="error" @click="dialog=false" style="margin-left:10px">Cancel</v-btn>
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
import axios from 'axios';

export default {
  data: () => ({
    headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Environment', align: 'left', value: 'environment'},
      { text: 'Region', align: 'left', value: 'region'},
      { text: 'Engine', align: 'left', value: 'engine' },
      { text: 'Hostname', align: 'left', value: 'hostname'},
      { text: 'Username', align: 'left', value: 'username'},
      { text: 'Password', align: 'left', value: 'password'}
    ],
    items: [],
    selected: [],
    search: '',
    item: { name: '', environment: '', region: '', engine: '', hostname: '', username: '', password: '' },
    mode: '',
    loading: true,
    engines_items: ['MySQL', 'PostgreSQL'],
    // Dialog: Item
    dialog: false,
    dialog_title: '',
    dialog_valid: false,
    // Environments & Regions
    environments: [],
    regions: [],
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  created() {
    this.getServers()
  },
  methods: {
    getServers() {
      const path = this.$store.getters.url + '/deployments/servers'
      axios.get(path)
        .then((response) => {
          this.items = response.data.data.servers
          for (var i = 0; i < response.data.data.environments.length; ++i) this.environments.push(response.data.data.environments[i]['name'])
          this.loading = false
        })
        .catch((error) => {
          if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
          // eslint-disable-next-line
          console.error(error)
        })
    },
    getRegions() {
      this.regions = []
      const path = this.$store.getters.url + '/deployments/regions/list'
      const payload = {"name": this.item.environment}
      axios.post(path, payload)
        .then((response) => {
          for (var i = 0; i < response.data.data.length; ++i) this.regions.push(response.data.data[i]['name'])
        })
        .catch((error) => {
          if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          this.notification(error.response.data.message, 'error')
          // eslint-disable-next-line
          console.error(error)
        })
    },
    newServer() {
      this.mode = 'new'
      this.item = { name: '', environment: '', region: '', engine: '', hostname: '', username: '', password: '' }
      this.dialog_title = 'New Server'
      this.dialog = true
    },
    editServer() {
      this.mode = 'edit'
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.getRegions()
      this.dialog_title = 'Edit Server'
      this.dialog = true
    },
    deleteServer() {
      this.mode = 'delete'
      this.dialog_title = 'Delete Server'
      this.dialog = true
    },
    submitServer() {
      this.loading = true
      if (this.mode == 'new') this.newServerSubmit()
      else if (this.mode == 'edit') this.editServerSubmit()
      else if (this.mode == 'delete') this.deleteServerSubmit()
    },
    newServerSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      // Check if new item already exists
      for (var i = 0; i < this.items.length; ++i) {
        if (this.items[i]['environment'] == this.item.environment && this.items[i]['region'] == this.item.region && this.items[i]['name'] == this.item.name) {
          this.notification('This server currently exists', 'error')
          this.loading = false
          return
        }
      }
      // Add item in the DB
      const path = this.$store.getters.url + '/deployments/servers'
      const payload = JSON.stringify(this.item);
      axios.post(path, payload)
        .then((response) => {
          this.notification(response.data.message, 'success')
          this.getServers()
          // Add item in the data table
          // this.items.push(this.item)
          this.dialog = false
        })
        .catch((error) => {
          if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          this.notification(error.response.data.message, 'error')
          // eslint-disable-next-line
          console.error(error)
        })
        .finally(() => {
          this.loading = false
        })
    },
    editServerSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      // Get Item Position
      for (var i = 0; i < this.items.length; ++i) {
        if (this.items[i]['environment'] == this.selected[0]['environment'] && this.items[i]['region'] == this.selected[0]['region'] && this.items[i]['name'] == this.selected[0]['name']) break
      }
      // Check if edited item already exists
      for (var j = 0; j < this.items.length; ++j) {
        if (this.items[j]['environment'] == this.item.environment && this.items[j]['region'] == this.item.region && this.items[j]['name'] == this.item.name && this.item.name != this.selected[0]['name']) {
          this.notification('This server currently exists', 'error')
          this.loading = false
          return
        }
      }
      // Edit item in the DB
      const path = this.$store.getters.url + '/deployments/servers'
      const payload = JSON.stringify(this.item)
      axios.put(path, payload)
        .then((response) => {
          this.notification(response.data.message, 'success')
          // Edit item in the data table
          this.items.splice(i, 1, this.item)
          this.dialog = false
        })
        .catch((error) => {
          if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
          // eslint-disable-next-line
          console.error(error)
        })
        .finally(() => {
          this.loading = false
          this.selected = []
        })
    },
    deleteServerSubmit() {
      // Get Selected Items
      var payload = []
      for (var i = 0; i < this.selected.length; ++i) payload.push(this.selected[i])
      // Delete items to the DB
      const path = this.$store.getters.url + '/deployments/servers'
      axios.delete(path, { data: payload })
        .then((response) => {
          this.notification(response.data.message, 'success')
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
          if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
          // eslint-disable-next-line
          console.error(error)
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