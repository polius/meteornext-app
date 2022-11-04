<template>
  <div>
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
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:3px">{{ confirmDialogMode == 'attach' ? 'fas fa-link' : 'fas fa-unlink' }}</v-icon>{{ confirmDialogMode.toUpperCase() }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="confirmDialog = false" style="width:40px; height:40px"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:5px; margin-bottom:15px;">
                  <div class="text-body-1">{{ `Are you sure you want to ${confirmDialogMode} the selected servers?` }}</div>
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
import EventBus from '../../js/event-bus'

export default {
  data() {
    return {
      disabledResources: false,
      loading: true,
      origin: [],
      items: [],
      current: [],
      headers: [
        { text: 'User', align: 'left', value: 'user' },
        { text: 'Server', align: 'left', value: 'server' },
        { text: 'Attached', align: 'left', value: 'attached' },
        { text: 'Attached Date', align: 'left', value: 'date' },
        { text: 'Folder', align: 'left', value: 'folder' },
      ],
      selected: [],
      options: null,
      firstLoad: true,
      sortBy: null,
      sortDesc: null,
      total: 0,
      // Filter Dialog
      filterDialog: false,
      filter: {},
      filterUsers: [],
      filterServers: [],
      filterApplied: false,
      // Confirm Dialog
      confirmDialog: false,
      confirmDialogMode: 'attach',
    }
  },
  props: ['active','search'],
  mounted() {
    EventBus.$on('filter-client-servers', () => {
      if (!this.filterApplied) this.filter = {}
      this.filterDialog = true
    })
    EventBus.$on('refresh-client-servers', this.getServers)
    EventBus.$on('attach-client-servers', this.attachServers)
    EventBus.$on('detach-client-servers', this.detachServers)
  },
  destroyed() {
    EventBus.$off()
  },
  watch: {
    options: {
      handler (newValue, oldValue) {
        if (oldValue == null || (!this.firstLoad && oldValue.page == newValue.page && oldValue.itemsPerPage == newValue.itemsPerPage)) {
          this.getServers()
        }
        else this.onSearch()
      },
      deep: true,
    },
    active: function(newVal) {
      if (newVal) this.onSearch()
    },
    search: function() {
      if (this.active) this.onSearch()
    },
    selected: function(val) {
      EventBus.$emit('client-servers-select', val)
    },
  },
  methods: {
    getServers() {
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
        payload['filter'] = Object.keys(this.filter).reduce((acc, val) => {
          acc[val] = this.filter[val]
          return acc
        },{})
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
      axios.get('/admin/client/servers', { params: payload })
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
          x.user.toLowerCase().includes(this.search.toLowerCase()) ||
          x.server.toLowerCase().includes(this.search.toLowerCase()) ||
          (x.date != null && x.date.includes(this.search)) ||
          (x.folder != null && x.folder.toLowerCase().includes(this.search.toLowerCase()))
        )
        this.total = items.length
        this.items = items.slice(itemStart, itemEnd)
      }
      this.disabledResources = this.items.some(x => !x.active)
    },
    getServer(server_id) {
      EventBus.$emit('client-get-server', server_id)
    },
    submitFilter() {
      // Check if some filter was applied
      if (!Object.keys(this.filter).some(x => this.filter[x] != null && this.filter[x].length != 0)) {
        EventBus.$emit('send-notification', 'Enter at least one filter.', '#EF5354')
        return
      }
      this.filterDialog = false
      EventBus.$emit('client-toggle-filter', { from: 'servers', value: true })
      this.filterApplied = true
      this.getServers()
    },
    clearFilter() {
      this.filterDialog = false
      this.filter = {}
      EventBus.$emit('client-toggle-filter', { from: 'servers', value: false })
      this.filterApplied = false
      this.firstLoad = true
      this.sortBy = null
      this.sortDesc = null
      this.$router.replace({query: {}})
      this.$nextTick(() => this.getServers())
    },
    attachServers() {
      this.confirmDialogMode = 'attach'
      this.confirmDialog = true
    },
    detachServers() {
      this.confirmDialogMode = 'detach'
      this.confirmDialog = true
    },
    confirmDialogSubmit() {
      if (this.confirmDialogMode == 'attach') this.submitAttachServers()
      else if (this.confirmDialogMode == 'detach') this.submitDetachServers()
    },
    submitAttachServers() {
      this.loading = true
      const payload = {
        servers: this.selected.map(x => ({ user_id: x.user_id, server_id: x.server_id }))
      }
      axios.post('/admin/client/servers', payload)
        .then((response) => {
          EventBus.$emit('send-notification', response.data.message, '#00b16a')
          this.selected = []
          this.getServers()
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
      axios.delete('/admin/client/servers', { params: payload })
        .then((response) => {
          EventBus.$emit('send-notification', response.data.message, '#00b16a')
          this.getServers()
          this.selected = []
          this.confirmDialog = false
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