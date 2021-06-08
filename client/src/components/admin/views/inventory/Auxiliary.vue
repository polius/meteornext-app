<template>
  <div>
    <v-data-table v-model="selected" :headers="computedHeaders" :items="items" :search="filter.search" :loading="loading" loading-text="Loading... Please wait" item-key="id" show-select class="elevation-1" style="padding-top:3px;">
      <template v-ripple v-slot:[`header.data-table-select`]="{}">
        <v-simple-checkbox
          :value="items.length == 0 ? false : selected.length == items.length"
          :indeterminate="selected.length > 0 && selected.length != items.length"
          @click="selected.length == items.length ? selected = [] : selected = JSON.parse(JSON.stringify(items))">
        </v-simple-checkbox>
      </template>
      <template v-slot:[`item.shared`]="{ item }">
        <v-icon v-if="!item.shared" small title="Personal" color="warning" style="margin-right:6px; margin-bottom:2px;">fas fa-user</v-icon>
        <v-icon v-else small title="Shared" color="#EB5F5D" style="margin-right:6px; margin-bottom:2px;">fas fa-users</v-icon>
        {{ !item.shared ? 'Personal' : 'Shared' }}
      </template>
      <template v-slot:[`item.ssl`]="{ item }">
        <v-icon small :title="item.ssl ? 'SSL Enabled' : 'SSL Disabled'" :color="item.ssl ? '#00b16a' : 'error'" style="margin-left:2px">fas fa-circle</v-icon>
      </template>
    </v-data-table>

    <v-dialog v-model="dialog" persistent max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1">{{ dialog_title }}</v-toolbar-title>
          <v-divider v-if="mode != 'delete'" class="mx-3" inset vertical></v-divider>
          <v-btn v-if="mode != 'delete'" title="Create the auxiliary only for a user" :color="!item.shared ? 'primary' : '#779ecb'" @click="item.shared = false" style="margin-right:10px;"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-user</v-icon>Personal</v-btn>
          <v-btn v-if="mode != 'delete'" title="Create the auxiliary for all users in a group" :color="item.shared ? 'primary' : '#779ecb'" @click="item.shared = true"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-users</v-icon>Shared</v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="dialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 15px 15px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" v-if="mode!='delete'" style="margin-top:20px;">
                  <v-row v-if="mode!='delete'" no-gutters style="margin-bottom:15px">
                    <v-col>
                      <v-autocomplete ref="group_id" :readonly="mode == 'edit'" @change="groupChanged" v-model="item.group_id" :items="groups" item-value="id" item-text="name" label="Group" :rules="[v => !!v || '']" hide-details style="padding-top:0px"></v-autocomplete>
                    </v-col>
                    <v-col v-if="!item.shared" style="margin-left:20px">
                      <v-autocomplete ref="owner_id" v-model="item.owner_id" :items="users" item-value="id" item-text="username" label="Owner" :rules="[v => !!v || '']" hide-details style="padding-top:0px"></v-autocomplete>
                    </v-col>
                  </v-row>
                  <v-text-field ref="name" v-model="item.name" :rules="[v => !!v || '']" label="Name" required></v-text-field>
                  <v-row no-gutters>
                    <v-col cols="8" style="padding-right:10px">
                      <v-select v-model="item.engine" :items="Object.keys(engines)" label="Engine" :rules="[v => !!v || '']" required style="padding-top:0px;" v-on:change="selectEngine"></v-select>
                    </v-col>
                    <v-col cols="4" style="padding-left:10px">
                      <v-select v-model="item.version" :items="versions" label="Version" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-select>
                    </v-col>
                  </v-row>
                  <div style="margin-bottom:20px;">
                    <v-row no-gutters>
                      <v-col cols="8" style="padding-right:10px">
                        <v-text-field v-model="item.hostname" :rules="[v => !!v || '']" label="Hostname" style="padding-top:0px;"></v-text-field>
                      </v-col>
                      <v-col cols="4" style="padding-left:10px">
                        <v-text-field v-model="item.port" :rules="[v => v == parseInt(v) || '']" label="Port" style="padding-top:0px;"></v-text-field>
                      </v-col>
                    </v-row>
                    <v-text-field v-model="item.username" :rules="[v => !!v || '']" label="Username" autocomplete="username" style="padding-top:0px;"></v-text-field>
                    <v-text-field v-model="item.password" label="Password" :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'" :type="showPassword ? 'text' : 'password'" @click:append="showPassword = !showPassword" autocomplete="new-password" style="padding-top:0px;" hide-details></v-text-field>
                    <div v-if="(item.ssl_client_key == null || typeof item.ssl_client_key === 'object') && (item.ssl_client_certificate == null || typeof item.ssl_client_certificate === 'object') && (item.ssl_ca_certificate == null || typeof item.ssl_ca_certificate === 'object')">
                      <v-switch v-model="item.ssl" flat label="SSL Connection" hide-details style="margin-top:20px"></v-switch>
                      <v-row no-gutters v-if="item.ssl" style="margin-top:20px; margin-bottom:20px;">
                        <v-col style="padding-right:10px;">
                          <v-file-input v-model="item.ssl_client_key" filled dense label="Client Key" prepend-icon="" hide-details></v-file-input>
                        </v-col>
                        <v-col style="padding-right:5px; padding-left:5px;">
                          <v-file-input v-model="item.ssl_client_certificate" filled dense label="Client Certificate" prepend-icon="" hide-details></v-file-input>
                        </v-col>
                        <v-col style="padding-left:10px;">
                          <v-file-input v-model="item.ssl_ca_certificate" filled dense label="CA Certificate" prepend-icon="" hide-details></v-file-input>
                        </v-col>
                      </v-row>
                    </div>
                    <v-card v-else style="height:52px; margin-top:20px">
                      <v-row no-gutters>
                        <v-col cols="auto" style="display:flex; margin:15px">
                          <v-icon color="#00b16a" style="font-size:20px">fas fa-key</v-icon>
                        </v-col>
                        <v-col>
                          <div class="text-body-1" style="color:#00b16a; margin-top:15px">{{ 'Using a SSL connection (' + ssl_active + ')' }}</div>
                        </v-col>
                        <v-col cols="auto" class="text-right">
                          <v-btn @click="removeSSL" icon title="Remove SSL connection" style="margin:8px"><v-icon style="font-size:18px">fas fa-times</v-icon></v-btn>
                        </v-col>
                      </v-row>
                    </v-card>
                    <v-checkbox v-if="item.ssl" v-model="item.ssl_verify_ca" label="Verify server certificate against CA" hide-details></v-checkbox>
                  </div>
                </v-form>
                <div style="padding-top:10px; padding-bottom:10px" v-if="mode=='delete'" class="subtitle-1">Are you sure you want to delete the selected auxiliary connections?</div>
                <v-divider></v-divider>
                <v-row no-gutters style="margin-top:20px;">
                  <v-col cols="auto" class="mr-auto">
                    <v-btn :loading="loading" color="#00b16a" @click="submitAuxiliary()">CONFIRM</v-btn>
                    <v-btn :disabled="loading" color="#EF5354" @click="dialog = false" style="margin-left:5px">CANCEL</v-btn>
                  </v-col>
                  <v-col cols="auto">
                    <v-btn v-if="mode != 'delete'" :loading="loading" color="info" @click="openTest()">Test Connection</v-btn>
                  </v-col>
                </v-row>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!----------------->
    <!-- TEST DIALOG -->
    <!----------------->
    <v-dialog v-model="testDialog" max-width="512px">
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">TEST CONNECTION</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn @click="testDialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
      </v-toolbar>
      <v-card>
        <v-card-text style="padding:0px;">
          <v-container style="padding:15px 20px 20px;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="testForm">
                  <div class="body-1">Select a region to test the auxiliary connection:</div>
                  <v-autocomplete ref="testRegion" outlined :loading="testLoading" v-model="regionItem" item-value="id" item-text="name" :rules="[v => !!v || '']" :items="regionsItems" label="Region" required hide-details style="margin-top:15px;">
                    <template v-slot:[`selection`]="{ item }">
                      <v-icon small :color="item.shared ? '#EB5F5D' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                      {{ item.name }}
                    </template>
                    <template v-slot:[`item`]="{ item }">
                      <v-icon small :color="item.shared ? '#EB5F5D' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                      {{ item.name }}
                    </template>
                  </v-autocomplete>
                </v-form>
                <v-divider style="margin-top:20px; margin-bottom:20px"></v-divider>
                <v-btn :loading="testLoading" color="#00b16a" @click="testConnection()">TEST CONNECTION</v-btn>
                <v-btn :disabled="testLoading" color="#EF5354" @click="testDialog = false" style="margin-left:5px">CANCEL</v-btn>
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
                  <v-checkbox v-model="columnsRaw" label="Engine" value="version" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Hostname" value="hostname" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Port" value="port" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Username" value="username" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="SSL" value="ssl" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Scope" value="shared" hide-details style="margin-top:5px"></v-checkbox>
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

