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
        <v-card-text style="padding: 0px 20px 20px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" v-model="dialog_valid" v-if="mode!='delete'" style="margin-top:15px; margin-bottom:20px;">
                  <!-- METADATA -->
                  <div class="title font-weight-regular">Metadata</div>
                  <v-text-field ref="field" v-model="item.name" :rules="[v => !!v || '']" label="Name" required></v-text-field>
                  <v-select v-model="item.environment" :rules="[v => !!v || '']" :items="environments" label="Environment" v-on:change="getRegions()" required style="margin-top:0px; padding-top:0px;"></v-select>
                  <v-select v-model="item.region" :disabled="item.environment == ''" :rules="[v => !!v || '']" :items="regions" label="Region" required style="margin-top:0px; padding-top:0px;"></v-select>
                  <!-- SQL -->
                  <div class="title font-weight-regular">SQL</div>
                  <v-select v-model="item.engine" :items="engines_items" label="Engine" :rules="[v => !!v || '']" required v-on:change="selectEngine"></v-select>
                  <v-text-field v-model="item.hostname" :rules="[v => !!v || '']" label="Hostname" required style="padding-top:0px;" append-icon="cloud"></v-text-field>
                  <v-text-field v-model="item.port" :rules="[v => !v && v == parseInt(v) || '']" label="Port" required style="padding-top:0px;" append-icon="directions_boat"></v-text-field>
                  <v-text-field v-model="item.username" :rules="[v => !!v || '']" label="Username" required style="padding-top:0px;" append-icon="person"></v-text-field>
                  <v-text-field v-model="item.password" label="Password" style="padding-top:0px;" hide-details append-icon="lock"></v-text-field>
                </v-form>
                <div style="padding-top:10px; padding-bottom:10px" v-if="mode=='delete'" class="subtitle-1">Are you sure you want to delete the selected servers?</div>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :loading="loading" color="#00b16a" @click="submitServer()">CONFIRM</v-btn>
                  <v-btn :disabled="loading" color="error" @click="dialog=false" style="margin-left:5px">CANCEL</v-btn>
                  <v-btn v-if="mode != 'delete'" :loading="loading" color="info" @click="testConnection()" style="float:right;">Test Connection</v-btn>
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
import axios from 'axios';

export default {
  data: () => ({
    headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Environment', align: 'left', value: 'environment'},
      { text: 'Region', align: 'left', value: 'region'},
      { text: 'Engine', align: 'left', value: 'engine' },
      { text: 'Hostname', align: 'left', value: 'hostname'},
      { text: 'Port', align: 'left', value: 'port'},
      { text: 'Username', align: 'left', value: 'username'},
      { text: 'Password', align: 'left', value: 'password'}
    ],
    items: [],
    selected: [],
    search: '',
    item: { name: '', environment: '', region: '', engine: '', hostname: '', port: '', username: '', password: '' },
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
      axios.get('/deployments/servers')
        .then((response) => {
          this.items = response.data.data.servers
          for (var i = 0; i < response.data.data.environments.length; ++i) this.environments.push(response.data.data.environments[i]['name'])
          this.loading = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    getRegions() {
      this.regions = []
      const payload = {"name": this.item.environment}
      axios.post('/deployments/regions/list', payload)
        .then((response) => {
          for (var i = 0; i < response.data.data.length; ++i) this.regions.push(response.data.data[i]['name'])
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    selectEngine(value) {
      if (this.item['port'] == '') {
        if (value == 'MySQL') this.item['port'] = '3306'
        else if (value == 'PostgreSQL') this.item['port'] = '5432'
      }
    },
    newServer() {
      this.mode = 'new'
      this.item = { name: '', environment: '', region: '', engine: '', hostname: '', port: '', username: '', password: '' }
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
      const payload = JSON.stringify(this.item);
      axios.post('/deployments/servers', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getServers()
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
      const payload = JSON.stringify(this.item)
      axios.put('/deployments/servers', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          // Edit item in the data table
          this.items.splice(i, 1, this.item)
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
    deleteServerSubmit() {
      // Get Selected Items
      var payload = []
      for (var i = 0; i < this.selected.length; ++i) payload.push(this.selected[i]['id'])
      // Delete items to the DB
      axios.delete('/deployments/servers', { data: payload })
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
    testConnection() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      // Test Connection
      this.notification('Testing Server...', 'info', true)
      this.loading = true
      const payload = JSON.stringify(this.item)
      axios.post('/deployments/servers/test', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
        })
    },
    notification(message, color, persistent=false) {
      this.snackbar = false
      setTimeout(() => {
        this.snackbarText = message
        this.snackbarColor = color
        this.snackbarTimeout = persistent ? Number(0) : Number(5000)
        this.snackbar = true
      }, 10)
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