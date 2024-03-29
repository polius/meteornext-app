<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="body-2 white--text font-weight-medium" style="font-size:0.9rem!important"><v-icon small style="margin-right:10px">fas fa-desktop</v-icon>MONITORING</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items>
          <v-btn @click="filterDialog = true" text :style="{ backgroundColor : filterApplied ? '#4ba1f1' : '' }"><v-icon small style="padding-right:10px">fas fa-sliders-h</v-icon>FILTER</v-btn>
          <v-btn @click="getMonitoringServers" text><v-icon small style="margin-right:10px">fas fa-sync-alt</v-icon>REFRESH</v-btn>
          <v-btn v-show="attached != null" @click="confirmDialog = true" text><v-icon small style="padding-right:10px">{{ attached ? 'fas fa-minus' : 'fas fa-plus' }}</v-icon>{{ attached ? 'DETACH' : 'ATTACH' }}</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
        </v-toolbar-items>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="headers" :items="items" @current-items="(items) => current = items" :options.sync="options" :server-items-length="total" :sort-by.sync="sortBy" :sort-desc.sync="sortDesc" :loading="loading" item-key="id" show-select class="elevation-1" mobile-breakpoint="0">
        <template v-ripple v-slot:[`header.data-table-select`]="{}">
          <v-simple-checkbox
            :value="items.length == 0 ? false : selected.length == items.length"
            :indeterminate="selected.length > 0 && selected.length != items.length"
            @click="checkboxClick">
          </v-simple-checkbox>
        </template>
        <template v-slot:[`item.server`]="{ item }">
          <v-icon v-if="!item.active" small color="warning" title="Maximum allowed resources exceeded. Upgrade your license to have more servers." style="margin-right:8px">fas fa-exclamation-triangle</v-icon>
          <v-btn @click="getServer(item.server_id)" text class="body-2" style="text-transform:inherit; padding:0 5px; margin-left:-5px">
            <v-icon small :title="item.shared ? item.secured ? 'Shared (Secured)' : 'Shared' : item.secured ? 'Personal (Secured)' : 'Personal'" :color="item.shared ? '#EB5F5D' : 'warning'" :style="`margin-bottom:2px; ${!item.secured ? 'padding-right:8px' : ''}`">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
            <v-icon v-if="item.secured" :title="item.shared ? 'Shared (Secured)' : 'Personal (Secured)'" :color="item.shared ? '#EB5F5D' : 'warning'" style="font-size:12px; padding-left:2px; padding-top:2px; padding-right:8px">fas fa-lock</v-icon>
            {{ item.server }}
          </v-btn>
        </template>
        <template v-slot:[`item.attached`]="{ item }">
          <v-icon small :title="item.attached ? 'Attached' : 'Detached'" :color="item.attached ? '#00b16a' : '#EF5354'" style="margin-left:15px">fas fa-circle</v-icon>
        </template>
        <template v-slot:[`footer.prepend`]>
          <div v-if="disabledResources" class="text-body-2 font-weight-regular" style="margin:10px"><v-icon small color="warning" style="margin-right:10px; margin-bottom:2px">fas fa-exclamation-triangle</v-icon>Some servers are disabled. Consider the possibility of upgrading your license.</div>
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
      disabledResources: false,
      loading: false,
      origin: [],
      items: [],
      current: [],
      headers: [
        { text: 'User', align: 'left', value: 'user' },
        { text: 'Server', align: 'left', value: 'server' },
        { text: 'Attached', align: 'left', value: 'attached' },
        { text: 'Attached Date', align: 'left', value: 'date' },
      ],
      selected: [],
      options: null,
      firstLoad: true,
      sortBy: null,
      sortDesc: null,
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
        if (oldValue == null || (!this.firstLoad && oldValue.page == newValue.page && oldValue.itemsPerPage == newValue.itemsPerPage)) {
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
      var payload = {}
      // Build Filter
      let filterKeys = Object.keys(this.$route.query).filter(x => !(['sortBy','sortDesc'].includes(x)))
      if (!this.filterApplied && filterKeys.length != 0) {
        this.filter = filterKeys.reduce((acc, val) => {
          acc[val] = this.$route.query[val]
          return acc
        },{})
        this.filterApplied = true
      }
      if (this.filterApplied) {
        this.filterOrigin = JSON.parse(JSON.stringify(this.filter))
        payload['filter'] = this.filter
      }
      // Build Sort
      const { sortBy, sortDesc } = this.options
      if (sortBy.length > 0) {
        payload['sort'] = { column: sortBy[0], desc: sortDesc[0] === undefined ? false : sortDesc[0] }
      }
      else if (this.firstLoad && 'sortBy' in this.$route.query && 'sortDesc' in this.$route.query) {
        this.sortBy = this.$route.query['sortBy']
        this.sortDesc = this.$route.query['sortDesc'] == 'true'
        payload['sort'] = { column: this.sortBy, desc: this.sortDesc }
      }
      // Build URL Params
      let query = {}
      if ('filter' in payload) query = {...payload['filter']}
      if ('sort' in payload) query = {...query, sortBy: payload['sort']['column'], sortDesc: payload['sort']['desc']}
      let routeQuery = ('sortDesc' in this.$route.query) ? {...this.$route.query, "sortDesc": this.$route.query['sortDesc'] == 'true'} : this.$route.query
      if (JSON.stringify(routeQuery) != JSON.stringify(query)) this.$router.replace({query: query})
      // Get Client Servers
      this.loading = true
      axios.get('/admin/monitoring/servers', { params: payload })
        .then((response) => {
          this.origin = response.data.servers.map(x => ({...x, date: this.dateFormat(x.date)}))
          this.filterUsers = response.data.users_list
          this.filterServers = response.data.servers_list
          this.onSearch()
          this.firstLoad = false
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    onSearch() {
      const { page, itemsPerPage } = this.options
      const itemStart = (page-1) * itemsPerPage
      const itemEnd = (page-1) * itemsPerPage + itemsPerPage
      if (this.search.length == 0) {
        this.items = this.origin.slice(itemStart, itemEnd)
        this.total = this.origin.length
      }
      else {
        const items = this.origin.filter(x =>
          x.user.includes(this.search) ||
          x.server.includes(this.search) ||
          (x.date != null && x.date.includes(this.search))
        )
        this.total = items.length
        this.items = items.slice(itemStart, itemEnd)
      }
      this.disabledResources = this.items.some(x => !x.active)
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
      this.firstLoad = true
      this.sortBy = null
      this.sortDesc = null
      this.$router.replace({query: {}})
      this.$nextTick(() => this.getMonitoringServers())
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
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
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
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
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
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
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
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
    checkboxClick() {
      if (this.search.trim().length == 0) this.selected.length == this.items.length ? this.selected = [] : this.selected = [...this.items]
      else {
        const allSelected = this.current.every(x => this.selected.find(y => y.id == x.id))
        if (allSelected) this.selected = this.selected.filter(x => !this.current.find(y => y.id == x.id))
        else this.selected = this.selected.filter(x => !this.current.find(y => y.id == x.id)).concat(this.current)
      }
    },
  },
}
</script>