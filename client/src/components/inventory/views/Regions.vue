<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">REGIONS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text @click="newRegion()" class="body-2"><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn v-if="selected.length == 1" text @click="editRegion()" class="body-2"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
          <v-btn v-if="selected.length > 0" text @click="deleteRegion()" class="body-2"><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
        </v-toolbar-items>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="id" show-select class="elevation-1" style="padding-top:3px;">
        <template v-slot:[`item.ssh_tunnel`]="{ item }">
          <v-icon v-if="item.ssh_tunnel" small color="#00b16a" style="margin-left:20px">fas fa-circle</v-icon>
          <v-icon v-else small color="error" style="margin-left:20px">fas fa-circle</v-icon>
        </template>
        <template v-slot:[`item.password`]="{ item }">
          <v-icon v-if="item.ssh_tunnel && (item.password || '').length != 0" small color="#00b16a" style="margin-left:20px">fas fa-circle</v-icon>
          <v-icon v-else-if="item.ssh_tunnel" small color="error" style="margin-left:20px">fas fa-circle</v-icon>
        </template>
        <template v-slot:[`item.key`]="{ item }">
          <v-icon v-if="item.ssh_tunnel && (item.key || '').length != 0" small color="#00b16a" style="margin-left:22px">fas fa-circle</v-icon>
          <v-icon v-else-if="item.ssh_tunnel" small color="error" style="margin-left:22px">fas fa-circle</v-icon>
        </template>
        <template v-slot:[`item.shared`]="{ item }">
          <v-icon v-if="!item.shared" small title="Personal" color="warning" style="margin-right:6px; margin-bottom:2px;">fas fa-user</v-icon>
          <v-icon v-else small title="Shared" color="error" style="margin-right:6px; margin-bottom:2px;">fas fa-users</v-icon>
          {{ !item.shared ? 'Personal' : 'Shared' }}
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="dialog" persistent max-width="768px">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">{{ dialog_title }}</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn title="Create the region only for you" :color="!item.shared ? 'primary' : '#779ecb'" @click="item.shared = false" style="margin-right:10px;"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-user</v-icon>Personal</v-btn>
          <v-btn :disabled="!owner" title="Create the region for all users in your group" :color="item.shared ? 'primary' : '#779ecb'" @click="item.shared = true"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-users</v-icon>Shared</v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 20px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" v-model="dialog_valid" v-if="mode!='delete'" style="margin-top:15px; margin-bottom:15px;">
                  <v-text-field ref="field" v-model="item.name" :rules="[v => !!v || '']" label="Name" required></v-text-field>
                  <v-switch v-model="item.ssh_tunnel" label="Use SSH Tunnel" color="info" hide-details style="margin-top:0px;"></v-switch>
                  <div v-if="item.ssh_tunnel" style="margin-top:25px;">
                    <v-row no-gutters>
                      <v-col cols="8" style="padding-right:10px">
                        <v-text-field v-model="item.hostname" :rules="[v => !!v || '']" label="Hostname" style="padding-top:0px;"></v-text-field>
                      </v-col>
                      <v-col cols="4" style="padding-left:10px">
                        <v-text-field v-model="item.port" :rules="[v => v == parseInt(v) || '']" label="Port" style="padding-top:0px;"></v-text-field>
                      </v-col>
                    </v-row>
                    <v-text-field v-model="item.username" :rules="[v => !!v || '']" label="Username" style="padding-top:0px;"></v-text-field>
                    <v-text-field v-model="item.password" label="Password" style="padding-top:0px;"></v-text-field>
                    <v-textarea v-model="item.key" label="Private Key" rows="2" filled auto-grow style="padding-top:0px;" hide-details></v-textarea>
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

    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
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
      { text: 'SSH Tunnel', align: 'left', value: 'ssh_tunnel'},
      { text: 'Hostname', align: 'left', value: 'hostname'},
      { text: 'Port', align: 'left', value: 'port'},
      { text: 'Username', align: 'left', value: 'username'},
      { text: 'Password', align: 'left', value: 'password'},
      { text: 'Private Key', align: 'left', value: 'key'},
      { text: 'Scope', align: 'left', value: 'shared' },
    ],
    items: [],
    selected: [],
    search: '',
    item: { name: '', ssh_tunnel: false, hostname: '', port: '', username: '', password: '', key: '', shared: false },
    mode: '',
    loading: true,
    dialog: false,
    dialog_title: '',
    dialog_valid: false,

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(5000),
    snackbarText: '',
    snackbarColor: ''
  }),
  computed: {
    owner: function() { return this.$store.getters['app/owner'] },
    inventory_secured: function() { return this.$store.getters['app/inventory_secured'] },
  },
  created() {
    this.getRegions()
  },
  methods: {
    getRegions() {
      axios.get('/inventory/regions')
        .then((response) => {
          this.items = response.data.data
          this.loading = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    newRegion() {
      this.mode = 'new'
      this.item = { name: '', ssh_tunnel: false, hostname: '', port: '', username: '', password: '', key: '', shared: false }
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
      // Add item in the DB
      this.notification('Adding Region...', 'info', true)
      const payload = this.item
      axios.post('/inventory/regions', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getRegions()
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
    editRegionSubmit() {
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
      // Edit item in the DB
      this.notification('Editing Region...', 'info', true)
      const payload = this.item
      axios.put('/inventory/regions', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          // Edit item in the data table
          this.items.splice(i, 1, this.item)
          this.dialog = false
          this.selected = []
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
        })
    },
    deleteRegionSubmit() {
      // Build payload
      const payload = { regions: JSON.stringify(this.selected.map((x) => x.id)) }
      // Delete items to the DB
      this.notification('Deleting Region...', 'info', true)
      axios.delete('/inventory/regions', { params: payload })
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
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
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
      const payload = this.item
      axios.post('/inventory/regions/test', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
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