<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">USERS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text @click="newUser()" class="body-2"><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn v-if="selected.length == 1" text @click="editUser()" class="body-2"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
          <v-btn v-if="selected.length > 0" text @click="deleteUser()" class="body-2"><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn text class="body-2" @click="filterBy('all')" :style="filter == 'all' ? 'font-weight:600' : 'font-weight:400'">ALL</v-btn>
          <v-btn text class="body-2" @click="filterBy('enabled')" :style="filter == 'enabled' ? 'font-weight:600' : 'font-weight:400'">ENABLED</v-btn>
          <v-btn text class="body-2" @click="filterBy('disabled')" :style="filter == 'disabled' ? 'font-weight:600' : 'font-weight:400'">DISABLED</v-btn>
        </v-toolbar-items>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="username" show-select class="elevation-1" style="padding-top:3px;">
        <template v-slot:[`item.mfa`]="{ item }">
          <v-icon v-if="item.mfa" small color="#00b16a" style="margin-left:2px;">fas fa-circle</v-icon>
          <v-icon v-else small color="error" style="margin-left:2px;">fas fa-circle</v-icon>
        </template>
        <template v-slot:[`item.admin`]="{ item }">
          <v-icon v-if="item.admin" small color="#00b16a" style="margin-left:8px;">fas fa-circle</v-icon>
          <v-icon v-else small color="error" style="margin-left:8px;">fas fa-circle</v-icon>
        </template>
        <template v-slot:[`item.created_at`]="{ item }">
          <span>{{ dateFormat(item.created_at) }}</span>
        </template>
        <template v-slot:[`item.last_login`]="{ item }">
          <span>{{ dateFormat(item.last_login) }}</span>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="dialog" persistent max-width="768px">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">{{ dialog_title }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="dialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 20px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" v-model="dialog_valid" v-if="mode!='delete'" style="margin-top:15px; margin-bottom:20px;">
                  <v-text-field ref="field" v-model="item.username" :rules="[v => !!v || '']" label="Username" required append-icon="person"></v-text-field>
                  <v-text-field v-model="item.email" :rules="[v => !!v || '', v => /.+@.+\..+/.test(v) || '']" label="Email" type="email" required append-icon="email" style="padding-top:0px;"></v-text-field>
                  <v-text-field v-model="item.password" :rules="[v => !!v || '']" label="Password" type="password" required append-icon="lock" style="padding-top:0px;"></v-text-field>
                  <v-text-field v-model="item.coins" :rules="[v => v == parseInt(v) && v >= 0 || '']" label="Coins" required append-icon="monetization_on" style="padding-top:0px;"></v-text-field>
                  <v-autocomplete v-model="item.group" :items="groups" :rules="[v => !!v || '']" label="Group" required hide-details style="padding-top:0px; margin-bottom:20px;"></v-autocomplete>
                  <v-switch v-if="mode == 'edit'" v-model="item.mfa.enabled" @change="onMFAChange" :loading="loading" :disabled="loading" flat label="Multi-Factor Authentication (MFA)" hide-details style="margin-bottom:10px"></v-switch>
                  <v-card v-if="item.mfa.enabled && !item.mfa.origin" style="width:232px; margin-bottom:15px;">
                    <v-card-text>
                      <v-progress-circular v-if="item.mfa.uri == null" indeterminate style="margin-left:auto; margin-right:auto; display:table;"></v-progress-circular>
                      <qrcode-vue v-else :value="item.mfa.uri" size="200" level="H" background="#ffffff" foreground="#000000"></qrcode-vue>
                      <v-text-field outlined v-model="item.mfa.value" v-on:keyup.enter="submitUser()" label="MFA Code" append-icon="vpn_key" :rules="[v => v == parseInt(v) && v >= 0 || '']" required hide-details style="margin-top:10px"></v-text-field>
                    </v-card-text>
                  </v-card>
                  <v-switch v-model="item.admin" label="Administrator" color="info" style="margin-top:10px;" hide-details></v-switch>
                  <v-switch v-model="item.disabled" label="Disable Account" color="error" style="margin-top:10px;" hide-details></v-switch>
                </v-form>
                <div style="padding-top:10px; padding-bottom:10px" v-if="mode=='delete'" class="subtitle-1">Are you sure you want to delete the selected users?</div>
                <v-alert v-if="mode=='delete'" type="error" dense>All selected users related data (deployments, client, inventory) will be deleted.</v-alert>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :loading="loading" color="#00b16a" @click="submitUser()">Confirm</v-btn>
                  <v-btn :disabled="loading" color="error" @click="dialog=false" style="margin-left:10px">Cancel</v-btn>
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
import moment from 'moment';
import QrcodeVue from 'qrcode.vue'

