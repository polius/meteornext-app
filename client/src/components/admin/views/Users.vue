<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="body-2 white--text font-weight-medium" style="font-size:0.9rem!important"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-user</v-icon>USERS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items>
          <v-btn text @click="newUser()"><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn :disabled="selected.length != 1" text @click="editUser()"><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
          <v-btn :disabled="selected.length == 0" text @click="deleteUser()"><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="getUsers" text><v-icon small style="margin-right:10px">fas fa-sync-alt</v-icon>REFRESH</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn text class="body-2" @click="filterBy('all')" :style="filter == 'all' ? 'font-weight:600' : 'font-weight:400'">ALL</v-btn>
          <v-btn text class="body-2" @click="filterBy('enabled')" :style="filter == 'enabled' ? 'font-weight:600' : 'font-weight:400'">ENABLED</v-btn>
          <v-btn text class="body-2" @click="filterBy('disabled')" :style="filter == 'disabled' ? 'font-weight:600' : 'font-weight:400'">DISABLED</v-btn>
        </v-toolbar-items>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
        <v-divider class="mx-3" inset vertical style="margin-right:4px!important"></v-divider>
        <v-btn @click="openColumnsDialog" icon title="Show/Hide columns" style="margin-right:-10px; width:40px; height:40px;"><v-icon small>fas fa-cog</v-icon></v-btn>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="computedHeaders" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="username" show-select class="elevation-1" style="padding-top:3px;" mobile-breakpoint="0">
        <template v-ripple v-slot:[`header.data-table-select`]="{}">
          <v-simple-checkbox
            :value="items.length == 0 ? false : selected.length == items.length"
            :indeterminate="selected.length > 0 && selected.length != items.length"
            @click="selected.length == items.length ? selected = [] : selected = [...items]">
          </v-simple-checkbox>
        </template>
        <template v-slot:[`item.mfa`]="{ item }">
          <v-icon v-if="item.mfa" :title="`MFA Enabled (${item.mfa == '2fa' ? 'Virtual 2FA Device' : 'Security Key'})`" small color="#00b16a" style="margin-left:4px;">fas fa-lock</v-icon>
          <v-icon v-else small title="MFA Disabled" color="#EF5354" style="margin-left:4px;">fas fa-unlock</v-icon>
        </template>
        <template v-slot:[`item.admin`]="{ item }">
          <v-icon small :title="item.admin ? 'Admin User' : 'Regular User'" :color="item.admin ? '#00b16a' : '#EF5354'" style="margin-left:8px; font-size:17px">fas fa-shield-alt</v-icon>
        </template>
        <template v-slot:[`item.last_ping`]="{ item }">
          <v-icon v-if="isOnline(item.last_ping)" :title="lastOnline(item)" small color="#00b16a" style="margin-left:8px;">fas fa-circle</v-icon>
          <v-icon v-else :title="lastOnline(item)" small color="#EF5354" style="margin-left:8px;">fas fa-circle</v-icon>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="dialog" persistent max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:2px">{{ getIcon(mode) }}</v-icon>{{ dialog_title }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="dialog = false"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" v-model="dialog_valid" v-if="mode!='delete'" style="margin-bottom:20px;">
                  <v-alert v-if="mode == 'edit' && selected.length == 1 && item.group != selected[0]['group']" color="#fb8c00" dense><v-icon style="font-size:16px; margin-bottom:2px; margin-right:10px">fas fa-exclamation-triangle</v-icon>This user will lose access to the shared inventory from the previous group.</v-alert>
                  <v-text-field ref="field" v-model="item.username" :rules="[v => !!v || '']" label="Username" autocomplete="email" required></v-text-field>
                  <v-text-field v-model="item.email" :rules="[v => !!v || '', v => /.+@.+\..+/.test(v) || '']" label="Email" type="email" required autocomplete="username" style="padding-top:0px;"></v-text-field>
                  <v-text-field v-model="item.password" :rules="[v => !!v || mode == 'edit' || '']" :label="mode == 'new' ? 'Password' : 'New Password'" :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'" :type="showPassword ? 'text' : 'password'" @click:append="showPassword = !showPassword" autocomplete="new-password" style="padding-top:0px;"></v-text-field>
                  <v-text-field v-model="item.coins" :rules="[v => v == parseInt(v) && v >= 0 || '']" label="Coins" required style="padding-top:0px;"></v-text-field>
                  <v-autocomplete v-model="item.group" :items="groups" :rules="[v => !!v || '']" label="Group" required hide-details style="padding-top:0px; margin-bottom:20px;"></v-autocomplete>
                  <v-checkbox v-model="item.admin" label="Administrator" color="info" style="margin-top:10px;" hide-details></v-checkbox>
                  <v-checkbox v-model="item.disabled" label="Disable Account" color="#EF5354" style="margin-top:10px;" hide-details></v-checkbox>
                  <v-switch v-model="item.change_password" label="Force user to change password at next login" color="#fa8231" style="margin-top:10px" hide-details></v-switch>
                </v-form>
                <div v-if="mode == 'delete'">
                  <div class="subtitle-1">Are you sure you want to delete the selected users?</div>
                  <v-card style="margin-top:15px; margin-bottom:15px">
                    <v-list>
                      <v-list-item v-for="item in selected" :key="item.username" style="min-height:35px">
                        <v-list-item-content style="padding:0px">
                          <v-list-item-title>{{ item.username }}</v-list-item-title>
                        </v-list-item-content>
                      </v-list-item>
                    </v-list>
                  </v-card>
                  <v-checkbox v-model="dialog_confirm" label="I confirm I want to delete the selected users." hide-details class="body-1" style="margin-bottom:15px"></v-checkbox>
                </div>
                <v-divider></v-divider>
                <v-row no-gutters style="margin-top:20px;">
                  <v-col cols="auto" class="mr-auto">
                    <v-btn :disabled="mode == 'delete' && !dialog_confirm" :loading="loading" color="#00b16a" @click="submitUser()">Confirm</v-btn>
                    <v-btn :disabled="loading" color="#EF5354" @click="dialog=false" style="margin-left:5px">Cancel</v-btn>
                  </v-col>
                  <v-col cols="auto">
                    <v-btn v-if="mode == 'edit'" :disabled="(selected.length == 1 && selected[0]['disabled'] == 1) || loading" @click="mfaDialog = true" color="info">Manage MFA</v-btn>
                  </v-col>
                </v-row>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <MFA :enabled="mfaDialog" @update="mfaDialog = $event" mode="admin" :dialog="dialog" :user="{'username': mfaUsername}"/>

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
                  <v-checkbox v-model="columnsRaw" label="Username" value="username" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Group" value="group" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Email" value="email" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Created By" value="created_by" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Created At" value="created_at" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Updated By" value="updated_by" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Updated At" value="updated_at" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Last Login" value="last_login" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="IP" value="ip" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="User Agent" value="user_agent" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Coins" value="coins" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="MFA" value="mfa" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Admin" value="admin" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Online" value="last_ping" hide-details style="margin-top:5px"></v-checkbox>
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
import moment from 'moment';
import MFA from './../../mfa/MFA'

