<template>
  <div>      
    <v-data-table v-model="selected" :headers="computedHeaders" :items="items" :search="filter.search" :loading="loading" loading-text="Loading... Please wait" item-key="id" show-select class="elevation-1" style="padding-top:3px;" mobile-breakpoint="0">
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
      <template v-slot:[`item.key`]="{ item }">
        <v-icon v-if="item.key" small color="#00b16a" style="margin-left:20px">fas fa-circle</v-icon>
        <v-icon v-else small color="#EF5354" style="margin-left:20px">fas fa-circle</v-icon>
      </template>
    </v-data-table>

    <v-dialog v-model="dialog" persistent max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:2px">{{ getIcon(mode) }}</v-icon>{{ dialog_title }}</v-toolbar-title>
          <v-divider v-if="mode != 'delete'" class="mx-3" inset vertical></v-divider>
          <v-btn v-if="mode != 'delete'" title="Create the region only for a user" :color="!item.shared ? 'primary' : '#779ecb'" @click="item.shared = false" style="margin-right:10px;"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-user</v-icon>Personal</v-btn>
          <v-btn v-if="mode != 'delete'" title="Create the region for all users in a group" :color="item.shared ? 'primary' : '#779ecb'" @click="item.shared = true"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-users</v-icon>Shared</v-btn>
          <v-divider v-if="mode != 'delete'" class="mx-3" inset vertical></v-divider>
          <v-checkbox v-if="mode != 'delete'" title="Prevent this resource from being edited and hide sensible data" v-model="item.secured" flat color="white" hide-details>
            <template v-slot:label>
              <div style="color:white">Secured</div>
            </template>
          </v-checkbox>
          <v-spacer></v-spacer>
          <v-btn @click="dialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form v-if="mode != 'delete'" ref="form" style="margin-top:15px; margin-bottom:15px">
                  <v-row no-gutters style="margin-bottom:15px">
                    <v-col>
                      <v-autocomplete ref="group_id" @change="groupChanged" v-model="item.group_id" :items="groups" item-value="id" item-text="name" label="Group" :rules="[v => !!v || '']" hide-details style="padding-top:0px; margin-top:0px"></v-autocomplete>
                    </v-col>
                    <v-col v-if="!item.shared" style="margin-left:20px">
                      <v-autocomplete ref="owner_id" v-model="item.owner_id" :items="users" item-value="id" item-text="username" label="Owner" :rules="[v => !!v || '']" hide-details style="padding-top:0px; margin-top:0px"></v-autocomplete>
                    </v-col>
                  </v-row>
                  <v-text-field ref="name" v-model="item.name" :rules="[v => !!v || '']" label="Name" required></v-text-field>
                  <v-switch @click="sshtunnelClick" v-model="item.ssh_tunnel" label="SSH Tunnel" color="info" hide-details style="margin-top:0px;"></v-switch>
                  <div v-if="item.ssh_tunnel" style="margin-top:25px">
                    <v-row no-gutters>
                      <v-col cols="9" style="padding-right:10px">
                        <v-text-field ref="hostname" v-model="item.hostname" :rules="[v => !!v || '']" label="Hostname" style="padding-top:0px;"></v-text-field>
                      </v-col>
                      <v-col cols="3" style="padding-left:10px">
                        <v-text-field v-model="item.port" :rules="[v => v == parseInt(v) || '']" label="Port" style="padding-top:0px;"></v-text-field>
                      </v-col>
                    </v-row>
                    <v-text-field v-model="item.username" :rules="[v => !!v || '']" label="Username" autocomplete="username" style="padding-top:0px;"></v-text-field>
                    <v-text-field v-model="item.password" label="Password" :type="showPassword ? 'text' : 'password'" autocomplete="new-password" style="padding-top:0px;">
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
                <div v-else>
                  <div class="subtitle-1">Are you sure you want to delete the selected regions?</div>
                  <v-card style="margin-top:15px; margin-bottom:15px">
                    <v-list>
                      <v-list-item v-for="item in selected" :key="item.id" style="min-height:35px">
                        <v-list-item-content style="padding:0px">
                          <v-list-item-title>
                            <v-icon small :title="item.shared ? item.secured ? 'Shared (Secured)' : 'Shared' : item.secured ? 'Personal (Secured)' : 'Personal'" :color="item.shared ? '#EB5F5D' : 'warning'" :style="`margin-bottom:2px; ${!item.secured ? 'padding-right:8px' : ''}`">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                            <v-icon v-if="item.secured" :title="item.shared ? 'Shared (Secured)' : 'Personal (Secured)'" :color="item.shared ? '#EB5F5D' : 'warning'" style="font-size:12px; padding-left:2px; padding-top:2px; padding-right:8px">fas fa-lock</v-icon>
                            {{ item.name }}
                          </v-list-item-title>
                        </v-list-item-content>
                      </v-list-item>
                    </v-list>
                  </v-card>
                  <v-checkbox v-model="dialogConfirm" label="I confirm I want to delete the selected regions." hide-details class="body-1" style="margin-bottom:15px"></v-checkbox>
                </div>
                <v-divider></v-divider>
                <v-row no-gutters style="margin-top:20px;">
                  <v-col cols="auto" class="mr-auto">
                    <v-btn :disabled="mode == 'delete' && !dialogConfirm" :loading="loading" color="#00b16a" @click="submitRegion()">CONFIRM</v-btn>
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
                  <v-checkbox v-model="columnsRaw" label="Group" value="group" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Owner" value="owner" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Created By" value="created_by" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Created At" value="created_at" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Updated By" value="updated_by" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Updated At" value="updated_at" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Servers" value="servers" hide-details style="margin-top:5px"></v-checkbox>
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
import axios from 'axios'
import moment from 'moment'

