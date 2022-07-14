<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="body-2 white--text font-weight-medium" style="font-size:0.9rem!important"><v-icon small style="margin-right:10px">fas fa-bolt</v-icon>CLIENT</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items>
          <v-tabs @change="changeTab" background-color="primary" color="white" v-model="tabs" slider-color="white" slot="extension">
            <v-tab title="Show Executed Queries"><span class="pl-2 pr-2"><v-icon small style="padding-right:10px">fas fa-database</v-icon>QUERIES</span></v-tab>
            <v-tab title="Show Attached / Detached Servers"><span class="pl-2 pr-2"><v-icon small style="padding-right:10px">fas fa-server</v-icon>SERVERS</span></v-tab>
          </v-tabs>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="filterClick" text :style="{ backgroundColor : filterActive ? '#4ba1f1' : '' }"><v-icon small style="padding-right:10px">fas fa-sliders-h</v-icon>FILTER</v-btn>
          <v-btn @click="refreshClick" text ><v-icon small style="margin-right:10px">fas fa-sync-alt</v-icon>REFRESH</v-btn>
          <v-btn v-show="tabs == 1 && attached != null" @click="attachClick" text><v-icon small style="padding-right:10px">{{ attached ? 'fas fa-unlink' : 'fas fa-link' }}</v-icon>{{ attached ? 'DETACH' : 'ATTACH' }}</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
        </v-toolbar-items>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
        <v-divider v-if="tabs == 0" class="mx-3" inset vertical style="margin-right:4px!important"></v-divider>
        <v-btn v-if="tabs == 0" @click="filterColumnsClick" icon title="Show/Hide columns" style="margin-right:-10px; width:40px; height:40px;"><v-icon small>fas fa-cog</v-icon></v-btn>
      </v-toolbar>
      <Queries v-show="tabs == 0" :active="tabs == 0" :search="search" />
      <Servers v-show="tabs == 1" :active="tabs == 1" :search="search" />
    </v-card>
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
                <v-form ref="form" style="margin-top:15px">
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
                    <v-text-field readonly outlined v-model="server.usage" label="Usage" hide-details style="margin-top:20px"></v-text-field>
                  </div>
                </v-form>
                <v-divider></v-divider>
                <v-row no-gutters style="margin-top:15px">
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
import Queries from './client/Queries'
import Servers from './client/Servers'

export default {
  data() {
    return {
      tabs: 0,
      loading: false,
      attached: null,
      search: '',
      filter: {
        queries: false,
        servers: false
      },
      // Server Dialog
      serverDialog: false,
      server: {},
      showPassword: false,
    }
  },
  components: { Queries, Servers },
  created() {
    if (this.$route.path.startsWith('/admin/client/queries')) this.tabs = 0
    else if (this.$route.path.startsWith('/admin/client/servers')) this.tabs = 1
    else this.$router.push('/admin/client/queries')
  },
  mounted() {
    EventBus.$on('client-toggle-filter', (value) => { this.filter[value.from] = value.value })
    EventBus.$on('client-get-server', this.getServer)
    EventBus.$on('client-servers-select', this.selectServer)
  },
  computed: {
    filterActive: function() {
      return (this.filter['queries'] && this.tabs == 0) || (this.filter['servers'] && this.tabs == 1)
    },
  },
  methods: {
    changeTab(val) {
      if (val == 0) this.$router.push("/admin/client/queries")
      if (val == 1) this.$router.push("/admin/client/servers")
    },
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
    selectServer(val) {
      if (val.length == 0) this.attached = null
      else if (val.every(x => x.attached == 1)) this.attached = true
      else if (val.every(x => x.attached == 0)) this.attached = false
      else this.attached = null
    },
    filterClick() {
      if (this.tabs == 0) EventBus.$emit('filter-client-queries')
      else EventBus.$emit('filter-client-servers')
    },
    refreshClick() {
      if (this.tabs == 0) EventBus.$emit('refresh-client-queries')
      else EventBus.$emit('refresh-client-servers')
    },
    attachClick() {
      if (this.attached) EventBus.$emit('detach-client-servers')
      else EventBus.$emit('attach-client-servers')
    },
    filterColumnsClick() {
      EventBus.$emit('filter-client-columns')
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