<script>
import EventBus from '../../js/event-bus'
import axios from 'axios';
import moment from 'moment'

export default {
  data: () => ({
    headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Engine', align: 'left', value: 'version'},
      { text: 'Hostname', align: 'left', value: 'hostname'},
      { text: 'Port', align: 'left', value: 'port'},
      { text: 'Username', align: 'left', value: 'username'},
      { text: 'SSL', align: 'left', value: 'ssl'},
      { text: 'Scope', align: 'left', value: 'shared' },
      { text: 'Group', align: 'left', value: 'group' },
      { text: 'Owner', align: 'left', value: 'owner' },
      { text: 'Created By', align: 'left', value: 'created_by' },
      { text: 'Created At', align: 'left', value: 'created_at' },
      { text: 'Updated By', align: 'left', value: 'updated_by' },
      { text: 'Updated At', align: 'left', value: 'updated_at' },
    ],
    auxiliary: [],
    items: [],
    selected: [],
    search: '',
    item: { group_id: '', owner_id: '', name: '', engine: '', version: '', hostname: '', port: '', username: '', password: '', ssl: false, shared: true },
    mode: '',
    loading: true,
    engines: {
      'MySQL': ['MySQL 5.6', 'MySQL 5.7', 'MySQL 8.x'],
      'Aurora MySQL': ['Aurora MySQL 5.6', 'Aurora MySQL 5.7']
    },
    versions: [],
    dialog: false,
    dialog_title: '',
    users: [],
    showPassword: false,
    // Test Dialog
    testDialog: false,
    testLoading: false,
    regionsItems: [],
    regionItem: null,
    // Filter Columns Dialog
    columnsDialog: false,
    columns: ['name','region','version','hostname','port','username','shared','group','owner'],
    columnsRaw: [],
  }),
  props: ['tab','groups','filter'],
  mounted () {
    EventBus.$on('filter-auxiliary', this.filterAuxiliary);
    EventBus.$on('filter-auxiliary-columns', this.filterAuxiliaryColumns);
    EventBus.$on('new-auxiliary', this.newAuxiliary);
    EventBus.$on('clone-auxiliary', this.cloneAuxiliary);
    EventBus.$on('edit-auxiliary', this.editAuxiliary);
    EventBus.$on('delete-auxiliary', this.deleteAuxiliary);
  },
  computed: {
    computedHeaders() { return this.headers.filter(x => this.columns.includes(x.value)) },
    ssl_active: function() {
      let elements = []
      if (this.item.ssl_client_key != null) elements.push('Client Key')
      if (this.item.ssl_client_certificate != null) elements.push('Client Certificate')
      if (this.item.ssl_ca_certificate != null) elements.push('CA Certificate')
      return elements.join(' + ')
    }
  },
  methods: {
    groupChanged() {
      this.item.owner_id = null
      requestAnimationFrame(() => {
        if (!this.item.shared) this.$refs.owner_id.focus()
      })
      if (this.item.group_id != null) this.getUsers()
    },
    getUsers() {
      axios.get('/admin/inventory/users', { params: { group_id: this.item.group_id }})
        .then((response) => {
          this.users = response.data.users
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
    },
    getAuxiliary() {
      this.loading = true
      const payload = (this.filter.by == 'group' & this.filter.group != null) ? { group_id: this.filter.group } : (this.filter.by == 'user') ? { user_id: this.filter.user } : {}
      axios.get('/admin/inventory/auxiliary', { params: payload})
        .then((response) => {
          response.data.auxiliary.map(x => {
            x['created_at'] = this.dateFormat(x['created_at'])
            x['updated_at'] = this.dateFormat(x['updated_at'])
          })
          this.auxiliary = response.data.auxiliary
          this.items = response.data.auxiliary
          this.filterBy(this.filter.scope)
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
    },
    selectEngine(value) {
      if (this.item.port == '') {
        if (['MySQL','Aurora MySQL'].includes(value)) this.item.port = '3306'
        else if (value == 'PostgreSQL') this.item.port = '5432'
      }
      this.versions = this.engines[value]
    },
    newAuxiliary() {
      this.mode = 'new'
      this.users = []
      this.item = { group_id: this.filter.group, owner_id: '', name: '', engine: '', version: '', hostname: '', port: '', username: '', password: '', ssl: false, shared: true }
      if (this.filter.group != null) this.getUsers()
      this.dialog_title = 'NEW AUXILIARY'
      this.dialog = true
    },
    cloneAuxiliary() {
      this.mode = 'clone'
      this.users = []
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.getUsers()
      this.versions = this.engines[this.item.engine]
      this.dialog_title = 'CLONE AUXILIARY'
      this.dialog = true
    },
    editAuxiliary() {
      this.mode = 'edit'
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.getUsers()
      this.versions = this.engines[this.item.engine]
      this.dialog_title = 'EDIT AUXILIARY'
      this.dialog = true
    },
    deleteAuxiliary() {
      this.mode = 'delete'
      this.dialog_title = 'DELETE AUXILIARY'
      this.dialog = true
    },
    submitAuxiliary() {
      if (['new','clone'].includes(this.mode)) this.newAuxiliarySubmit()
      else if (this.mode == 'edit') this.editAuxiliarySubmit()
      else if (this.mode == 'delete') this.deleteAuxiliarySubmit()
    },
    async newAuxiliarySubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        return
      }
      // Get SSL Imported Files
      let ssl_ca_certificate = await this.readFileAsync(this.item.ssl_ca_certificate)
      let ssl_client_key = await this.readFileAsync(this.item.ssl_client_key)
      let ssl_client_certificate = await this.readFileAsync(this.item.ssl_client_certificate)
      // Check SSL fields
      if (this.item.ssl && ssl_ca_certificate == null && ssl_client_key == null && ssl_client_certificate == null) {
        this.notification('Import at least one SSL certificate/key', 'error')
        return
      }
      // Parse SSL
      ssl_ca_certificate = (ssl_ca_certificate === undefined) ? null : ssl_ca_certificate
      ssl_client_key = (ssl_client_key === undefined) ? null : ssl_client_key
      ssl_client_certificate = (ssl_client_certificate === undefined) ? null : ssl_client_certificate
      // Add item in the DB
      this.loading = true
      const payload = {...this.item, ssl_ca_certificate, ssl_client_key, ssl_client_certificate}
      axios.post('/admin/inventory/auxiliary', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getAuxiliary()
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
    },
    async editAuxiliarySubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        return
      }
      // Get SSL Imported Files
      let ssl_ca_certificate = await this.readFileAsync(this.item.ssl_ca_certificate)
      let ssl_client_key = await this.readFileAsync(this.item.ssl_client_key)
      let ssl_client_certificate = await this.readFileAsync(this.item.ssl_client_certificate)
      if (this.item.ssl && ssl_ca_certificate == null && ssl_client_key == null && ssl_client_certificate == null) {
        this.notification('Import at least one SSL certificate/key', 'error')
        return
      }
      // Parse SSL
      ssl_ca_certificate = (ssl_ca_certificate === undefined) ? null : ssl_ca_certificate
      ssl_client_key = (ssl_client_key === undefined) ? null : ssl_client_key
      ssl_client_certificate = (ssl_client_certificate === undefined) ? null : ssl_client_certificate
      // Edit item in the DB
      this.loading = true
      const payload = {...this.item, ssl_ca_certificate, ssl_client_key, ssl_client_certificate}
      axios.put('/admin/inventory/auxiliary', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getAuxiliary()
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
    },
    deleteAuxiliarySubmit() {
      this.loading = true
      // Build payload
      const payload = { auxiliary: JSON.stringify(this.selected.map((x) => x.id)) }
      // Delete items to the DB
      axios.delete('/admin/inventory/auxiliary', { params: payload })
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getAuxiliary()
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
    },
    openTest() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        return
      }
      this.regionItem = null
      this.testDialog = true
      this.getRegions()
    },
    getRegions() {
      this.testLoading = true
      const payload = this.item.shared ? { group_id: this.item.group_id } : { group_id: this.item.group_id, owner_id: this.item.owner_id }
      axios.get('/admin/inventory/regions', { params: payload})
        .then((response) => {
          this.regionsItems = response.data.regions.map(x => ({id: x.id, name: x.name, shared: x.shared }))
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.testLoading = false)
    },
    async testConnection() {
      // Check if all fields are filled
      if (!this.$refs.testForm.validate()) {
        this.notification('Please select a region', 'error')
        return
      }
      // Get SSL Imported Files
      let ssl_ca_certificate = await this.readFileAsync(this.item.ssl_ca_certificate)
      let ssl_client_key = await this.readFileAsync(this.item.ssl_client_key)
      let ssl_client_certificate = await this.readFileAsync(this.item.ssl_client_certificate)
      if (this.item.ssl && ssl_ca_certificate == null && ssl_client_key == null && ssl_client_certificate == null) {
        this.notification('Import at least one SSL certificate/key', 'error')
        return
      }
      // Test Connection
      this.testLoading = true
      const payload = { ...this.item, region: this.regionItem, ssl_client_key, ssl_client_certificate, ssl_ca_certificate }
      axios.post('/admin/inventory/auxiliary/test', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.testLoading = false)
    },
    filterBy(val) {
      if (val == 'all') this.items = this.auxiliary.slice(0)
      else if (val == 'personal') this.items = this.auxiliary.filter(x => !x.shared)
      else if (val == 'shared') this.items = this.auxiliary.filter(x => x.shared)
    },
    filterAuxiliary() {
      this.selected = []
      if (this.filter.group != null) this.columns = this.columns.filter(x => x != 'group')
      else if (!this.columns.some(x => x == 'group')) this.columns.push('group')
      this.getAuxiliary()
    },
    filterAuxiliaryColumns() {
      this.columnsRaw = [...this.columns]
      this.columnsDialog = true
    },
    selectAllColumns() {
      this.columnsRaw = ['name','region','version','hostname','port','username','ssl','shared','group','owner','created_by','created_at','updated_by','updated_at']
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
    readFileAsync(file) {
      if (file == null || typeof file !== 'object') return file
      return new Promise((resolve, reject) => {
        let reader = new FileReader()
        reader.onload = () => { resolve(reader.result)}
        reader.onerror = reject
        reader.readAsText(file, 'utf-8')
      })
    },
    removeSSL() {
      this.item.ssl_ca_certificate = null
      this.item.ssl_client_key = null
      this.item.ssl_client_certificate = null
    },
    notification(message, color, persistent=false) {
      EventBus.$emit('notification', message, color, persistent)
    }
  },
  watch: {
    dialog (val) {
      if (!val) return
      this.showPassword = false
      this.showSSHPassword = false
      requestAnimationFrame(() => {
        if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
        if (this.mode == 'new') {
          if (this.filter.group == null) this.$refs.group_id.focus()
          else this.$refs.name.focus()
        }
        else if (['clone','edit'].includes(this.mode)) this.$refs.name.focus()
      })
    },
    testDialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.testForm !== 'undefined') this.$refs.testForm.resetValidation()
        if (typeof this.$refs.testRegion !== 'undefined') this.$refs.testRegion.focus()
      })
    },
    selected(val) {
      EventBus.$emit('change-selected', val)
    },
    tab(val) {
      this.selected = []
      if (val == 3) this.getAuxiliary()
    }
  }
}
</script>