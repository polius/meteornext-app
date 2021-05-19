<template>
  <div>
    <v-data-table :headers="headers" :items="items" :hide-default-footer="items.length < 11" :loading="loading" item-key="id" show-select class="elevation-1">
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
    }
  },
  props: ['search'],
  mounted() {
    this.getServers()
  },
  methods: {
    getServers() {
      this.loading = true
      // Get Client queries
      axios.get('/admin/client/servers')
        .then((response) => {
          this.items = response.data.servers.map(x => ({...x, date: this.dateFormat(x.date)}))
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
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
  },
}
</script>