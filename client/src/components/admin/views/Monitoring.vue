<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="body-2 white--text font-weight-medium" style="font-size:0.9rem!important"><v-icon small style="margin-right:10px">fas fa-desktop</v-icon>MONITORING</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn @click="filterDialog = true" text :style="{ backgroundColor : filterApplied ? '#4ba1f1' : '' }"><v-icon small style="padding-right:10px">fas fa-sliders-h</v-icon>FILTER</v-btn>
          <v-btn @click="getMonitoringServers" text><v-icon small style="margin-right:10px">fas fa-sync-alt</v-icon>REFRESH</v-btn>
          <v-btn v-show="attached != null" @click="confirmDialog = true" text><v-icon small style="padding-right:10px">{{ attached ? 'fas fa-minus' : 'fas fa-plus' }}</v-icon>{{ attached ? 'DETACH' : 'ATTACH' }}</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
        </v-toolbar-items>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="headers" :items="items" :options.sync="options" :server-items-length="total" :hide-default-footer="total.length < 11" :loading="loading" item-key="id" show-select class="elevation-1">
        <template v-ripple v-slot:[`header.data-table-select`]="{}">
          <v-simple-checkbox
            :value="items.length == 0 ? false : selected.length == items.length"
            :indeterminate="selected.length > 0 && selected.length != items.length"
            @click="selected.length == items.length ? selected = [] : selected = [...items]">
          </v-simple-checkbox>
        </template>
        <template v-slot:[`item.server`]="{ item }">
          <v-btn @click="getServer(item.server_id)" text class="body-2" style="text-transform:inherit; padding:0 5px; margin-left:-5px">
            <v-icon small :title="item.shared ? 'Shared' : 'Personal'" :color="item.shared ? '#EB5F5D' : 'warning'" style="margin-right:6px; margin-bottom:2px;">
              {{ item.shared ? 'fas fa-users' : 'fas fa-user' }}
            </v-icon>
            {{ item.server }}
          </v-btn>
        </template>
        <template v-slot:[`item.shared`]="{ item }">
          <v-icon small :title="item.shared ? 'Shared' : 'Personal'" :color="item.shared ? '#EB5F5D' : 'warning'" style="margin-right:6px; margin-bottom:2px;">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
          {{ item.shared ? 'Shared' : 'Personal' }}
        </template>
        <template v-slot:[`item.attached`]="{ item }">
          <v-icon small :title="item.attached ? 'Attached' : 'Detached'" :color="item.attached ? '#00b16a' : '#EF5354'" style="margin-left:15px">fas fa-circle</v-icon>
        </template>
      </v-data-table>
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
        <v-card-text style="padding: 0px 15px 15px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:20px;">
                  <v-row no-gutters style="margin-bottom:15px">
                    <v-col>
                      <v-text-field readonly v-model="server.group" label="Group" hide-details style="padding-top:0px"></v-text-field>
                    </v-col>
                    <v-col v-if="!server.shared" style="margin-left:20px">
                      <v-text-field readonly v-model="server.owner" label="Owner" hide-details style="padding-top:0px"></v-text-field>
                    </v-col>
                  </v-row>
                  <v-row no-gutters>
                    <v-col cols="8" style="padding-right:10px">
                      <v-text-field readonly v-model="server.name" label="Name"></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-left:10px">
                      <v-text-field readonly v-model="server.region" label="Region">
                        <template v-slot:prepend-inner>
                          <v-icon small :color="server.region_shared ? '#EB5F5D' : 'warning'" style="margin-top:4px; margin-right:5px">{{ server.region_shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
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
                  <div style="margin-bottom:20px">
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
                <v-row no-gutters style="margin-top:20px;">
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
    <v-dialog v-model="filterDialog" max-width="50%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:3px">fas fa-sliders-h</v-icon>FILTER</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="filterDialog = false" style="width:40px; height:40px"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:10px; margin-bottom:20px;">
                  <v-row>
                    <v-col>
                      <v-autocomplete :loading="loading" text v-model="filter.user" :items="filterUsers" item-value="user" item-text="user" label="User" clearable style="padding-top:0px" hide-details>
                        <template v-slot:item="{ item }" >
                          <v-row no-gutters align="center">
                            <v-col class="flex-grow-1 flex-shrink-1">
                              {{ item.user }}
                            </v-col>
                            <v-col cols="auto" class="flex-grow-0 flex-shrink-0">
                              <v-chip label>{{ item.group }}</v-chip>
                            </v-col>
                          </v-row>
                        </template>
                      </v-autocomplete>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col>
                      <v-autocomplete :loading="loading" text v-model="filter.server" :items="filterServers" label="Server" clearable style="padding-top:0px" hide-details></v-autocomplete>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col>
                      <v-autocomplete :loading="loading" text v-model="filter.attached" :items="[{ id: 'attached', text: 'Server attached'}, { id: 'detached', text: 'Server detached' }]" item-value="id" item-text="text" label="Attached" clearable style="padding-top:0px" hide-details></v-autocomplete>
                    </v-col>
                  </v-row>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :loading="loading" color="#00b16a" @click="submitFilter">CONFIRM</v-btn>
                  <v-btn :disabled="loading" color="#EF5354" @click="filterDialog = false" style="margin-left:5px;">CANCEL</v-btn>
                  <v-btn v-show="filterApplied" :disabled="loading" color="info" @click="clearFilter" style="float:right;">Remove Filter</v-btn>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="confirmDialog" max-width="50%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:3px">{{ attached ? 'fas fa-minus' : 'fas fa-plus' }}</v-icon>{{ attached ? 'DETACH' : 'ATTACH' }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="confirmDialog = false" style="width:40px; height:40px"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:5px; margin-bottom:15px;">
                  <div class="text-body-1">{{ `Are you sure you want to ${attached ? 'detach' : 'attach'} the selected servers?` }}</div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :loading="loading" color="#00b16a" @click="confirmDialogSubmit">CONFIRM</v-btn>
                  <v-btn :disabled="loading" color="#EF5354" @click="confirmDialog = false" style="margin-left:5px;">CANCEL</v-btn>
                </div>
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
import moment from 'moment'
import EventBus from '../js/event-bus'

export default {
  data() {
    return {
      loading: false,
      origin: [],
      items: [],
      headers: [
        { text: 'User', align: 'left', value: 'user' },
        { text: 'Server', align: 'left', value: 'server' },
        { text: 'Attached', align: 'left', value: 'attached' },
        { text: 'Attached Date', align: 'left', value: 'date' },
      ],
      selected: [],
      options: null,
      total: 0,
      attached: null,
      search: '',
      // Filter Dialog
      filterDialog: false,
      filter: {},
      filterUsers: [],
      filterServers: [],
      filterApplied: false,
      // Confirm Dialog
      confirmDialog: false,
      // Server Dialog
      serverDialog: false,
      server: {},
      showPassword: false,
    }
  },
  watch: {
    options: {
      handler (newValue, oldValue) {
        if (oldValue == null || (oldValue.page == newValue.page && oldValue.itemsPerPage == newValue.itemsPerPage)) {
          this.getMonitoringServers()
        }
        else this.onSearch()
      },
      deep: true,
    },
    search: function() {
      this.onSearch()
    },
    selected: function(val) {
      this.selectServer(val)
    },
  },
  methods: {
    getMonitoringServers() {
      this.loading = true
      var payload = {}
      // Build Filter
      let filter = this.filterApplied ? JSON.parse(JSON.stringify(this.filter)) : null
      if (filter != null) payload['filter'] = filter
      // Build Sort
      const { sortBy, sortDesc } = this.options
      if (sortBy.length > 0) payload['sort'] = { column: sortBy[0], desc: sortDesc[0] }
      // Get Client Servers
      axios.get('/admin/monitoring/servers', { params: payload })
        .then((response) => {
          this.origin = response.data.servers.map(x => ({...x, date: this.dateFormat(x.date)}))
          this.total = this.origin.length
          this.filterUsers = response.data.users_list
          this.filterServers = response.data.servers_list
          this.onSearch()
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    onSearch() {
      const { page, itemsPerPage } = this.options
      const itemStart = (page-1) * itemsPerPage
      const itemEnd = (page-1) * itemsPerPage + itemsPerPage
      if (this.search.length == 0) this.items = this.origin.slice(itemStart, itemEnd)
      else {
        this.items = this.origin.filter(x =>
          x.user.includes(this.search) ||
          x.server.includes(this.search) ||
          (x.date != null && x.date.includes(this.search))
        ).slice(itemStart, itemEnd)
      }
    },
    submitFilter() {
      // Check if some filter was applied
      if (!Object.keys(this.filter).some(x => this.filter[x] != null && this.filter[x].length != 0)) {
        EventBus.$emit('send-notification', 'Enter at least one filter.', '#EF5354')
        return
      }
      this.filterDialog = false
      this.filterApplied = true
      this.getMonitoringServers()
    },
    clearFilter() {
      this.filterDialog = false
      this.filterApplied = false
      this.filter = {}
      this.getMonitoringServers()
    },
    confirmDialogSubmit() {
      if (this.attached) this.submitDetachServers()
      else this.submitAttachServers()
    },
    submitAttachServers() {
      this.loading = true
      const payload = {
        servers: this.selected.map(x => ({ user_id: x.user_id, server_id: x.server_id }))
      }
      axios.post('/admin/monitoring/servers', payload)
        .then((response) => {
          EventBus.$emit('send-notification', response.data.message, '#00b16a')
          this.selected = []
          this.getMonitoringServers()
          this.confirmDialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    submitDetachServers() {
      this.loading = true
      const payload = {
        servers: JSON.stringify(this.selected.map(x => ({ user_id: x.user_id, server_id: x.server_id })))
      }
      axios.delete('/admin/monitoring/servers', { params: payload })
        .then((response) => {
          EventBus.$emit('send-notification', response.data.message, '#00b16a')
          this.getMonitoringServers()
          this.selected = []
          this.confirmDialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    getServer(server_id) {
      // Get Server
      this.showPassword = false
      this.serverDialog = true
      this.loading = true
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
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
  },
}
</script>