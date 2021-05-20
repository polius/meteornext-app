<template>
  <div>
    <v-data-table v-model="selected" :headers="headers" :items="items" :hide-default-footer="items.length < 11" :loading="loading" item-key="id" show-select class="elevation-1">
      <template v-ripple v-slot:[`header.data-table-select`]="{}">
        <v-simple-checkbox
          :value="items.length == 0 ? false : selected.length == items.length"
          :indeterminate="selected.length > 0 && selected.length != items.length"
          @click="selected.length == items.length ? selected = [] : selected = JSON.parse(JSON.stringify(items))">
        </v-simple-checkbox>
      </template>
      <template v-slot:[`item.server_name`]="{ item }">
        <v-btn @click="getServer(item.server_id)" text class="body-2" style="text-transform:inherit; padding:0 5px; margin-left:-5px">
          <v-icon small :title="item.server_shared ? 'Shared' : 'Personal'" :color="item.server_shared ? '#EB5F5D' : 'warning'" style="margin-right:6px; margin-bottom:2px;">
            {{ item.server_shared ? 'fas fa-users' : 'fas fa-user' }}
          </v-icon>
          {{ item.server_name }}
        </v-btn>
      </template>
      <template v-slot:[`item.server_shared`]="{ item }">
        <v-icon small :title="item.server_shared ? 'Shared' : 'Personal'" :color="item.server_shared ? '#EB5F5D' : 'warning'" style="margin-right:6px; margin-bottom:2px;">{{ item.server_shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
        {{ item.shared ? 'Shared' : 'Personal' }}
      </template>
      <template v-slot:[`item.server_attached`]="{ item }">
        <v-icon small :title="item.server_attached ? 'Attached' : 'Detached'" :color="item.server_attached ? '#00b16a' : 'error'" style="margin-left:15px">fas fa-circle</v-icon>
      </template>
    </v-data-table>

    <v-dialog v-model="filterDialog" max-width="50%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:3px">fas fa-sliders-h</v-icon>FILTER</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="filterDialog = false" style="width:40px; height:40px"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 10px 15px 15px 15px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:10px; margin-bottom:20px;">
                  <v-row>
                    <v-col>
                      <v-autocomplete :loading="loading" text v-model="filter.user" :items="filterUsers" item-value="user" item-text="user" label="User" style="padding-top:0px" hide-details>
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
                      <v-autocomplete :loading="loading" text v-model="filter.server" :items="filterServers" item-value="name" item-text="name" label="Server" style="padding-top:0px" hide-details>
                        <template v-slot:item="{ item }" >
                          <v-row no-gutters align="center">
                            <v-col class="flex-grow-1 flex-shrink-1">
                              {{ item.name }}
                            </v-col>
                            <v-col cols="auto" class="flex-grow-0 flex-shrink-0">
                              <v-chip label><v-icon small :color="item.shared ? 'error' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>{{ item.shared ? 'Shared' : 'Personal' }}</v-chip>
                            </v-col>
                          </v-row>
                        </template>
                        <template v-slot:selection="{ item }" >
                          <v-icon small :color="item.shared ? 'error' : 'warning'" style="margin-right:7px; margin-top:2px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          {{ item.name }}
                        </template>
                      </v-autocomplete>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col>
                      <v-checkbox v-model="filter.attached" label="Attached" style="margin-top:0px" hide-details></v-checkbox>
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
      items: [],
      headers: [
        { text: 'User', align: 'left', value: 'user_username' },
        { text: 'Server', align: 'left', value: 'server_name' },
        { text: 'Attached', align: 'left', value: 'server_attached' },
        { text: 'Attached Date', align: 'left', value: 'date' },
        { text: 'Folder Name', align: 'left', value: 'folder_name' },
      ],
      selected: [],
      // Filter Dialog
      filterDialog: false,
      filter: {},
      filterUsers: [],
      filterServers: [],
      filterApplied: false,
    }
  },
  props: ['search'],
  mounted() {
    EventBus.$on('filter-client-servers', () => { this.filterDialog = true })
    EventBus.$on('refresh-client-servers', this.getServers)
    EventBus.$on('attach-client-servers', this.attachServers)
    EventBus.$on('detach-client-servers', this.detachServers)
    this.getServers()
  },
  watch: {
    selected: function(val) {
      EventBus.$emit('client-servers-select', val)
    },
  },
  methods: {
    getServers() {
      this.loading = true
      // Get Client queries
      axios.get('/admin/client/servers')
        .then((response) => {
          this.items = response.data.servers.map(x => ({...x, date: this.dateFormat(x.date)}))
          this.filterUsers = response.data.users
          this.filterServers = this.items.reduce((acc, val) => {
            if (!(acc.find(x => x.name == val.server_name && x.shared == val.server_shared))) {
              acc.push({ name: val.server_name, shared: val.server_shared })
            }
            return acc
          },[])
          // this.onSearch()
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
    },
    getServer(server_id) {
      EventBus.$emit('client-get-server', server_id)
    },
    submitFilter() {

    },
    clearFilter() {
      this.filterDialog = false
      this.filter = {}
      EventBus.$emit('client-toggle-filter', false)
      this.getServers()
    },
    attachServers() {

    },
    detachServers() {

    },
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
  },
}
</script>