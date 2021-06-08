<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">REGIONS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text @click="newRegion()"><v-icon small style="margin-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn v-if="selected.length == 1 && !(inventory_secured && selected[0].shared && !owner)" @click="cloneRegion()" text><v-icon small style="margin-right:10px">fas fa-clone</v-icon>CLONE</v-btn>
          <v-btn v-if="selected.length == 1" text @click="editRegion()"><v-icon small style="margin-right:10px">{{ !owner && selected[0].shared ? 'fas fa-info' : 'fas fa-feather-alt' }}</v-icon>{{ !owner && selected[0].shared ? 'INFO' : 'EDIT' }}</v-btn>
          <v-btn v-if="selected.length > 0 && !(!owner && selected.some(x => x.shared))" text @click="deleteRegion()"><v-icon small style="margin-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn text class="body-2" @click="filterBy('all')" :style="filter == 'all' ? 'font-weight:600' : 'font-weight:400'">ALL</v-btn>
          <v-btn text class="body-2" @click="filterBy('personal')" :style="filter == 'personal' ? 'font-weight:600' : 'font-weight:400'">PERSONAL</v-btn>
          <v-btn text class="body-2" @click="filterBy('shared')" :style="filter == 'shared' ? 'font-weight:600' : 'font-weight:400'">SHARED</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
        </v-toolbar-items>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="id" show-select class="elevation-1" style="padding-top:3px;">
        <template v-ripple v-slot:[`header.data-table-select`]="{}">
          <v-simple-checkbox
            :value="items.length == 0 ? false : selected.length == items.length"
            :indeterminate="selected.length > 0 && selected.length != items.length"
            @click="selected.length == items.length ? selected = [] : selected = JSON.parse(JSON.stringify(items))">
          </v-simple-checkbox>
        </template>
        <template v-slot:[`item.ssh_tunnel`]="{ item }">
          <v-icon v-if="item.ssh_tunnel" small color="#00b16a" style="margin-left:20px">fas fa-circle</v-icon>
          <v-icon v-else small color="#EF5354" style="margin-left:20px">fas fa-circle</v-icon>
        </template>
        <template v-slot:[`item.shared`]="{ item }">
          <v-icon v-if="!item.shared" small title="Personal" color="warning" style="margin-right:6px; margin-bottom:2px;">fas fa-user</v-icon>
          <v-icon v-else small title="Shared" color="#EB5F5D" style="margin-right:6px; margin-bottom:2px;">fas fa-users</v-icon>
          {{ !item.shared ? 'Personal' : 'Shared' }}
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="dialog" persistent max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1">{{ dialog_title }}</v-toolbar-title>
          <v-divider v-if="mode != 'delete'" class="mx-3" inset vertical></v-divider>
          <v-btn v-if="mode != 'delete'" :readonly="readOnly" title="Create the region only for you" :color="!item.shared ? 'primary' : '#779ecb'" @click="!readOnly ? item.shared = false : ''" style="margin-right:10px;"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-user</v-icon>Personal</v-btn>
          <v-btn v-if="mode != 'delete'" :disabled="!owner && !readOnly" :readonly="readOnly" title="Create the region for all users in your group" :color="item.shared ? 'primary' : '#779ecb'" @click="!readOnly ? item.shared = true : ''"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-users</v-icon>Shared</v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="dialog = false" icon><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 15px 15px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" v-model="dialog_valid" v-if="mode!='delete'" style="margin-top:15px; margin-bottom:15px;">
                  <v-text-field ref="field" v-model="item.name" :rules="[v => !!v || '']" :readonly="readOnly" label="Name" required hide-details></v-text-field>
                  <v-switch v-model="item.ssh_tunnel" :readonly="readOnly" label="SSH Tunnel" color="info" hide-details style="margin-top:15px;"></v-switch>
                  <div v-if="item.ssh_tunnel && !(readOnly && inventory_secured)" style="margin-top:20px">
                    <v-row no-gutters>
                      <v-col cols="9" style="padding-right:10px">
                        <v-text-field v-model="item.hostname" :readonly="readOnly" :rules="[v => !!v || '']" label="Hostname" style="padding-top:0px;"></v-text-field>
                      </v-col>
                      <v-col cols="3" style="padding-left:10px">
                        <v-text-field v-model="item.port" :readonly="readOnly" :rules="[v => v == parseInt(v) || '']" label="Port" style="padding-top:0px;"></v-text-field>
                      </v-col>
                    </v-row>
                    <v-text-field v-model="item.username" :readonly="readOnly" :rules="[v => !!v || '']" label="Username" autocomplete="username"  style="padding-top:0px;"></v-text-field>
                    <v-text-field v-model="item.password" :readonly="readOnly" label="Password" :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'" :type="showPassword ? 'text' : 'password'" @click:append="showPassword = !showPassword" autocomplete="new-password" style="padding-top:0px;"></v-text-field>
                    <v-file-input v-if="item.key == null || typeof item.key === 'object'" v-model="item.key" filled label="Private Key" prepend-icon="" hide-details style="padding-top:0px"></v-file-input>
                    <v-card v-else style="height:52px">
                      <v-row no-gutters>
                        <v-col cols="auto" style="display:flex; margin:15px">
                          <v-icon color="#00b16a" style="font-size:20px">fas fa-key</v-icon>
                        </v-col>
                        <v-col>
                          <div class="text-body-1" style="color:#00b16a; margin-top:15px">Using a Private Key</div>
                        </v-col>
                        <v-col cols="auto" class="text-right">
                          <v-btn @click="item.key = null" icon title="Remove Private Key" style="margin:8px"><v-icon style="font-size:18px">fas fa-times</v-icon></v-btn>
                        </v-col>
                      </v-row>
                    </v-card>
                  </div>
                </v-form>
                <div style="padding-top:10px; padding-bottom:10px" v-if="mode=='delete'" class="subtitle-1">Are you sure you want to delete the selected regions?</div>
                <v-divider></v-divider>
                <v-row no-gutters style="margin-top:20px;">
                  <v-col cols="auto" class="mr-auto">
                    <div v-if="readOnly">
                      <v-btn color="#00b16a" @click="dialog = false">CLOSE</v-btn>
                    </div>
                    <div v-else>
                      <v-btn :loading="loading" color="#00b16a" @click="submitRegion()">CONFIRM</v-btn>
                      <v-btn :disabled="loading" color="#EF5354" @click="dialog = false" style="margin-left:5px">CANCEL</v-btn>
                    </div>
                  </v-col>
                  <v-col cols="auto">
                    <v-btn v-if="item['ssh_tunnel'] && mode != 'delete'" :loading="loading" color="info" @click="testConnection()">Test Connection</v-btn>
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
    // Data Table
    filter: 'all',
    headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'SSH Tunnel', align: 'left', value: 'ssh_tunnel'},
      { text: 'Hostname', align: 'left', value: 'hostname'},
      { text: 'Port', align: 'left', value: 'port'},
      { text: 'Username', align: 'left', value: 'username'},
      { text: 'Scope', align: 'left', value: 'shared' },
    ],
    regions: [],
    items: [],
    selected: [],
    search: '',
    item: { name: '', ssh_tunnel: false, hostname: null, port: null, username: null, password: null, key: null, shared: false },
    mode: '',
    loading: true,
    dialog: false,
    dialog_title: '',
    dialog_valid: false,
    showPassword: false,
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(5000),
    snackbarText: '',
    snackbarColor: ''
  }),
  computed: {
    owner: function() { return this.$store.getters['app/owner'] },
    inventory_secured: function() { return this.$store.getters['app/inventory_secured'] },
    readOnly: function() { return this.mode == 'edit' && !this.owner && this.item.shared == 1 }
  },
  created() {
    this.getRegions()
  },
  methods: {
    getRegions() {
      axios.get('/inventory/regions')
        .then((response) => {
          this.regions = response.data.data
          this.items = response.data.data
          this.filterBy(this.filter)
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    newRegion() {
      this.mode = 'new'
      this.item = { name: '', ssh_tunnel: false, hostname: null, port: '22', username: null, password: null, key: null, shared: false }
      this.dialog_title = 'NEW REGION'
      this.dialog = true
    },
    cloneRegion() {
      this.mode = 'clone'
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.item.shared = (!this.owner) ? false : this.item.shared
      this.dialog_title = 'CLONE REGION'
      this.dialog = true
    },
    editRegion() {
      this.mode = 'edit'
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.dialog_title = (!this.owner && this.item.shared) ? 'INFO' : 'EDIT REGION'
      this.dialog = true
    },
    deleteRegion() {
      this.mode = 'delete'
      this.dialog_title = 'DELETE REGION'
      this.dialog = true
    },
    submitRegion() {
      if (['new','clone'].includes(this.mode)) this.newRegionSubmit()
      else if (this.mode == 'edit') this.editRegionSubmit()
      else if (this.mode == 'delete') this.deleteRegionSubmit()
    },
    async newRegionSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
        return
      }
      // Get SSH Private Key
      let key = await this.readFileAsync(this.item.key)
      // Add item in the DB
      this.loading = true
      const payload = {...this.item, key}
      axios.post('/inventory/regions', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getRegions()
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    async editRegionSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
        return
      }
      // Get SSH Private Key
      let key = await this.readFileAsync(this.item.key)
      // Edit item in the DB
      this.loading = true
      const payload = {...this.item, key}
      axios.put('/inventory/regions', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getRegions()
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    deleteRegionSubmit() {
      this.loading = true
      // Build payload
      const payload = { regions: JSON.stringify(this.selected.map((x) => x.id)) }
      // Delete items to the DB
      axios.delete('/inventory/regions', { params: payload })
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getRegions()
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    async testConnection() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
        return
      }
      // Get SSH Private Key
      let key = await this.readFileAsync(this.item.key)
      // Test Connection
      this.loading = true
      const payload = (this.readOnly && this.inventory_secured) ? { region: this.item.id } : {...this.item, key}
      axios.post('/inventory/regions/test', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    filterBy(val) {
      this.filter = val
      if (val == 'all') this.items = this.regions.slice(0)
      else if (val == 'personal') this.items = this.regions.filter(x => !x.shared)
      else if (val == 'shared') this.items = this.regions.filter(x => x.shared)
    },
    readFileAsync(file) {
      if (file == null || typeof file !== 'object') return file
      return new Promise((resolve, reject) => {
        let reader = new FileReader()
        reader.onload = () => { resolve(reader.result)}
        reader.onerror = reject
        reader.readAsText(file, 'utf-8')
      })
    },
    notification(message, color, timeout=5) {
      this.snackbar = false
      setTimeout(() => {
        this.snackbarText = message
        this.snackbarColor = color
        this.snackbarTimeout = Number(timeout*1000)
        this.snackbar = true
      }, 10)
    }
  },
  watch: {
    dialog (val) {
      if (!val) return
      this.showPassword = false
      requestAnimationFrame(() => {
        if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
        if (typeof this.$refs.field !== 'undefined') this.$refs.field.focus()
      })
    },
  }
}
</script> 