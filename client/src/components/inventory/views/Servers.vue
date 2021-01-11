<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">SERVERS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text @click="newServer()" class="body-2"><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn v-if="selected.length == 1 && !(inventory_secured && selected[0].shared && !owner)" @click="cloneServer()" text class="body-2"><v-icon small style="padding-right:10px">fas fa-clone</v-icon>CLONE</v-btn>
          <v-btn v-if="selected.length == 1" text @click="editServer()" class="body-2"><v-icon small style="padding-right:10px">{{ !owner && selected[0].shared ? 'fas fa-info' : 'fas fa-feather-alt' }}</v-icon>{{ !owner && selected[0].shared ? 'INFO' : 'EDIT' }}</v-btn>
          <v-btn v-if="selected.length > 0 && !(!owner && selected.some(x => x.shared))" text @click="deleteServer()" class="body-2"><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn text class="body-2" @click="filterBy('all')" :style="filter == 'all' ? 'font-weight:600' : 'font-weight:400'">ALL</v-btn>
          <v-btn text class="body-2" @click="filterBy('personal')" :style="filter == 'personal' ? 'font-weight:600' : 'font-weight:400'">PERSONAL</v-btn>
          <v-btn text class="body-2" @click="filterBy('shared')" :style="filter == 'shared' ? 'font-weight:600' : 'font-weight:400'">SHARED</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
        </v-toolbar-items>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="id" show-select class="elevation-1" style="padding-top:3px;">
        <template v-slot:[`item.region`]="{ item }">
          <v-icon small :title="item.region_shared ? 'Shared' : 'Personal'" :color="item.region_shared ? 'error' : 'warning'" style="margin-right:10px">{{ item.region_shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
          {{ item.region }}
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
          <v-divider v-if="mode != 'delete'" class="mx-3" inset vertical></v-divider>
          <v-btn v-if="mode != 'delete' && !(!owner && item.shared)" title="Create the server only for you" :color="!item.shared ? 'primary' : '#779ecb'" @click="item.shared = false" style="margin-right:10px;"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-user</v-icon>Personal</v-btn>
          <v-btn v-if="mode != 'delete'" :disabled="!item.shared && !owner" title="Create the server for all users in your group" :color="item.shared ? 'primary' : '#779ecb'" @click="item.shared = true"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-users</v-icon>Shared</v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="dialog = false" icon><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 20px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" v-model="dialog_valid" v-if="mode!='delete'" style="margin-top:20px;">
                  <v-row no-gutters style="margin-top:15px">
                    <v-col cols="8" style="padding-right:10px">
                      <v-text-field ref="field" v-model="item.name" :readonly="readOnly" :rules="[v => !!v || '']" label="Name" required style="padding-top:0px;"></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-left:10px">
                      <v-select v-model="item.region" item-value="name" :readonly="readOnly" :rules="[v => !!v || '']" :items="regions" label="Region" required style="padding-top:0px;">
                        <template v-slot:[`selection`]="{ item }">
                          <v-icon small style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          {{ item.name }}
                        </template>
                        <template v-slot:[`item`]="{ item }">
                          <v-icon small style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          {{ item.name }}
                        </template>
                      </v-select>
                    </v-col>
                  </v-row>
                  <v-row no-gutters>
                    <v-col cols="8" style="padding-right:10px">
                      <v-select v-model="item.engine" :readonly="readOnly" :items="Object.keys(engines)" label="Engine" :rules="[v => !!v || '']" required style="padding-top:0px;" v-on:change="selectEngine"></v-select>
                    </v-col>
                    <v-col cols="4" style="padding-left:10px">
                      <v-select v-model="item.version" :readonly="readOnly" :items="versions" label="Version" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-select>
                    </v-col>
                  </v-row>
                  <div v-if="!(readOnly && inventory_secured)" style="margin-bottom:20px">
                    <v-row no-gutters>
                      <v-col cols="8" style="padding-right:10px">
                        <v-text-field v-model="item.hostname" :readonly="readOnly" :rules="[v => !!v || '']" label="Hostname" required style="padding-top:0px;"></v-text-field>
                      </v-col>
                      <v-col cols="4" style="padding-left:10px">
                        <v-text-field v-model="item.port" :readonly="readOnly" :rules="[v => v == parseInt(v) || '']" label="Port" required style="padding-top:0px;"></v-text-field>
                      </v-col>
                    </v-row>
                    <v-text-field v-model="item.username" :readonly="readOnly" :rules="[v => !!v || '']" label="Username" required style="padding-top:0px;"></v-text-field>
                    <v-text-field v-model="item.password" :readonly="readOnly" label="Password" style="padding-top:0px;" hide-details></v-text-field>
                    <v-switch v-model="item.ssl" :readonly="readOnly" flat label="Use SSL" style="margin-top:20px" hide-details></v-switch>
                    <v-row no-gutters v-if="item.ssl" style="margin-top:20px; margin-bottom:20px;">
                      <v-col style="padding-right:10px;">
                        <v-file-input v-model="item.ssl_client_key" :readonly="readOnly" filled dense label="Client Key" prepend-icon="" hide-details></v-file-input>
                      </v-col>
                      <v-col style="padding-right:5px; padding-left:5px;">
                        <v-file-input v-model="item.ssl_client_certificate" :readonly="readOnly" filled dense label="Client Certificate" prepend-icon="" hide-details></v-file-input>
                      </v-col>
                      <v-col style="padding-left:10px;">
                        <v-file-input v-model="item.ssl_client_ca_certificate" :readonly="readOnly" filled dense label="CA Certificate" prepend-icon="" hide-details></v-file-input>
                      </v-col>
                    </v-row>
                    <!-- <v-switch v-model="item.client_disabled" label="Disable in Client" color="error" style="margin-top:10px;" hide-details></v-switch> -->
                  </div>
                </v-form>
                <div v-if="mode=='delete'" class="subtitle-1" style="padding-top:10px; padding-bottom:10px">Are you sure you want to delete the selected servers?</div>
                <v-divider></v-divider>
                <v-row no-gutters style="margin-top:20px;">
                  <v-col cols="auto" class="mr-auto">
                    <div v-if="readOnly">
                      <v-btn color="#00b16a" @click="dialog = false">CLOSE</v-btn>
                    </div>
                    <div v-else>
                      <v-btn :loading="loading" color="#00b16a" @click="submitServer()">CONFIRM</v-btn>
                      <v-btn :disabled="loading" color="error" @click="dialog = false" style="margin-left:5px">CANCEL</v-btn>
                    </div>
                  </v-col>
                  <v-col cols="auto">
                    <v-btn v-if="mode != 'delete'" :loading="loading" color="info" @click="testConnection()">Test Connection</v-btn>
                  </v-col>
                </v-row>
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
    filter: 'all',
    headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Region', align: 'left', value: 'region'},
      { text: 'Engine', align: 'left', value: 'version' },
      { text: 'Hostname', align: 'left', value: 'hostname'},
      { text: 'Port', align: 'left', value: 'port'},
      { text: 'Username', align: 'left', value: 'username'},
      { text: 'Scope', align: 'left', value: 'shared' },
    ],
    servers: [],
    items: [],
    selected: [],
    search: '',
    item: { name: '', region: '', engine: '', version: '', hostname: '', port: '', username: '', password: '', ssl: false, client_disabled: false, shared: false },
    mode: '',
    loading: true,
    engines: {
      'MySQL': ['MySQL 5.6', 'MySQL 5.7', 'MySQL 8.x'],
      'Aurora MySQL': ['Aurora MySQL 5.6', 'Aurora MySQL 5.7']
    },
    versions: [],
    // Dialog: Item
    dialog: false,
    dialog_title: '',
    dialog_valid: false,
    // Regions
    regions: [],
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  computed: {
    owner: function() { return this.$store.getters['app/owner'] == 1 ? true : false },
    inventory_secured: function() { return this.$store.getters['app/inventory_secured'] },
    readOnly: function() { return this.mode == 'edit' && !this.owner && this.item.shared == 1 }
  },
  created() {
    this.getServers()
    this.getRegions()
  },
  methods: {
    getServers() {
      axios.get('/inventory/servers')
        .then((response) => {
          this.servers = response.data.data
          this.items = response.data.data
          this.filterBy(this.filter)
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
    },
    getRegions() {
      axios.get('/inventory/regions')
        .then((response) => {
          this.regions = response.data.data.map(x => ({ id: x.id, name: x.name, shared: x.shared }))
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
    },
    selectEngine(value) {
      if (this.item.port == '') {
        if (['MySQL','Aurora MySQL'].includes(value)) this.item.port = '3306'
        else if (value == 'PostgreSQL') this.item.port = '5432'
      }
      this.versions = this.engines[value]
    },
    newServer() {
      this.mode = 'new'
      this.item = { name: '', region: '', engine: '', version: '', hostname: '', port: '', username: '', password: '', ssl: false, client_disabled: false, shared: false }
      this.dialog_title = 'New Server'
      this.dialog = true
    },
    cloneServer() {
      this.mode = 'clone'
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      delete this.item['id']
      this.versions = this.engines[this.item.engine]
      this.dialog_title = 'Clone Server'
      this.dialog = true
    },
    editServer() {
      this.mode = 'edit'
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.versions = this.engines[this.item.engine]
      this.dialog_title = (!this.owner && this.item.shared) ? 'INFO' : 'Edit Server'
      this.dialog = true
    },
    deleteServer() {
      this.mode = 'delete'
      this.dialog_title = 'Delete Server'
      this.dialog = true
    },
    submitServer() {
      this.loading = true
      if (['new','clone'].includes(this.mode)) this.newServerSubmit()
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
      // Add item in the DB
      const payload = this.item
      axios.post('/inventory/servers', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getServers()
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
    },
    editServerSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      // Edit item in the DB
      const payload = this.item
      axios.put('/inventory/servers', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getServers()
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
    },
    deleteServerSubmit() {
      // Build payload
      const payload = { servers: JSON.stringify(this.selected.map((x) => x.id)) }
      // Delete items to the DB
      axios.delete('/inventory/servers', { params: payload })
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getServers()
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
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
      const payload = {
        region: (this.readOnly && this.inventory_secured) ? this.item.region_id : this.regions.find(x => x.name == this.item.region).id,
        server: (this.readOnly && this.inventory_secured) ? this.item.id : { hostname: this.item.hostname, port: this.item.port, username: this.item.username, password: this.item.password }
      }
      axios.post('/inventory/servers/test', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a', 2)
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
    },
    filterBy(val) {
      this.filter = val
      if (val == 'all') this.items = this.servers.slice(0)
      else if (val == 'personal') this.items = this.servers.filter(x => !x.shared)
      else if (val == 'shared') this.items = this.servers.filter(x => x.shared)
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