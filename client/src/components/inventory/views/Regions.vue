<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">REGIONS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items>
          <v-btn text @click="newRegion()"><v-icon small style="margin-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn :disabled="selected.length != 1 || selected[0].secured == 1" text @click="editRegion()"><v-icon small style="margin-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
          <v-btn :disabled="selected.length != 1 || selected[0].secured == 1" @click="cloneRegion()" text><v-icon small style="margin-right:10px">fas fa-clone</v-icon>CLONE</v-btn>
          <v-btn :disabled="selected.length == 0 || selected.some(x => x.secured) || (!owner && selected.some(x => x.shared))" text @click="deleteRegion()"><v-icon small style="margin-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="testRegion" :disabled="selected.length != 1 || !selected[0].ssh_tunnel" title="Test a region connection" text><v-icon small style="margin-right:10px">fas fa-server</v-icon>TEST</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn text class="body-2" @click="filterBy('all')" :style="filter == 'all' ? 'font-weight:600' : 'font-weight:400'">ALL</v-btn>
          <v-btn text class="body-2" @click="filterBy('personal')" :style="filter == 'personal' ? 'font-weight:600' : 'font-weight:400'">PERSONAL</v-btn>
          <v-btn text class="body-2" @click="filterBy('shared')" :style="filter == 'shared' ? 'font-weight:600' : 'font-weight:400'">SHARED</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
        </v-toolbar-items>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
        <v-divider class="mx-3" inset vertical style="margin-right:4px!important"></v-divider>
        <v-btn @click="openColumnsDialog" icon title="Show/Hide columns" style="margin-right:-10px; width:40px; height:40px;"><v-icon small>fas fa-cog</v-icon></v-btn>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="computedHeaders" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="id" show-select class="elevation-1" style="padding-top:3px;" mobile-breakpoint="0">
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
        <template v-slot:[`item.ssh_tunnel`]="{ item }">
          <v-icon v-if="item.ssh_tunnel" small color="#00b16a" style="margin-left:20px">fas fa-circle</v-icon>
          <v-icon v-else small color="#EF5354" style="margin-left:20px">fas fa-circle</v-icon>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="dialog" persistent max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:2px">{{ getIcon(mode) }}</v-icon>{{ dialog_title }}</v-toolbar-title>
          <v-divider v-if="mode != 'delete'" class="mx-3" inset vertical></v-divider>
          <v-btn v-if="mode != 'delete'" :disabled="(item.shared == 1 && !owner)" @click="item.shared = false" title="Create the region only for you" :color="!item.shared ? 'primary' : '#779ecb'" style="margin-right:10px;"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-user</v-icon>Personal</v-btn>
          <v-btn v-if="mode != 'delete'" :disabled="(item.shared == 0 && !owner)" @click="item.shared = true" title="Create the region for all users in your group" :color="item.shared ? 'primary' : '#779ecb'"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-users</v-icon>Shared</v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="dialog = false" icon><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-alert v-if="!owner && item.shared" color="warning" outlined dense style="margin-bottom:30px"><v-icon color="warning" style="font-size:16px; margin-bottom:3px; margin-right:10px">fas fa-exclamation-triangle</v-icon>This resource cannot be edited. You are not a group owner.</v-alert>
                <v-form v-if="mode != 'delete'" ref="form" style="margin-top:15px; margin-bottom:15px;">
                  <v-text-field ref="field" v-model="item.name" :rules="[v => !!v || '']" :readonly="readonly" label="Name" required hide-details style="margin-top:0px; padding-top:0px"></v-text-field>
                  <v-switch @click="sshtunnelClick" v-model="item.ssh_tunnel" :readonly="readonly" label="SSH Tunnel" color="info" hide-details style="margin-top:15px"></v-switch>
                  <div v-if="item.ssh_tunnel" style="margin-top:25px">
                    <v-row no-gutters>
                      <v-col cols="9" style="padding-right:10px">
                        <v-text-field ref="hostname" v-model="item.hostname" :readonly="readonly" :rules="[v => !!v || '']" label="Hostname" style="padding-top:0px; margin-top:0px"></v-text-field>
                      </v-col>
                      <v-col cols="3" style="padding-left:10px">
                        <v-text-field v-model="item.port" :readonly="readonly" :rules="[v => v == parseInt(v) || '']" label="Port" style="padding-top:0px; margin-top:0px"></v-text-field>
                      </v-col>
                    </v-row>
                    <v-text-field v-model="item.username" :readonly="readonly" :rules="[v => !!v || '']" label="Username" autocomplete="username"  style="padding-top:0px;"></v-text-field>
                    <v-text-field v-model="item.password" :readonly="readonly" label="Password" :type="showPassword ? 'text' : 'password'" autocomplete="new-password" style="padding-top:0px;">
                      <template v-slot:[`append`]>
                        <v-btn title="Generate password" @click="generatePassword" icon><v-icon>mdi-key</v-icon></v-btn>
                        <v-btn :title="showPassword ? 'Hide password' : 'Show password'" @click="showPassword = !showPassword" icon><v-icon>{{ showPassword ? 'mdi-eye' : 'mdi-eye-off' }}</v-icon></v-btn>
                      </template>
                    </v-text-field>
                    <v-file-input v-if="item.key == null || typeof item.key === 'object'" v-model="item.key" filled label="Private Key" prepend-icon="" hide-details style="padding-top:0px"></v-file-input>
                    <v-card v-else style="height:52px">
                      <v-row no-gutters>
                        <v-col cols="auto" style="display:flex; margin:15px">
                          <v-icon color="#00b16a" style="font-size:17px; margin-top:2px">fas fa-key</v-icon>
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
                <div v-else class="subtitle-1" style="margin-bottom:12px">Are you sure you want to delete the selected regions?</div>
                <v-divider></v-divider>
                <v-row no-gutters style="margin-top:20px;">
                  <v-col cols="auto" class="mr-auto">
                    <v-btn :loading="loading" color="#00b16a" @click="submitRegion()">CONFIRM</v-btn>
                    <v-btn :disabled="loading" color="#EF5354" @click="dialog = false" style="margin-left:5px">CANCEL</v-btn>
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
                  <v-checkbox v-model="columnsRaw" label="SSH Tunnel" value="ssh_tunnel" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Hostname" value="hostname" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Port" value="port" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Username" value="username" hide-details style="margin-top:5px"></v-checkbox>
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
    showPassword: false,
    // Filter Columns Dialog
    columnsDialog: false,
    columns: ['name','ssh_tunnel','hostname','port','username','shared'],
    columnsRaw: [],
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  computed: {
    owner: function() { return this.$store.getters['app/owner'] },
    readonly: function() { return this.item.shared == 1 && !this.owner },
    computedHeaders() { return this.headers.filter(x => this.columns.includes(x.value)) },
  },
  created() {
    this.getRegions()
  },
  methods: {
    getRegions() {
      this.loading = true
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
      this.dialog_title = 'EDIT REGION'
      this.dialog = true
    },
    deleteRegion() {
      this.mode = 'delete'
      this.dialog_title = 'DELETE REGION'
      this.dialog = true
    },
    testRegion() {
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.testConnection()
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
      if (!this.item.secured && !this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
        return
      }
      // Get SSH Private Key
      let key = await this.readFileAsync(this.item.key)
      // Test Connection
      this.loading = true
      const payload = this.item.secured ? { region: this.item.id } : {...this.item, key}
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
    generatePassword() {
      axios.get('/inventory/genpass')
        .then((response) => {
          this.item.password = response.data.password
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
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
    getIcon(mode) {
      if (mode == 'new') return 'fas fa-plus'
      if (mode == 'edit') return 'fas fa-feather-alt'
      if (mode == 'delete') return 'fas fa-minus'
      if (mode == 'clone') return 'fas fa-clone'
    },
    openColumnsDialog() {
      this.columnsRaw = [...this.columns]
      this.columnsDialog = true
    },
    selectAllColumns() {
      this.columnsRaw = ['name','ssh_tunnel','hostname','port','username','shared']
    },
    deselectAllColumns() {
      this.columnsRaw = []
    },
    filterColumns() {
      this.columns = [...this.columnsRaw]
      this.columnsDialog = false
    },
    sshtunnelClick(val) {
      requestAnimationFrame(() => {
        if (val && typeof this.$refs.hostname !== 'undefined' && !this.readonly) this.$refs.hostname.focus()
      })
    },
    notification(message, color, timeout=3) {
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
        if (typeof this.$refs.field !== 'undefined' && !this.readonly) this.$refs.field.focus()
      })
    },
  }
}
</script> 