export default {
  data: () => ({
    // Data Table
    headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'SSH Tunnel', align: 'left', value: 'ssh_tunnel'},
      { text: 'Hostname', align: 'left', value: 'hostname'},
      { text: 'Port', align: 'left', value: 'port'},
      { text: 'Username', align: 'left', value: 'username'},
      { text: 'Group', align: 'left', value: 'group' },
      { text: 'Owner', align: 'left', value: 'owner' },
      { text: 'Created By', align: 'left', value: 'created_by' },
      { text: 'Created At', align: 'left', value: 'created_at' },
      { text: 'Updated By', align: 'left', value: 'updated_by' },
      { text: 'Updated At', align: 'left', value: 'updated_at' },
      { text: 'Servers', align: 'left', value: 'servers' },
    ],
    regions: [],
    items: [],
    selected: [],
    item: { group_id: '', owner_id: '', name: '', ssh_tunnel: false, hostname: null, port: null, username: null, password: null, key: null, shared: false, secured: false },
    mode: '',
    loading: true,
    dialog: false,
    dialog_title: '',
    dialogConfirm: false,
    users: [],
    showPassword: false,
    // Filter Columns Dialog
    columnsDialog: false,
    columns: ['name','ssh_tunnel','hostname','port','username','shared','group','owner'],
    columnsRaw: [],
  }),
  props: ['tab','groups','filter'],
  mounted() {
    EventBus.$on('get-regions', this.getRegions);
    EventBus.$on('filter-regions', this.filterRegions);
    EventBus.$on('filter-region-columns', this.filterRegionColumns);
    EventBus.$on('new-region', this.newRegion);
    EventBus.$on('clone-region', this.cloneRegion);
    EventBus.$on('edit-region', this.editRegion);
    EventBus.$on('delete-region', this.deleteRegion);
  },
  destroyed() {
    EventBus.$off()
  },
  computed: {
    computedHeaders() { return this.headers.filter(x => this.columns.includes(x.value)) }
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
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    getRegions() {
      this.loading = true
      const payload = (this.filter.by == 'group' && this.filter.group != null) ? { group_id: this.filter.group } : (this.filter.by == 'user' && this.filter.user != null) ? { user_id: this.filter.user } : {}
      axios.get('/admin/inventory/regions', { params: payload})
        .then((response) => {
          response.data.regions.map(x => {
            x['created_at'] = this.dateFormat(x['created_at'])
            x['updated_at'] = this.dateFormat(x['updated_at'])
          })
          this.regions = response.data.regions
          this.items = response.data.regions
          this.filterBy()
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    newRegion() {
      this.mode = 'new'
      this.users = []
      this.item = { group_id: this.filter.group, owner_id: '', name: '', ssh_tunnel: false, hostname: null, port: '22', username: null, password: null, key: null, shared: false, secured: false }
      if (this.filter.group != null) this.getUsers()
      this.dialog_title = 'NEW REGION'
      this.dialog = true
    },
    cloneRegion() {
      this.mode = 'clone'
      this.users = []
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.getUsers()
      this.dialog_title = 'CLONE REGION'
      this.dialog = true
    },
    editRegion() {
      this.mode = 'edit'
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.getUsers()
      this.dialog_title = 'EDIT REGION'
      this.dialog = true
    },
    deleteRegion() {
      this.mode = 'delete'
      this.dialog_title = 'DELETE REGIONS'
      this.dialogConfirm = false
      this.selected.sort((a, b) => a.name.localeCompare(b.name))
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
      axios.post('/admin/inventory/regions', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getRegions()
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
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
      axios.put('/admin/inventory/regions', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getRegions()
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    deleteRegionSubmit() {
      this.loading = true
      // Build payload
      const payload = { regions: JSON.stringify(this.selected.map((x) => x.id)) }
      // Delete items to the DB
      axios.delete('/admin/inventory/regions', { params: payload })
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getRegions()
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
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
      const payload = {...this.item, key}
      axios.post('/admin/inventory/regions/test', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
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
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    filterBy() {
      let regions = JSON.parse(JSON.stringify(this.regions))
      // Filter by scope
      if (this.filter.scope == 'personal') regions = regions.filter(x => !x.shared)
      else if (this.filter.scope == 'shared') regions = regions.filter(x => x.shared)
      // Filter by secured
      if (this.filter.secured == 'secured') regions = regions.filter(x => x.secured)
      else if (this.filter.secured == 'not_secured') regions = regions.filter(x => !x.secured)
      // Assign filter
      this.items = regions
    },
    filterRegions() {
      this.selected = []
      if (this.filter.group != null) this.columns = this.columns.filter(x => x != 'group')
      else if (!this.columns.some(x => x == 'group')) this.columns.push('group')
      this.getRegions()
    },
    filterRegionColumns() {
      this.columnsRaw = [...this.columns]
      this.columnsDialog = true
    },
    selectAllColumns() {
      this.columnsRaw = ['name','ssh_tunnel','hostname','port','username','shared','group','owner','created_by','created_at','updated_by','updated_at','servers']
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
    getIcon(mode) {
      if (mode == 'new') return 'fas fa-plus'
      if (mode == 'edit') return 'fas fa-feather-alt'
      if (mode == 'delete') return 'fas fa-minus'
      if (mode == 'clone') return 'fas fa-clone'
    },
    sshtunnelClick(val) {
      requestAnimationFrame(() => {
        if (val && typeof this.$refs.hostname !== 'undefined' && !this.readonly) this.$refs.hostname.focus()
      })
    },
    notification(message, color, persistent=false) {
      EventBus.$emit('notification', message, color, persistent)
    }
  },
  watch: {
    dialog (val) {
      if (!val) return
      this.showPassword = false
      requestAnimationFrame(() => {
        if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
        if (this.mode == 'new') {
          if (this.filter.group == null) this.$refs.group_id.focus()
          else this.$refs.name.focus()
        }
        else if (['clone','edit'].includes(this.mode)) this.$refs.name.focus()
      })
    },
    selected(val) {
      EventBus.$emit('change-selected', val)
    },
    tab(val) {
      this.selected = []
      if (val == 1) this.getRegions()
    }
  }
}
</script> 