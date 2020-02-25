<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title class="white--text">REGIONS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text @click="newRegion()"><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn v-if="selected.length == 1" text @click="editRegion()"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
          <v-btn v-if="selected.length > 0" text @click="deleteRegion()"><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
        </v-toolbar-items>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" style="margin-left:10px;" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="id" show-select class="elevation-1" style="padding-top:3px;">
        <template v-slot:item.ssh_tunnel="props">
          <v-icon v-if="props.item.ssh_tunnel" small color="#00b16a" style="margin-left:20px">fas fa-circle</v-icon>
          <v-icon v-else small color="error" style="margin-left:20px">fas fa-circle</v-icon>
        </template>
        <template v-slot:item.password="props">
          <v-icon v-if="props.item.ssh_tunnel && (props.item.password || '').length != 0" small color="#00b16a" style="margin-left:20px">fas fa-circle</v-icon>
          <v-icon v-else-if="props.item.ssh_tunnel" small color="error" style="margin-left:20px">fas fa-circle</v-icon>
        </template>
        <template v-slot:item.key="props">
          <v-icon v-if="props.item.ssh_tunnel && (props.item.key || '').length != 0" small color="#00b16a" style="margin-left:22px">fas fa-circle</v-icon>
          <v-icon v-else-if="props.item.ssh_tunnel" small color="error" style="margin-left:22px">fas fa-circle</v-icon>
        </template>
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
                  <v-select v-model="item.environment" :rules="[v => !!v || '']" :items="environments" label="Environment" required style="margin-top:0px; padding-top:0px;"></v-select>
                  <!-- SSH -->
                  <v-switch v-model="item.ssh_tunnel" label="SSH Tunnel" color="info" hide-details style="margin-top:0px;"></v-switch>
                  <div v-if="item.ssh_tunnel" style="margin-top:15px;">
                    <div class="title font-weight-regular">SSH</div>
                    <v-text-field v-model="item.hostname" :rules="[v => !!v || '']" label="Hostname" append-icon="cloud"></v-text-field>
                    <v-text-field v-model="item.port" :rules="[v => !!v && !isNaN(parseFloat(v)) && isFinite(v) || '']" label="Port" style="padding-top:0px;" append-icon="directions_boat"></v-text-field>
                    <v-text-field v-model="item.username" :rules="[v => !!v || '']" label="Username" style="padding-top:0px;" append-icon="person"></v-text-field>
                    <v-text-field v-model="item.password" label="Password" style="padding-top:0px;" append-icon="lock"></v-text-field>
                    <v-textarea v-model="item.key" label="Private Key" rows="2" filled auto-grow style="padding-top:0px;" append-icon="vpn_key" hide-details></v-textarea>
                  </div>
                </v-form>
                <div style="padding-top:10px; padding-bottom:10px" v-if="mode=='delete'" class="subtitle-1">Are you sure you want to delete the selected regions?</div>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :loading="loading" color="#00b16a" @click="submitRegion()">CONFIRM</v-btn>
                  <v-btn :disabled="loading" color="error" @click="dialog=false" style="margin-left:5px">CANCEL</v-btn>
                  <v-btn v-if="item['ssh_tunnel'] && mode != 'delete'" :loading="loading" color="info" @click="testConnection()" style="float:right;">Test Connection</v-btn>
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
    // Data Table
    headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Environment', align: 'left', value: 'environment' },
      { text: 'SSH Tunnel', align: 'left', value: 'ssh_tunnel'},
      { text: 'Hostname', align: 'left', value: 'hostname'},
      { text: 'Port', align: 'left', value: 'port'},
      { text: 'Username', align: 'left', value: 'username'},
      { text: 'Password', align: 'left', value: 'password'},
      { text: 'Private Key', align: 'left', value: 'key'}
    ],
    items: [],
    selected: [],
    search: '',
    item: { name: '', environment: '', ssh_tunnel: false, hostname: '', port: '', username: '', password: '', key: '' },
    mode: '',
    loading: true,
    dialog: false,
    dialog_title: '',
    dialog_valid: false,
    // Environments
    environments: [],
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(5000),
    snackbarText: '',
    snackbarColor: ''
  }),
  created() {
    this.getRegions()
  },
  methods: {
    getRegions() {
      axios.get('/deployments/regions')
        .then((response) => {
          this.items = response.data.data.regions
          for (var i = 0; i < response.data.data.environments.length; ++i) this.environments.push(response.data.data.environments[i]['name'])
          this.loading = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    newRegion() {
      this.mode = 'new'
      this.item = { name: '', environment: '', ssh_tunnel: false, hostname: '', port: '', username: '', password: '', key: '' }
      this.dialog_title = 'New Region'
      this.dialog = true
    },
    editRegion() {
      this.mode = 'edit'
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.dialog_title = 'Edit Region'
      this.dialog = true
    },
    deleteRegion() {
      this.mode = 'delete'
      this.dialog_title = 'Delete Region'
      this.dialog = true
    },
    submitRegion() {
      this.loading = true
      if (this.mode == 'new') this.newRegionSubmit()
      else if (this.mode == 'edit') this.editRegionSubmit()
      else if (this.mode == 'delete') this.deleteRegionSubmit()
    },
    newRegionSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      // Check if new item already exists
      for (var i = 0; i < this.items.length; ++i) {
        if (this.items[i]['environment'] == this.item.environment && this.items[i]['name'] == this.item.name) {
          this.notification('This region currently exists', 'error')
          this.loading = false
          return
        }
      }
      // Add item in the DB
      this.notification('Adding Region...', 'info', true)
      const payload = JSON.stringify(this.item);
      axios.post('/deployments/regions', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getRegions()
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
    editRegionSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      // Get Item Position
      for (var i = 0; i < this.items.length; ++i) {
        if (this.items[i]['environment'] == this.selected[0]['environment'] && this.items[i]['name'] == this.selected[0]['name']) break
      }
      // Check if edited item already exists
      for (var j = 0; j < this.items.length; ++j) {
        if (this.items[j]['environment'] == this.item.environment && this.items[j]['name'] == this.item.name && this.item.name != this.selected[0]['name']) {
          this.notification('This region currently exists', 'error')
          this.loading = false
          return
        }
      }
      // Edit item in the DB
      this.notification('Editing Region...', 'info', true)
      const payload = JSON.stringify(this.item)
      axios.put('/deployments/regions', payload)
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
    deleteRegionSubmit() {
      // Get Selected Items
      var payload = []
      for (var i = 0; i < this.selected.length; ++i) payload.push(this.selected[i]['id'])
      // Delete items to the DB
      this.notification('Deleting Region...', 'info', true)
      axios.delete('/deployments/regions', { data: payload })
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
      this.notification('Testing Region...', 'info', true)
      this.loading = true
      const payload = JSON.stringify(this.item)
      axios.post('/deployments/regions/test', payload)
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