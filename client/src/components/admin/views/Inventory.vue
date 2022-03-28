<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="body-2 white--text font-weight-medium" style="min-width:104px; font-size:0.9rem!important"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-layer-group</v-icon>INVENTORY</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items>
          <v-menu offset-y>
            <template v-slot:activator="{ attrs, on }">
              <v-btn color="primary" v-bind="attrs" v-on="on" class="elevation-0"><v-icon small style="margin-right:10px">fas fa-mouse-pointer</v-icon>{{ tab == 0 ? 'SERVERS' : tab == 1 ? 'REGIONS' : tab == 2 ? 'ENVIRONMENTS' : tab == 3 ? 'AUXILIARY' : tab == 4 ? 'CLOUD KEYS' : '' }}</v-btn>
            </template>
            <v-list-item-group @change="changeTab" v-model="tab">
              <v-list style="padding:0px">
                <v-list-item v-for="item in ['servers','regions','environments','auxiliary','cloud keys']" :key="item" link>
                  <v-list-item-title v-text="item.toUpperCase()" class="text-subtitle-2"></v-list-item-title>
                </v-list-item>
              </v-list>
            </v-list-item-group>
          </v-menu>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="filterClick" text :style="{ backgroundColor : filterApplied ? '#4ba1f1' : '' }"><v-icon small style="padding-right:10px">fas fa-sliders-h</v-icon>FILTER</v-btn>
          <v-btn @click="refreshClick" text><v-icon small style="margin-right:10px">fas fa-sync-alt</v-icon>REFRESH</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="newClick" text><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn :disabled="selected.length != 1" @click="editClick" text><v-icon small style="padding-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
          <v-btn :disabled="selected.length != 1" @click="cloneClick" text><v-icon small style="padding-right:10px">fas fa-clone</v-icon>CLONE</v-btn>
          <v-btn :disabled="selected.length == 0" @click="deleteClick" text><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
        </v-toolbar-items>
        <v-text-field v-model="filter.search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
        <v-divider class="mx-3" inset vertical style="margin-right:4px!important"></v-divider>
        <v-btn @click="filterColumnsClick" icon title="Show/Hide columns" style="margin-right:-10px; width:40px; height:40px;"><v-icon small>fas fa-cog</v-icon></v-btn>
      </v-toolbar>
      <Servers v-show="tab == 0" :tab="tab" :groups="groups" :filter="filter"/>
      <Regions v-show="tab == 1" :tab="tab" :groups="groups" :filter="filter"/>
      <Environments v-show="tab == 2" :tab="tab" :groups="groups" :filter="filter"/>
      <Auxiliary v-show="tab == 3" :tab="tab" :groups="groups" :filter="filter"/>
      <Cloud v-show="tab == 4" :tab="tab" :groups="groups" :filter="filter"/>
    </v-card>
    <!------------------->
    <!-- FILTER DIALOG -->
    <!------------------->
    <v-dialog v-model="dialog" persistent max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="padding-right:10px; padding-bottom:1px">fas fa-sliders-h</v-icon>FILTER</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="dialog = false"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 15px 0px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" @submit.prevent style="margin-top:15px; margin-bottom:15px;">
                  <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px">RESOURCE</div>
                  <v-radio-group v-model="filter.by" dense row hide-details style="margin-top:0px; margin-bottom:15px; padding-top:2px">
                    <v-radio label="User" value="user"></v-radio>
                    <v-radio label="Group" value="group"></v-radio>
                  </v-radio-group>
                  <v-autocomplete v-if="filter.by == 'user'" ref="filter_user" v-model="filter.user" v-on:keyup.enter="filterInventory()" filled :items="users" item-value="id" item-text="username" label="User" auto-select-first :rules="[v => !!v || '']" hide-details style="padding-top:0px; margin-bottom:20px">
                    <template v-slot:item="{ item }" >
                      <v-row align="center" no-gutters>
                        <v-col class="flex-grow-1 flex-shrink-1">
                          {{ item.username }}
                        </v-col>
                        <v-col cols="auto" class="flex-grow-0 flex-shrink-0">
                          <v-chip label>{{ item.group }}</v-chip>
                        </v-col>
                      </v-row>
                    </template>
                  </v-autocomplete>
                  <v-autocomplete v-else-if="filter.by == 'group'" ref="filter_group" v-model="filter.group" v-on:keyup.enter="filterInventory()" filled :items="groups" item-value="id" item-text="name" label="Group" auto-select-first :rules="[v => !!v || '']" hide-details style="padding-top:0px; margin-bottom:20px"></v-autocomplete>
                  <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px">SCOPE</div>
                  <v-radio-group v-model="filter.scope" hide-details style="margin-top:0px; margin-bottom:15px; padding-top:2px">
                    <v-radio label="All" value="all"></v-radio>
                    <v-radio label="Personal" value="personal" color="#fb8c00"></v-radio>
                    <v-radio label="Shared" value="shared" color="#eb5f5d"></v-radio>
                  </v-radio-group>
                  <div class="subtitle-1 font-weight-regular white--text" style="margin-bottom:10px">SECURED</div>
                  <v-radio-group v-model="filter.secured" hide-details style="margin-top:0px; margin-bottom:15px; padding-top:2px">
                    <v-radio label="All" value="all"></v-radio>
                    <v-radio label="Secured" value="secured"></v-radio>
                    <v-radio label="Not Secured" value="not_secured"></v-radio>
                  </v-radio-group>
                  <v-divider></v-divider>
                  <div style="margin-top:20px;">
                    <v-btn :loading="loading" color="#00b16a" @click="filterInventory()">Confirm</v-btn>
                    <v-btn :disabled="loading" color="#EF5354" @click="dialog = false" style="margin-left:5px;">Cancel</v-btn>
                    <v-btn v-if="filterApplied" :disabled="loading" color="info" @click="clearFilter()" style="float:right;">Remove Filter</v-btn>
                  </div>
                </v-form>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!-------------->
    <!-- SNACKBAR -->
    <!-------------->
    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script>