export default {
  data: () => ({
    // Data Table
    now: moment.utc(),
    filter: 'all',
    headers: [
      { text: 'Username', align: 'left', value: 'username' },
      { text: 'Group', align: 'left', value: 'group' },
      { text: 'Email', align: 'left', value: 'email'},
      { text: 'IP', align: 'left', value: 'ip'},
      { text: 'User Agent', align: 'left', value: 'user_agent'},
      { text: 'Created By', align: 'left', value: 'created_by'},
      { text: 'Created At', align: 'left', value: 'created_at'},
      { text: 'Updated By', align: 'left', value: 'updated_by'},
      { text: 'Updated At', align: 'left', value: 'updated_at'},
      { text: 'Last Login', align: 'left', value: 'last_login'},
      { text: 'Coins', align: 'left', value: 'coins'},
      { text: 'MFA', align: 'left', value: 'mfa'},
      { text: 'Admin', align: 'left', value: 'admin'},
      { text: 'Online', align: 'left', value: 'last_ping'},
    ],
    users: [],
    items: [],
    selected: [],
    search: '',
    item: { username: '', email: '', password: '', coins: '', group: '', admin: false, disabled: false, change_password: false },
    mode: '',
    loading: true,
    dialog: false,
    dialog_title: '',
    dialog_valid: false,
    dialog_confirm: false,
    showPassword: false,
    // User Groups
    groups: [],
    // Dialogs
    mfaDialog: false,
    mfaUsername: '',
    // Filter Columns Dialog
    columnsDialog: false,
    columns: ['username','group','email','created_at','last_login','coins','mfa','admin','last_ping'],
    columnsRaw: [],
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  components: { MFA },
  created() {
    this.getUsers()
    moment.relativeTimeThreshold('ss', 0)
  },
  computed: {
    computedHeaders() { return this.headers.filter(x => this.columns.includes(x.value)) },
  },
  methods: {
    getUsers() {
      this.loading = true
      axios.get('/admin/users')
        .then((response) => {
          const data = response.data.data.users.map(x => ({...x, created_at: this.dateFormat(x.created_at), updated_at: this.dateFormat(x.updated_at), last_login: this.dateFormat(x.last_login), last_ping: this.dateFormat(x.last_ping)}))
          this.users = [...data]
          this.items = [...data]
          this.groups = response.data.data.groups.map(x => x.name)
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    newUser() {
      this.mode = 'new'
      this.item = { username: '', email: '', password: '', coins: '', group: '', admin: false, disabled: false, change_password: false }
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
      this.dialog_title = 'DELETE USERS'
      this.dialog_confirm = false
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
        this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
        return
      }
      // Check if new item already exists
      for (var i = 0; i < this.items.length; ++i) {
        if (this.items[i]['username'] == this.item.username) {
          this.notification('This user currently exists', '#EF5354')
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
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    editUserSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
        return
      }
      // Get Item Position
      for (var i = 0; i < this.items.length; ++i) {
        if (this.items[i]['username'] == this.selected[0]['username']) break
      }
      // Check if edited item already exists
      for (var j = 0; j < this.items.length; ++j) {
        if (this.items[j]['username'] == this.item.username && this.item.username != this.selected[0]['username']) {
          this.notification('This user currently exists', '#EF5354')
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
        disabled: this.item.disabled,
        change_password: this.item.change_password
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
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
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
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
    isOnline(last_ping) {
      if (last_ping == null) return false
      return moment(last_ping).add(70,'seconds') >= this.now
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
    openColumnsDialog() {
      this.columnsRaw = [...this.columns]
      this.columnsDialog = true
    },
    selectAllColumns() {
      this.columnsRaw = ['username','group','email','created_by','created_at','updated_by','updated_at','last_login','ip','user_agent','coins','mfa','admin','last_ping']
    },
    deselectAllColumns() {
      this.columnsRaw = []
    },
    filterColumns() {
      this.columns = [...this.columnsRaw]
      this.columnsDialog = false
    },
    getIcon(mode) {
      if (mode == 'new') return 'fas fa-plus'
      if (mode == 'edit') return 'fas fa-feather-alt'
      if (mode == 'delete') return 'fas fa-minus'
      if (mode == 'clone') return 'fas fa-clone'
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