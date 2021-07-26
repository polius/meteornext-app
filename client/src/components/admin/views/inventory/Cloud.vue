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
      <template v-slot:[`item.type`]="{ item }">
          <v-icon v-if="item.type == 'aws'" size="22" color="#e47911" title="AWS">fab fa-aws</v-icon>
          <v-icon v-else-if="item.type == 'google'" size="20" color="#4285F4" title="Google Cloud" style="margin-left:4px">fab fa-google</v-icon>
        </template>
      <template v-slot:[`item.shared`]="{ item }">
        <v-icon v-if="!item.shared" small title="Personal" color="warning" style="margin-right:6px; margin-bottom:2px;">fas fa-user</v-icon>
        <v-icon v-else small title="Shared" color="#EB5F5D" style="margin-right:6px; margin-bottom:2px;">fas fa-users</v-icon>
        {{ !item.shared ? 'Personal' : 'Shared' }}
      </template>
    </v-data-table>

    <v-dialog v-model="dialog" persistent max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:2px">{{ getIcon(mode) }}</v-icon>{{ dialog_title }}</v-toolbar-title>
          <v-divider v-if="mode != 'delete'" class="mx-3" inset vertical></v-divider>
          <v-btn v-if="mode != 'delete'" title="Create the cloud key only for a user" :color="!item.shared ? 'primary' : '#779ecb'" @click="item.shared = false" style="margin-right:10px;"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-user</v-icon>Personal</v-btn>
          <v-btn v-if="mode != 'delete'" title="Create the cloud key for all users in a group" :color="item.shared ? 'primary' : '#779ecb'" @click="item.shared = true"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-users</v-icon>Shared</v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="dialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 15px 15px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" v-if="mode!='delete'" style="margin-top:20px; margin-bottom:20px">
                  <v-row v-if="mode!='delete'" no-gutters style="margin-bottom:15px">
                    <v-col>
                      <v-autocomplete ref="group_id" :readonly="mode == 'edit'" @change="groupChanged" v-model="item.group_id" :items="groups" item-value="id" item-text="name" label="Group" :rules="[v => !!v || '']" hide-details style="padding-top:0px"></v-autocomplete>
                    </v-col>
                    <v-col v-if="!item.shared" style="margin-left:20px">
                      <v-autocomplete ref="owner_id" v-model="item.owner_id" :items="users" item-value="id" item-text="username" label="Owner" :rules="[v => !!v || '']" hide-details style="padding-top:0px"></v-autocomplete>
                    </v-col>
                  </v-row>
                  <v-text-field ref="name" v-model="item.name" :rules="[v => !!v || '']" label="Name" required></v-text-field>
                  <v-select v-model="item.type" :items="[{id: 'aws', name: 'AWS'}, {id: 'google', name: 'Google Cloud'}]" item-value="id" :rules="[v => !!v || '']" label="Type" required style="padding-top:0px;">
                    <template v-slot:[`selection`]="{ item }">
                      <v-icon v-if="item.id == 'aws'" size="22" color="#e47911" style="margin-right:8px">fab fa-aws</v-icon>
                      <v-icon v-else-if="item.id == 'google'" size="20" color="#4285F4" style="margin-right:8px">fab fa-google</v-icon>
                      {{ item.id == 'aws' ? 'AWS' : 'Google Cloud' }}
                    </template>
                    <template v-slot:[`item`]="{ item }">
                      <v-icon v-if="item.id == 'aws'" size="22" color="#e47911" style="margin-right:8px">fab fa-aws</v-icon>
                      <v-icon v-else-if="item.id == 'google'" size="20" color="#4285F4" style="margin-left:4px; margin-right:12px">fab fa-google</v-icon>
                      {{ item.id == 'aws' ? 'AWS' : 'Google Cloud' }}
                    </template>
                  </v-select>
                  <v-text-field v-model="item.access_key" :rules="[v => !!v || '']" label="Access Key" autocomplete="username" style="padding-top:0px;"></v-text-field>
                  <v-text-field v-model="item.secret_key" :rules="[v => !!v || '']" label="Secret Key" :append-icon="showSecret ? 'mdi-eye' : 'mdi-eye-off'" :type="showSecret ? 'text' : 'password'" @click:append="showSecret = !showSecret" autocomplete="new-password" style="padding-top:0px;" hide-details></v-text-field>
                </v-form>
                <div style="padding-top:10px; padding-bottom:10px" v-if="mode=='delete'" class="subtitle-1">Are you sure you want to delete the selected cloud keys?</div>
                <v-divider></v-divider>
                <v-row no-gutters style="margin-top:20px;">
                  <v-col cols="auto" class="mr-auto">
                    <v-btn :loading="loading" color="#00b16a" @click="submitCloud()">CONFIRM</v-btn>
                    <v-btn :disabled="loading" color="#EF5354" @click="dialog = false" style="margin-left:5px">CANCEL</v-btn>
                  </v-col>
                  <v-col cols="auto">
                    <v-btn v-if="mode != 'delete'" :loading="loading" color="info" @click="openTest()">Test Cloud Key</v-btn>
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
                  <v-checkbox v-model="columnsRaw" label="Type" value="type" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Access Key" value="access_key" hide-details style="margin-top:5px"></v-checkbox>
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
      { text: 'Type', align: 'left', value: 'type'},
      { text: 'Access Key', align: 'left', value: 'access_key'},
      { text: 'Scope', align: 'left', value: 'shared' },
      { text: 'Group', align: 'left', value: 'group' },
      { text: 'Owner', align: 'left', value: 'owner' },
      { text: 'Created By', align: 'left', value: 'created_by' },
      { text: 'Created At', align: 'left', value: 'created_at' },
      { text: 'Updated By', align: 'left', value: 'updated_by' },
      { text: 'Updated At', align: 'left', value: 'updated_at' },
    ],
    cloud: [],
    items: [],
    selected: [],
    search: '',
    item: { group_id: '', owner_id: '', name: '', type: '', access_key: '', shared: true },
    mode: '',
    loading: true,
    dialog: false,
    dialog_title: '',
    users: [],
    showSecret: false,
    // Test Dialog
    testDialog: false,
    testLoading: false,
    regionsItems: [],
    regionItem: null,
    // Filter Columns Dialog
    columnsDialog: false,
    columns: ['name','type','access_key','shared','group','owner'],
    columnsRaw: [],
  }),
  props: ['tab','groups','filter'],
  mounted () {
    EventBus.$on('get-cloud', this.getCloud);
    EventBus.$on('filter-cloud', this.filterCloud);
    EventBus.$on('filter-cloud-columns', this.filterCloudColumns);
    EventBus.$on('new-cloud', this.newCloud);
    EventBus.$on('clone-cloud', this.cloneCloud);
    EventBus.$on('edit-cloud', this.editCloud);
    EventBus.$on('delete-cloud', this.deleteCloud);
  },
  computed: {
    computedHeaders() { return this.headers.filter(x => this.columns.includes(x.value)) },
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
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    getCloud() {
      this.loading = true
      const payload = (this.filter.by == 'group' & this.filter.group != null) ? { group_id: this.filter.group } : (this.filter.by == 'user') ? { user_id: this.filter.user } : {}
      axios.get('/admin/inventory/cloud', { params: payload})
        .then((response) => {
          response.data.cloud.map(x => {
            x['created_at'] = this.dateFormat(x['created_at'])
            x['updated_at'] = this.dateFormat(x['updated_at'])
          })
          this.cloud = response.data.cloud
          this.items = response.data.cloud
          this.filterBy(this.filter.scope)
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    newCloud() {
      this.mode = 'new'
      this.users = []
      this.item = { group_id: this.filter.group, owner_id: '', name: '', type: '', access_key: '', shared: true }
      if (this.filter.group != null) this.getUsers()
      this.dialog_title = 'NEW CLOUD KEY'
      this.dialog = true
    },
    cloneCloud() {
      this.mode = 'clone'
      this.users = []
      this.$nextTick(() => this.item = JSON.parse(JSON.stringify(this.selected[0])))
      this.getUsers()
      this.dialog_title = 'CLONE CLOUD KEY'
      this.dialog = true
    },
    editCloud() {
      this.mode = 'edit'
      this.$nextTick(() => this.item = JSON.parse(JSON.stringify(this.selected[0])))
      this.getUsers()
      this.dialog_title = 'EDIT CLOUD KEY'
      this.dialog = true
    },
    deleteCloud() {
      this.mode = 'delete'
      this.dialog_title = 'DELETE CLOUD KEY'
      this.dialog = true
    },
    submitCloud() {
      if (['new','clone'].includes(this.mode)) this.newCloudSubmit()
      else if (this.mode == 'edit') this.editCloudSubmit()
      else if (this.mode == 'delete') this.deleteCloudSubmit()
    },
    async newCloudSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
        return
      }
      // Add item in the DB
      this.loading = true
      const payload = this.item
      axios.post('/admin/inventory/cloud', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getCloud()
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    async editCloudSubmit() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
        return
      }
      // Edit item in the DB
      this.loading = true
      const payload = this.item
      axios.put('/admin/inventory/cloud', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getCloud()
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    deleteCloudSubmit() {
      this.loading = true
      // Build payload
      const payload = { cloud: JSON.stringify(this.selected.map((x) => x.id)) }
      // Delete items to the DB
      axios.delete('/admin/inventory/cloud', { params: payload })
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getCloud()
          this.selected = []
          this.dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    filterBy(val) {
      if (val == 'all') this.items = this.cloud.slice(0)
      else if (val == 'personal') this.items = this.cloud.filter(x => !x.shared)
      else if (val == 'shared') this.items = this.cloud.filter(x => x.shared)
    },
    filterCloud() {
      this.selected = []
      if (this.filter.group != null) this.columns = this.columns.filter(x => x != 'group')
      else if (!this.columns.some(x => x == 'group')) this.columns.push('group')
      this.getCloud()
    },
    filterCloudColumns() {
      this.columnsRaw = [...this.columns]
      this.columnsDialog = true
    },
    selectAllColumns() {
      this.columnsRaw = ['name','type','access_key','shared','group','owner','created_by','created_at','updated_by','updated_at']
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
    getIcon(mode) {
      if (mode == 'new') return 'fas fa-plus'
      if (mode == 'edit') return 'fas fa-feather-alt'
      if (mode == 'delete') return 'fas fa-minus'
      if (mode == 'clone') return 'fas fa-clone'
    },
    notification(message, color, persistent=false) {
      EventBus.$emit('notification', message, color, persistent)
    }
  },
  watch: {
    dialog (val) {
      if (!val) return
      this.showSecret = false
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
      if (val == 4) this.getCloud()
    }
  }
}
</script>