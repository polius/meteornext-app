<template>
  <div>
    <v-data-table v-model="selected" :headers="headers" :items="items" :options.sync="options" :server-items-length="total" :hide-default-footer="total.length < 11" :loading="loading" item-key="id" show-select class="elevation-1">
      <template v-ripple v-slot:[`header.data-table-select`]="{}">
        <v-simple-checkbox
          :value="items.length == 0 ? false : selected.length == items.length"
          :indeterminate="selected.length > 0 && selected.length != items.length"
          @click="selected.length == items.length ? selected = [] : selected = JSON.parse(JSON.stringify(items))">
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
        <v-icon small :title="item.attached ? 'Attached' : 'Detached'" :color="item.attached ? '#00b16a' : 'error'" style="margin-left:15px">fas fa-circle</v-icon>
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
                  <v-btn :disabled="loading" color="error" @click="filterDialog = false" style="margin-left:5px;">CANCEL</v-btn>
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
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:3px">{{ confirmDialogMode == 'attach' ? 'fas fa-plus' : 'fas fa-minus' }}</v-icon>{{ confirmDialogMode.toUpperCase() }}</v-toolbar-title>
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
                  <v-btn :disabled="loading" color="error" @click="confirmDialog = false" style="margin-left:5px;">CANCEL</v-btn>
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
      loading: true,
      origin: [],
      items: [],
      headers: [
        { text: 'User', align: 'left', value: 'user' },
        { text: 'Server', align: 'left', value: 'server' },
        { text: 'Attached', align: 'left', value: 'attached' },
        { text: 'Attached Date', align: 'left', value: 'date' },
        { text: 'Folder', align: 'left', value: 'folder' },
      ],
      selected: [],
      options: null,
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
    EventBus.$on('filter-client-servers', () => { this.filterDialog = true })
    EventBus.$on('refresh-client-servers', this.getServers)
    EventBus.$on('attach-client-servers', this.attachServers)
    EventBus.$on('detach-client-servers', this.detachServers)
  },
  watch: {
    options: {
      handler (newValue, oldValue) {
        if (oldValue == null || (oldValue.page == newValue.page && oldValue.itemsPerPage == newValue.itemsPerPage)) {
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
      this.loading = true
      var payload = {}
      // Build Filter
      let filter = this.filterApplied ? JSON.parse(JSON.stringify(this.filter)) : null
      if (filter != null) payload['filter'] = filter
      // Build Sort
      const { sortBy, sortDesc } = this.options
      if (sortBy.length > 0) payload['sort'] = { column: sortBy[0], desc: sortDesc[0] }
      // Get Client Servers
      axios.get('/admin/client/servers', { params: payload })
        .then((response) => {
          this.origin = response.data.servers.map(x => ({...x, date: this.dateFormat(x.date)}))
          this.total = this.origin.length
          this.filterUsers = response.data.users
          this.filterServers = this.origin.reduce((acc, val) => {
            if (!(acc.find(x => x.name == val.server))) acc.push(val.server)
            return acc
          },[])
          this.onSearch()
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
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
          (x.date != null && x.date.includes(this.search)) ||
          (x.folder != null && x.folder.includes(this.search))
        ).slice(itemStart, itemEnd)
      }
    },
    getServer(server_id) {
      EventBus.$emit('client-get-server', server_id)
    },
    submitFilter() {
      // Check if some filter was applied
      if (!Object.keys(this.filter).some(x => this.filter[x] != null && this.filter[x].length != 0)) {
        EventBus.$emit('send-notification', 'Enter at least one filter.', 'error')
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
      this.getServers()
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
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
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
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
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