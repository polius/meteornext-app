<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">AUXILIARY CONNECTIONS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text @click="newAuxiliary()"><v-icon small style="margin-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn v-if="selected.length == 1 && !(inventory_secured && selected[0].shared && !owner)" @click="cloneAuxiliary()" text><v-icon small style="margin-right:10px">fas fa-clone</v-icon>CLONE</v-btn>
          <v-btn v-if="selected.length == 1" text @click="editAuxiliary()"><v-icon small style="margin-right:10px">{{ !owner && selected[0].shared ? 'fas fa-info' : 'fas fa-feather-alt' }}</v-icon>{{ !owner && selected[0].shared ? 'INFO' : 'EDIT' }}</v-btn>
          <v-btn v-if="selected.length > 0 && !(!owner && selected.some(x => x.shared))" text @click="deleteAuxiliary()"><v-icon small style="margin-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
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
          <v-btn v-if="mode != 'delete'" :readonly="readOnly" title="Create the auxiliary only for you" :color="!item.shared ? 'primary' : '#779ecb'" @click="!readOnly ? item.shared = false : ''" style="margin-right:10px;"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-user</v-icon>Personal</v-btn>
          <v-btn v-if="mode != 'delete'" :disabled="!owner && !readOnly" :readonly="readOnly" title="Create the auxiliary for all users in your group" :color="item.shared ? 'primary' : '#779ecb'" @click="!readOnly ? item.shared = true : ''"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-users</v-icon>Shared</v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="dialog = false" icon><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 15px 15px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" v-model="dialog_valid" v-if="mode!='delete'" style="margin-top:15px;">
                  <v-text-field ref="field" v-model="item.name" :readonly="readOnly" :rules="[v => !!v || '']" label="Name" required></v-text-field>
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
                        <v-text-field v-model="item.hostname" :readonly="readOnly" :rules="[v => !!v || '']" label="Hostname" style="padding-top:0px;"></v-text-field>
                      </v-col>
                      <v-col cols="4" style="padding-left:10px">
                        <v-text-field v-model="item.port" :readonly="readOnly" :rules="[v => v == parseInt(v) || '']" label="Port" style="padding-top:0px;"></v-text-field>
                      </v-col>
                    </v-row>
                    <v-text-field v-model="item.username" :readonly="readOnly" :rules="[v => !!v || '']" label="Username" style="padding-top:0px;"></v-text-field>
                    <v-text-field v-model="item.password" :readonly="readOnly" label="Password" :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'" :type="showPassword ? 'text' : 'password'" @click:append="showPassword = !showPassword" style="padding-top:0px;" hide-details></v-text-field>
                    <v-switch v-model="item.ssl" :readonly="readOnly" flat label="SSL Connection" style="margin-top:20px" hide-details></v-switch>
                    <v-row no-gutters v-if="item.ssl" style="margin-top:20px">
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
                  </div>
                </v-form>
                <div style="padding-top:10px; padding-bottom:10px" v-if="mode=='delete'" class="subtitle-1">Are you sure you want to delete the selected auxiliary connections?</div>
                <v-divider></v-divider>
                <v-row no-gutters style="margin-top:20px;">
                  <v-col cols="auto" class="mr-auto">
                    <div v-if="readOnly">
                      <v-btn color="#00b16a" @click="dialog = false">CLOSE</v-btn>
                    </div>
                    <div v-else>
                      <v-btn :loading="loading" color="#00b16a" @click="submitAuxiliary()">CONFIRM</v-btn>
                      <v-btn :disabled="loading" color="error" @click="dialog = false" style="margin-left:5px">CANCEL</v-btn>
                    </div>
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

    <v-dialog v-model="testDialog" max-width="512px">
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">TEST CONNECTION</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn @click="testDialog = false" icon><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
      </v-toolbar>
      <v-card>
        <v-card-text style="padding:0px;">
          <v-container style="padding:15px 20px 20px;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="testForm">
                  <div class="body-1">Select a region to test the auxiliary connection:</div>
                  <v-autocomplete ref="testRegion" outlined :loading="testLoading" v-model="regionItem" item-value="id" :rules="[v => !!v || '']" :items="regionsItems" label="Region" required hide-details style="margin-top:15px;">
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
                <v-btn :disabled="testLoading" color="error" @click="testDialog = false" style="margin-left:5px">CANCEL</v-btn>
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
      { text: 'Engine', align: 'left', value: 'version'},
      { text: 'Hostname', align: 'left', value: 'hostname'},
      { text: 'Port', align: 'left', value: 'port'},
      { text: 'Username', align: 'left', value: 'username'},
      { text: 'Scope', align: 'left', value: 'shared' },
    ],
    auxiliary: [],
    items: [],
    selected: [],
    search: '',
    item: { name: '', engine: '', version: '', hostname: '', port: '', username: '', password: '', ssl: false, shared: false },
    mode: '',
    loading: true,
    engines: {
      'MySQL': ['MySQL 5.6', 'MySQL 5.7', 'MySQL 8.x'],
      'Aurora MySQL': ['Aurora MySQL 5.6', 'Aurora MySQL 5.7']
    },
    versions: [],
    dialog: false,
    dialog_title: '',
    dialog_valid: false,
    showPassword: false,
    // Test Dialog
    testDialog: false,
    testLoading: false,
    regionsItems: [],
    regionItem: null,
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  computed: {
    owner: function() { return this.$store.getters['app/owner'] },
    inventory_secured: function() { return this.$store.getters['app/inventory_secured'] },
    readOnly: function() { return this.mode == 'edit' && !this.owner && this.item.shared == 1 }
  },
  created() {
    this.getAuxiliary()
  },
  methods: {
    getAuxiliary() {
      axios.get('/inventory/auxiliary')
        .then((response) => {
          this.auxiliary = response.data.data
          this.items = response.data.data
          this.filterBy(this.filter)
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
      this.item = { name: '', engine: '', version: '', hostname: '', port: '', username: '', password: '', ssl: false, shared: false }
      this.dialog_title = 'NEW AUXILIARY'
      this.dialog = true
    },
    cloneAuxiliary() {
      this.mode = 'clone'
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.item.shared = (!this.owner) ? false : this.item.shared
      delete this.item['id']
      this.versions = this.engines[this.item.engine]
      this.dialog_title = 'CLONE AUXILIARY'
      this.dialog = true
    },
    editAuxiliary() {
      this.mode = 'edit'
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.versions = this.engines[this.item.engine]
      this.dialog_title = (!this.owner && this.item.shared) ? 'INFO' : 'EDIT AUXILIARY'
      this.dialog = true
    },
    deleteAuxiliary() {
      this.mode = 'delete'
      this.dialog_title = 'DELETE AUXILIARY'
      this.dialog = true
    },
    submitAuxiliary() {
      this.loading = true
      if (['new','clone'].includes(this.mode)) this.newAuxiliarySubmit()
      else if (this.mode == 'edit') this.editAuxiliarySubmit()
      else if (this.mode == 'delete') this.deleteAuxiliarySubmit()
    },
    newAuxiliarySubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      // Add item in the DB
      const payload = this.item
      axios.post('/inventory/auxiliary', payload)
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
    editAuxiliarySubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      // Edit item in the DB
      const payload = this.item
      axios.put('/inventory/auxiliary', payload)
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
      // Build payload
      const payload = { auxiliary: JSON.stringify(this.selected.map((x) => x.id)) }
      // Delete items to the DB
      axios.delete('/inventory/auxiliary', { params: payload })
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
      this.getRegions()
      this.testDialog = true
    },
    getRegions() {
      this.testLoading = true
      axios.get('/inventory/regions')
        .then((response) => {
          this.regionsItems = response.data.data.map(x => ({id: x.id, name: x.name, shared: x.shared }))
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.testLoading = false)
    },
    testConnection() {
      // Check if all fields are filled
      if (!this.$refs.testForm.validate()) {
        this.notification('Please select a region', 'error')
        return
      }
      // Test Connection
      this.notification('Testing Auxiliary Connection...', 'info', true)
      this.testLoading = true
      const payload = (this.readOnly && this.inventory_secured) ? { auxiliary: this.item.id, region: this.regionItem } : { ...this.item, region: this.regionItem }
      axios.post('/inventory/auxiliary/test', payload)
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
      this.filter = val
      if (val == 'all') this.items = this.auxiliary.slice(0)
      else if (val == 'personal') this.items = this.auxiliary.filter(x => !x.shared)
      else if (val == 'shared') this.items = this.auxiliary.filter(x => x.shared)
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
      this.showPassword = false
      requestAnimationFrame(() => {
        if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
        if (typeof this.$refs.field !== 'undefined') this.$refs.field.focus()
      })
    },
    testDialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.testForm !== 'undefined') this.$refs.testForm.resetValidation()
        if (typeof this.$refs.testRegion !== 'undefined') this.$refs.testRegion.focus()
      })
    }
  }
}
</script>