export default {
  data: () => ({
    // Data Table
    filter: 'all',
    headers: [
      { text: 'Username', align: 'left', value: 'username' },
      { text: 'Group', align: 'left', value: 'group' },
      { text: 'Email', align: 'left', value: 'email'},
      { text: 'Created', align: 'left', value: 'created_at'},
      { text: 'Last login', align: 'left', value: 'last_login'},
      { text: 'Coins', align: 'left', value: 'coins'},
      { text: 'MFA', align: 'left', value: 'mfa'},
      { text: 'Admin', align: 'left', value: 'admin'},
    ],
    users: [],
    items: [],
    selected: [],
    search: '',
    item: { username: '', email: '', password: '', coins: '', group: '', mfa: { enabled: false, origin: false, hash: null, uri: null, value: ''}, admin: false, disabled: false },
    mode: '',
    loading: true,
    dialog: false,
    dialog_title: '',
    dialog_valid: false,
    // User Groups
    groups: [],
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(4000),
    snackbarText: '',
    snackbarColor: ''
  }),
  components: { QrcodeVue },
  created() {
    this.getUsers()
  },
  methods: {
    getUsers() {
      axios.get('/admin/users')
        .then((response) => {
          this.users = response.data.data.users
          this.items = response.data.data.users
          this.groups = response.data.data.groups.map(x => x.name)
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
    },
    newUser() {
      this.mode = 'new'
      this.item = { username: '', email: '', password: '', coins: '', group: '', mfa: { enabled: false, origin: false, hash: null, uri: null, value: ''}, admin: false, disabled: false }
      this.dialog_title = 'New User'
      this.dialog = true
    },
    editUser() {
      this.mode = 'edit'
      let item = JSON.parse(JSON.stringify(this.selected[0]))
      item.mfa = { enabled: item.mfa, origin: item.mfa, hash: this.item.mfa_hash, uri: null, value: ''}
      this.item = item
      this.dialog_title = 'Edit User'
      this.dialog = true
    },
    deleteUser() {
      this.mode = 'delete'
      this.dialog_title = 'Delete User'
      this.dialog = true
    },
    submitUser() {
      if (this.mode == 'new') this.newUserSubmit()
      else if (this.mode == 'edit') this.editUserSubmit()
      else if (this.mode == 'delete') this.deleteUserSubmit()
    },
    newUserSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        return
      }
      // Check if new item already exists
      for (var i = 0; i < this.items.length; ++i) {
        if (this.items[i]['username'] == this.item.username) {
          this.notification('This user currently exists', 'error')
          return
        }
      }
      // Add item to the DB
      this.loading = true
      const payload = this.item
      axios.post('/admin/users', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          // Retrieve again the users list
          this.getUsers()
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
    },
    editUserSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        return
      }
      // Get Item Position
      for (var i = 0; i < this.items.length; ++i) {
        if (this.items[i]['username'] == this.selected[0]['username']) break
      }
      // Check if edited item already exists
      for (var j = 0; j < this.items.length; ++j) {
        if (this.items[j]['username'] == this.item.username && this.item.username != this.selected[0]['username']) {
          this.notification('This user currently exists', 'error')
          return
        }
      }
      // Add item to the DB
      this.loading = true
      const payload = { 
        current_username: this.selected[0]['username'], 
        username: this.item.username, 
        email: this.item.email, 
        password: this.item.password,
        coins: this.item.coins,
        group: this.item.group,
        mfa: {
          enabled: this.item.mfa.enabled,
          hash: this.item.mfa.hash,
          value: this.item.mfa.value
        },
        admin: this.item.admin,
        disabled: this.item.disabled
      }
      axios.put('/admin/users', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          // Edit item in the data table
          let mfa = this.item.mfa
          this.item['mfa'] = mfa['enabled']
          this.item['mfa_hash'] = mfa['mfa_hash']
          this.items.splice(i, 1, this.item)
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
    },
    deleteUserSubmit() {
      this.loading = true
      // Build payload
      const payload = { users: JSON.stringify(this.selected.map((x) => x.username)) }
      // Delete items to the DB
      axios.delete('/admin/users', { params: payload })
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          // Delete items from the data table
          while(this.selected.length > 0) {
            var s = this.selected.pop()
            for (var i = 0; i < this.items.length; ++i) {
              if (this.items[i]['username'] == s['username']) {
                // Delete Item
                this.items.splice(i, 1)
                break
              }
            }
          }
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
    },
    onMFAChange(val) {
      if (val && !this.item.mfa.origin && this.item.mfa.uri == null) this.getMFA()
    },
    getMFA() {
      const payload = {
        username: this.item.username
      } 
      axios.get('/admin/users/mfa', { params: payload })
        .then((response) => {
          this.item.mfa.hash = response.data['mfa_hash']
          this.item.mfa.uri = response.data['mfa_uri']
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
    },
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
    filterBy(val) {
      this.filter = val
      if (val == 'all') this.items = this.users.slice(0)
      else if (val == 'enabled') this.items = this.users.filter(x => !x.disabled)
      else if (val == 'disabled') this.items = this.users.filter(x => x.disabled)
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