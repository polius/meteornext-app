<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">USERS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text @click="newUser()"><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn v-if="selected.length == 1" text @click="editUser()"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
          <v-btn v-if="selected.length > 0" text @click="deleteUser()"><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
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
          <v-icon v-if="item.mfa" :title="`MFA Enabled (${item.mfa == '2fa' ? 'Virtual 2FA Device' : 'Security Key'})`" small color="#00b16a" style="margin-left:4px;">fas fa-lock</v-icon>
          <v-icon v-else small title="MFA Disabled" color="error" style="margin-left:4px;">fas fa-unlock</v-icon>
        </template>
        <template v-slot:[`item.admin`]="{ item }">
          <v-icon v-if="item.admin" title="Admin User" small color="#00b16a" style="margin-left:8px; font-size:16px">fas fa-user-shield</v-icon>
          <v-icon v-else small title="Regular User" color="error" style="margin-left:9px; font-size:17px">fas fa-user</v-icon>
        </template>
        <template v-slot:[`item.created_at`]="{ item }">
          <span>{{ item.created_at }}</span>
        </template>
        <template v-slot:[`item.last_login`]="{ item }">
          <span>{{ item.last_login }}</span>
        </template>
        <template v-slot:[`item.last_ping`]="{ item }">
          <v-icon v-if="isOnline(item.last_ping)" :title="lastOnline(item)" small color="#00b16a" style="margin-left:8px;">fas fa-circle</v-icon>
          <v-icon v-else :title="lastOnline(item)" small color="error" style="margin-left:8px;">fas fa-circle</v-icon>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="dialog" persistent max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1">{{ dialog_title }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="dialog = false"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 20px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" v-model="dialog_valid" v-if="mode!='delete'" style="margin-top:15px; margin-bottom:20px;">
                  <v-alert v-if="mode == 'edit' && selected.length == 1 && item.group != selected[0]['group']" type="warning" dense dismissible icon="mdi-alert">This user will lose access to the shared inventory from the previous group.</v-alert>
                  <v-text-field ref="field" v-model="item.username" :rules="[v => !!v || '']" label="Username" required ></v-text-field>
                  <v-text-field v-model="item.email" :rules="[v => !!v || '', v => /.+@.+\..+/.test(v) || '']" label="Email" type="email" required style="padding-top:0px;"></v-text-field>
                  <v-text-field v-model="item.password" :rules="[v => !!v || '']" label="Password" type="password" required style="padding-top:0px;"></v-text-field>                  <v-text-field v-model="item.coins" :rules="[v => v == parseInt(v) && v >= 0 || '']" label="Coins" required style="padding-top:0px;"></v-text-field>
                  <v-autocomplete v-model="item.group" :items="groups" :rules="[v => !!v || '']" label="Group" required hide-details style="padding-top:0px; margin-bottom:20px;"></v-autocomplete>
                  <v-switch v-model="item.admin" label="Administrator" color="info" style="margin-top:10px;" hide-details></v-switch>
                  <v-switch v-model="item.disabled" label="Disable Account" color="error" style="margin-top:10px;" hide-details></v-switch>
                </v-form>
                <div style="padding-top:10px; padding-bottom:10px" v-if="mode=='delete'" class="subtitle-1">Are you sure you want to delete the selected users?</div>
                <v-alert v-if="mode=='delete'" type="error" dense>All selected users related data (deployments, client, inventory) will be deleted.</v-alert>
                <v-divider></v-divider>
                <v-row no-gutters style="margin-top:20px;">
                  <v-col cols="auto" class="mr-auto">
                    <v-btn :loading="loading" color="#00b16a" @click="submitUser()">Confirm</v-btn>
                    <v-btn :disabled="loading" color="error" @click="dialog=false" style="margin-left:5px">Cancel</v-btn>
                  </v-col>
                  <v-col cols="auto">
                    <v-btn v-if="mode == 'edit'" :disabled="loading" @click="mfaDialog = true" color="info">Manage MFA</v-btn>
                  </v-col>
                </v-row>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <MFA :enabled="mfaDialog" @update="mfaDialog = $event" mode="admin" :dialog="dialog" :user="{'username': mfaUsername}"/>

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
import MFA from './../../mfa/MFA'

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
      { text: 'Online', align: 'left', value: 'last_ping'},
    ],
    users: [],
    items: [],
    selected: [],
    search: '',
    item: { username: '', email: '', password: '', coins: '', group: '', admin: false, disabled: false },
    mode: '',
    loading: true,
    dialog: false,
    dialog_title: '',
    dialog_valid: false,
    // User Groups
    groups: [],
    // Dialogs
    mfaDialog: false,
    passwordDialog: false,
    mfaUsername: '',
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(4000),
    snackbarText: '',
    snackbarColor: ''
  }),
  components: { MFA },
  created() {
    this.getUsers()
    moment.relativeTimeThreshold('ss', 0)
  },
  methods: {
    getUsers() {
      axios.get('/admin/users')
        .then((response) => {
          const data = response.data.data.users.map(x => ({...x, created_at: this.dateFormat(x.created_at), last_login: this.dateFormat(x.last_login), last_ping: this.dateFormat(x.last_ping)}))
          this.users = JSON.parse(JSON.stringify(data))
          this.items = JSON.parse(JSON.stringify(data))
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
      this.item = { username: '', email: '', password: '', coins: '', group: '', admin: false, disabled: false }
      this.mfaUsername = ''
      this.dialog_title = 'NEW USER'
      this.dialog = true
    },
    editUser() {
      this.mode = 'edit'
      let item = JSON.parse(JSON.stringify(this.selected[0]))
      this.item = item
      this.mfaUsername = item.username
      this.dialog_title = 'EDIT USER'
      this.dialog = true
    },
    deleteUser() {
      this.mode = 'delete'
      this.dialog_title = 'DELETE USER'
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
        admin: this.item.admin,
        disabled: this.item.disabled
      }
      axios.put('/admin/users', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          // Retrieve again the users list
          this.getUsers()
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
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
    isOnline(last_ping) {
      if (last_ping == null) return false
      return moment(last_ping).add(70,'seconds') >= moment.utc()
    },
    lastOnline(item) {
      if (item['last_login'] == null) return 'not logged in'
      if (item['last_ping'] == null) return moment(item['last_login']).fromNow()
      return moment(item['last_ping']).fromNow()
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