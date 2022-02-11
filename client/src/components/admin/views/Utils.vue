<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="body-2 white--text font-weight-medium" style="font-size:0.9rem!important"><v-icon small style="margin-right:10px">fas fa-database</v-icon>UTILS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items>
          <v-tabs background-color="primary" color="white" v-model="tabs" slider-color="white" slot="extension">
            <v-tab title="Manage Imports"><span class="pl-2 pr-2"><v-icon small style="margin-right:10px">fas fa-arrow-up</v-icon>IMPORTS</span></v-tab>
            <v-tab title="Manage Exports"><span class="pl-2 pr-2"><v-icon small style="margin-right:10px">fas fa-arrow-down</v-icon>EXPORTS</span></v-tab>
            <v-tab title="Manage Clones"><span class="pl-2 pr-2"><v-icon small style="margin-right:10px">fas fa-clone</v-icon>CLONES</span></v-tab>
          </v-tabs>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn :disabled="rowsSelected != 1" text @click="infoClick"><v-icon small style="margin-right:10px">fas fa-bookmark</v-icon>DETAILS</v-btn>
          <v-btn :disabled="rowsSelected == 0" text @click="manageClick"><v-icon small style="margin-right:10px;">fas fa-mouse-pointer</v-icon>MANAGE</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="filterClick" text :style="{ backgroundColor : filterActive ? '#4ba1f1' : '' }"><v-icon small style="padding-right:10px">fas fa-sliders-h</v-icon>FILTER</v-btn>
          <v-btn @click="refreshClick" text ><v-icon small style="margin-right:10px">fas fa-sync-alt</v-icon>REFRESH</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
        </v-toolbar-items>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
        <v-divider class="mx-3" inset vertical style="margin-right:4px!important"></v-divider>
        <v-btn @click="columnsClick" icon title="Show/Hide columns" style="margin-right:-10px; width:40px; height:40px;"><v-icon small>fas fa-cog</v-icon></v-btn>
      </v-toolbar>
      <Imports v-show="tabs == 0" :active="tabs == 0" :search="search" />
      <Exports v-show="tabs == 1" :active="tabs == 1" :search="search" />
      <Clones v-show="tabs == 2" :active="tabs == 2" :search="search" />
    </v-card>
    <!------------------->
    <!-- SERVER DIALOG -->
    <!------------------->
    <v-dialog v-model="serverDialog" max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1">SERVER</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn readonly title="Create the server only for a user" :color="!server.shared ? 'primary' : '#779ecb'" style="margin-right:10px;"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-user</v-icon>Personal</v-btn>
          <v-btn readonly title="Create the server for all users in a group" :color="server.shared ? 'primary' : '#779ecb'"><v-icon small style="margin-bottom:2px; margin-right:10px">fas fa-users</v-icon>Shared</v-btn>
          <v-spacer></v-spacer>
          <v-btn @click="serverDialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-progress-linear v-show="loading" indeterminate></v-progress-linear>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:15px;">
                  <v-row no-gutters style="margin-bottom:15px">
                    <v-col>
                      <v-text-field readonly v-model="server.group" label="Group" hide-details style="padding-top:0px; margin-top:0px"></v-text-field>
                    </v-col>
                    <v-col v-if="!server.shared" style="margin-left:20px">
                      <v-text-field readonly v-model="server.owner" label="Owner" hide-details style="padding-top:0px; margin-top:0px"></v-text-field>
                    </v-col>
                  </v-row>
                  <v-row no-gutters>
                    <v-col cols="6" style="padding-right:10px">
                      <v-text-field readonly v-model="server.name" label="Name"></v-text-field>
                    </v-col>
                    <v-col cols="6" style="padding-left:10px">
                      <v-text-field readonly v-model="server.region" label="Region">
                        <template v-slot:prepend-inner>
                          <v-icon small :title="server.region_shared ? server.region_secured ? 'Shared (Secured)' : 'Shared' : server.region_secured ? 'Personal (Secured)' : 'Personal'" :color="server.region_shared ? '#EB5F5D' : 'warning'" :style="`margin-top:4px; margin-bottom:2px; ${!server.region_secured ? 'padding-right:6px' : ''}`">{{ server.region_shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          <v-icon v-if="server.region_secured" :title="server.region_shared ? 'Shared (Secured)' : 'Personal (Secured)'" :color="server.region_shared ? '#EB5F5D' : 'warning'" style="font-size:12px; padding-left:2px; padding-top:6px; padding-right:6px">fas fa-lock</v-icon>
                        </template>
                      </v-text-field>
                    </v-col>
                  </v-row>
                  <v-row no-gutters>
                    <v-col cols="8" style="padding-right:10px">
                      <v-text-field readonly v-model="server.engine" label="Engine" style="padding-top:0px;"></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-left:10px">
                      <v-text-field readonly v-model="server.version" label="Version" style="padding-top:0px;"></v-text-field>
                    </v-col>
                  </v-row>
                  <div style="margin-bottom:15px">
                    <v-row no-gutters>
                      <v-col cols="8" style="padding-right:10px">
                        <v-text-field readonly v-model="server.hostname" label="Hostname" style="padding-top:0px;"></v-text-field>
                      </v-col>
                      <v-col cols="4" style="padding-left:10px">
                        <v-text-field readonly v-model="server.port" label="Port" style="padding-top:0px;"></v-text-field>
                      </v-col>
                    </v-row>
                    <v-text-field readonly v-model="server.username" label="Username" style="padding-top:0px;"></v-text-field>
                    <v-text-field readonly v-model="server.password" label="Password" :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'" :type="showPassword ? 'text' : 'password'" @click:append="showPassword = !showPassword" style="padding-top:0px;" hide-details></v-text-field>
                    <!-- SSL -->
                    <v-card v-if="server.ssl" style="height:52px; margin-top:15px; margin-bottom:15px">
                      <v-row no-gutters>
                        <v-col cols="auto" style="display:flex; margin:15px">
                          <v-icon color="#00b16a" style="font-size:17px; margin-top:3px">fas fa-key</v-icon>
                        </v-col>
                        <v-col>
                          <div class="text-body-1" style="color:#00b16a; margin-top:15px">Using a SSL connection</div>
                        </v-col>
                      </v-row>
                    </v-card>
                    <!-- SSH -->
                    <v-card v-if="server.ssh" style="height:52px; margin-top:15px; margin-bottom:15px">
                      <v-row no-gutters>
                        <v-col cols="auto" style="display:flex; margin:15px">
                          <v-icon color="#2196f3" style="font-size:16px; margin-top:4px">fas fa-terminal</v-icon>
                        </v-col>
                        <v-col>
                          <div class="text-body-1" style="color:#2196f3; margin-top:15px">Using a SSH connection</div>
                        </v-col>
                      </v-row>
                    </v-card>
                    <!-- SECURED -->
                    <v-card v-if="server.secured" style="height:52px; margin-top:15px; margin-bottom:15px">
                      <v-row no-gutters>
                        <v-col cols="auto" style="display:flex; margin:15px">
                          <v-icon color="#EF5354" style="font-size:16px; margin-top:4px">fas fa-lock</v-icon>
                        </v-col>
                        <v-col>
                          <div class="text-body-1" style="color:#EF5354; margin-top:15px">This server is secured</div>
                        </v-col>
                      </v-row>
                    </v-card>
                    <v-text-field readonly outlined v-model="server.usage" label="Usage" hide-details style="margin-top:20px"></v-text-field>
                  </div>
                </v-form>
                <v-divider></v-divider>
                <v-row no-gutters style="margin-top:15px;">
                  <v-col>
                    <v-btn :loading="loading" color="info" @click="testConnection()">Test Connection</v-btn>
                  </v-col>
                </v-row>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import axios from 'axios'
import EventBus from '../js/event-bus'
import Imports from './utils/Imports.vue'
import Exports from './utils/Exports.vue'
import Clones from './utils/Clones.vue'

export default {
  data() {
    return {
      tabs: 0,
      loading: false,
      search: '',
      filter: {
        import: false,
        export: false,
        clone: false,
      },
      selected: {
        import: 0,
        export: 0,
        clone: 0,
      },
      // Server Dialog
      serverDialog: false,
      server: {},
      showPassword: false,
    }
  },
  components: { Imports, Exports, Clones },
  mounted() {
    EventBus.$on('utils-toggle-filter', (value) => { this.filter[value.from] = value.value })
    EventBus.$on('utils-get-server', this.getServer)
    EventBus.$on('utils-select-row', (value) => { this.selected[value.from] = value.value })
  },
  created() {
    if (this.$route.path == '/admin/utils/imports') this.tabs = 0
    else if (this.$route.path == '/admin/utils/exports') this.tabs = 1
    else if (this.$route.path == '/admin/utils/clones') this.tabs = 2
    else this.$router.push('/admin/utils/imports')
  },
  computed: {
    filterActive: function() {
      return (this.filter['import'] && this.tabs == 0) || (this.filter['export'] && this.tabs == 1) || (this.filter['clone'] && this.tabs == 2)
    },
    rowsSelected: function() {
      if (this.tabs == 0) return this.selected['import']
      else if (this.tabs == 1) return this.selected['export']
      return this.selected['clone']
    }
  },
  watch: {
    tabs: function(val) {
      if (val == 0 && this.$route.path != '/admin/utils/imports') this.$router.push('/admin/utils/imports')
      else if (val == 1 && this.$route.path != '/admin/utils/exports') this.$router.push('/admin/utils/exports')
      else if (val == 2 && this.$route.path != '/admin/utils/clones') this.$router.push('/admin/utils/clones')
    },
  },
  methods: {
    getServer(server_id) {
      // Get Server
      this.loading = true
      this.showPassword = false
      this.serverDialog = true
      const payload = { server_id: server_id }
      axios.get('/admin/inventory/servers', { params: payload })
        .then((response) => {
          // Build usage
          let usage = []
          if (response.data.servers[0].usage.includes('D')) usage.push('Deployments')
          if (response.data.servers[0].usage.includes('M')) usage.push('Monitoring')
          if (response.data.servers[0].usage.includes('U')) usage.push('Utils')
          if (response.data.servers[0].usage.includes('C')) usage.push('Client')
          // Add server
          this.server = {...response.data.servers[0], usage: usage.join(', ')}
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    infoClick() {
      if (this.tabs == 0) EventBus.$emit('info-utils-import')
      else if (this.tabs == 1) EventBus.$emit('info-utils-export')
      else EventBus.$emit('info-utils-clone')
    },
    manageClick() {
      if (this.tabs == 0) EventBus.$emit('manage-utils-import')
      else if (this.tabs == 1) EventBus.$emit('manage-utils-export')
      else EventBus.$emit('manage-utils-clone')
    },
    filterClick() {
      if (this.tabs == 0) EventBus.$emit('filter-utils-import')
      else if (this.tabs == 1) EventBus.$emit('filter-utils-export')
      else EventBus.$emit('filter-utils-clone')
    },
    refreshClick() {
      if (this.tabs == 0) EventBus.$emit('refresh-utils-import')
      else if (this.tabs == 1) EventBus.$emit('refresh-utils-export')
      else EventBus.$emit('refresh-utils-clone')
    },
    columnsClick() {
      if (this.tabs == 0) EventBus.$emit('columns-utils-import')
      else if (this.tabs == 1) EventBus.$emit('columns-utils-export')
      else EventBus.$emit('columns-utils-clone')
    },
    testConnection() {
      // Test Connection
      EventBus.$emit('send-notification', 'Testing Server...', 'info')
      this.loading = true
      const payload = {
        region_id: this.server.region_id,
        server: { engine: this.server.engine, hostname: this.server.hostname, port: this.server.port, username: this.server.username, password: this.server.password }
      }
      axios.post('/admin/inventory/servers/test', payload)
        .then((response) => {
          EventBus.$emit('send-notification', response.data.message, '#00b16a')
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
  },
}
</script>