import EventBus from '../js/event-bus'
import axios from 'axios'
import Environments from './inventory/Environments'
import Regions from './inventory/Regions'
import Servers from './inventory/Servers'
import Auxiliary from './inventory/Auxiliary'
import Cloud from './inventory/Cloud'

export default {
  data() {
    return {
      tab: null,
      selected: [],
      // Filter Dialog
      dialog: false,
      loading: false,
      groups: [],
      users: [],
      filter: { by: 'user', search: '', group: null, user: null, scope: 'all', secured: 'all' },
      filterApplied: false,
      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarText: '',
      snackbarColor: ''
    }
  },
  components: { Environments, Regions, Servers, Auxiliary, Cloud },
  created() {
    this.getGroups()
    this.getUsers()
  },
  mounted() {
    EventBus.$on('init-columns', this.initColumns)
    EventBus.$on('notification', this.notification)
    EventBus.$on('change-selected', this.changeSelected)
    EventBus.$on('notification', this.notification)
    if (this.$route.path.startsWith('/admin/inventory/servers')) this.tab = 0
    else if (this.$route.path.startsWith('/admin/inventory/regions')) this.tab = 1
    else if (this.$route.path.startsWith('/admin/inventory/environments')) this.tab = 2
    else if (this.$route.path.startsWith('/admin/inventory/auxiliary')) this.tab = 3
    else if (this.$route.path.startsWith('/admin/inventory/cloud')) this.tab = 4
    else {
      this.$router.push('/admin/inventory/servers')
      this.tab = 0
    }
  },
  methods: {
    changeTab(val) {
      if (val == 0) this.$router.push("/admin/inventory/servers")
      if (val == 1) this.$router.push("/admin/inventory/regions")
      if (val == 2) this.$router.push("/admin/inventory/environments")
      if (val == 3) this.$router.push("/admin/inventory/auxiliary")
      if (val == 4) this.$router.push("/admin/inventory/cloud")
    },
    getGroups() {
      axios.get('/admin/inventory/groups')
        .then((response) => {
          this.groups = response.data.groups
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    getUsers() {
      axios.get('/admin/inventory/users')
        .then((response) => {
          this.users = response.data.users
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    refreshClick() {
      if (this.tab == 0) EventBus.$emit('get-servers')
      else if (this.tab == 1) EventBus.$emit('get-regions')
      else if (this.tab == 2) EventBus.$emit('get-environments')
      else if (this.tab == 3) EventBus.$emit('get-auxiliary')
      else if (this.tab == 4) EventBus.$emit('get-cloud')
    },
    newClick() {
      if (this.tab == 0) EventBus.$emit('new-server')
      else if (this.tab == 1) EventBus.$emit('new-region')
      else if (this.tab == 2) EventBus.$emit('new-environment')
      else if (this.tab == 3) EventBus.$emit('new-auxiliary')
      else if (this.tab == 4) EventBus.$emit('new-cloud')
    },
    cloneClick() {
      if (this.tab == 0) EventBus.$emit('clone-server')
      else if (this.tab == 1) EventBus.$emit('clone-region')
      else if (this.tab == 2) EventBus.$emit('clone-environment')
      else if (this.tab == 3) EventBus.$emit('clone-auxiliary')
      else if (this.tab == 4) EventBus.$emit('clone-cloud')
    },
    editClick() {
      if (this.tab == 0) EventBus.$emit('edit-server')
      else if (this.tab == 1) EventBus.$emit('edit-region')
      else if (this.tab == 2) EventBus.$emit('edit-environment')
      else if (this.tab == 3) EventBus.$emit('edit-auxiliary')
      else if (this.tab == 4) EventBus.$emit('edit-cloud')
    },
    deleteClick() {
      if (this.tab == 0) EventBus.$emit('delete-server')
      else if (this.tab == 1) EventBus.$emit('delete-region')
      else if (this.tab == 2) EventBus.$emit('delete-environment')
      else if (this.tab == 3) EventBus.$emit('delete-auxiliary')
      else if (this.tab == 4) EventBus.$emit('delete-cloud')
    },
    filterColumnsClick() {
      if (this.tab == 0) EventBus.$emit('filter-server-columns')
      else if (this.tab == 1) EventBus.$emit('filter-region-columns')
      else if (this.tab == 2) EventBus.$emit('filter-environment-columns')
      else if (this.tab == 3) EventBus.$emit('filter-auxiliary-columns')
      else if (this.tab == 4) EventBus.$emit('filter-cloud-columns')
    },
    filterClick() {
      this.filter_by = 'group'
      this.dialog = true
    },
    filterInventory() {
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
        this.loading = false
        return
      }
      if (this.tab == 0) EventBus.$emit('filter-servers')
      else if (this.tab == 1) EventBus.$emit('filter-regions')
      else if (this.tab == 2) EventBus.$emit('filter-environments')
      else if (this.tab == 3) EventBus.$emit('filter-auxiliary')
      else if (this.tab == 4) EventBus.$emit('filter-cloud')
      this.filterApplied = true
      this.dialog = false
    },
    clearFilter() {
      this.filter = { by: 'user', search: '', group: null, user: null, scope: 'all', secured: 'all' }
      this.$nextTick(() => {
        if (this.tab == 0) EventBus.$emit('filter-servers')
        else if (this.tab == 1) EventBus.$emit('filter-regions')
        else if (this.tab == 2) EventBus.$emit('filter-environments')
        else if (this.tab == 3) EventBus.$emit('filter-auxiliary')
        else if (this.tab == 4) EventBus.$emit('filter-cloud')
      })
      this.filterApplied = false
      this.dialog = false
    },
    changeSelected(val) {
      this.selected = val
    },
    notification(message, color, persistent=false) {
      this.snackbarText = message
      this.snackbarColor = color
      this.snackbarTimeout = persistent ? Number(0) : Number(3000)
      this.snackbar = true
    }
  },
  watch: {
    tab: function (newValue, oldValue) {
      if (newValue === undefined) this.tab = oldValue
    },
    dialog (val) {
      if (!val) return
      if (!this.filterApplied) this.filter = { by: 'user', search: '', group: null, scope: 'all', secured: 'all' }
      requestAnimationFrame(() => {
        if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
        if (typeof this.$refs.filter_user !== 'undefined' && this.filter.by == 'user') this.$refs.filter_user.focus()
      })
    },
    'filter.by': function() {
      this.$refs.form.resetValidation()
    },
  },
}
</script>