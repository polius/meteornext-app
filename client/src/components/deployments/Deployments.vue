<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">DEPLOYMENTS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn v-if="selected.length == 0" text @click="newDeploy()"><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn v-else-if="selected.length == 1" text @click="infoDeploy()"><v-icon small style="padding-right:10px">fas fa-info</v-icon>INFORMATION</v-btn>
        </v-toolbar-items>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="id" show-select class="elevation-1" style="padding-top:5px;">
        <template v-slot:[`item.name`]="{ item }">
          <v-edit-dialog :return-value.sync="item.name" lazy @open="openName(item)" @save="saveName(item)"> 
            {{ item.name }}
            <template v-slot:input>
              <v-text-field v-model="inline_editing_name" label="Name" single-line hide-details style="margin-bottom:20px;"></v-text-field>
            </template>
          </v-edit-dialog>
        </template>
        <template v-slot:[`item.release`]="{ item }">
          <v-edit-dialog :return-value.sync="item.release" large @open="openRelease(item)" @save="saveRelease(item)"> 
            {{ item.release }}
            <template v-slot:input>
              <v-autocomplete v-model="inline_editing_release" :items="releases_items" label="Releases" hide-details style="margin-top:15px; margin-bottom:5px;"></v-autocomplete>
            </template>
          </v-edit-dialog>
        </template>
        <template v-slot:[`item.mode`]="{ item }">
          <v-chip outlined :color="getModeColor(item.mode)">{{ item.mode }}</v-chip>
        </template>
        <template v-slot:[`item.method`]="{ item }">
          <span :style="'color: ' + getMethodColor(item.method)" style="font-weight:500">{{ item.method }}</span>
        </template>
        <template v-slot:[`item.status`]="{ item }">
          <v-icon v-if="item.status == 'CREATED'" title="Created" small style="color: #3498db; margin-left:9px;">fas fa-check</v-icon>
          <v-icon v-else-if="item.status == 'SCHEDULED'" title="Scheduled" small style="color: #ff9800; margin-left:8px;">fas fa-clock</v-icon>
          <v-icon v-else-if="item.status == 'QUEUED'" :title="`${'Queued: ' + item.queue}`" small style="color: #3498db; margin-left:8px;">fas fa-clock</v-icon>
          <v-icon v-else-if="item.status == 'STARTING'" title="Starting" small style="color: #3498db; margin-left:8px;">fas fa-spinner</v-icon>
          <v-icon v-else-if="item.status == 'IN PROGRESS'" title="In Progress" small style="color: #ff9800; margin-left:8px;">fas fa-spinner</v-icon>
          <v-icon v-else-if="item.status == 'SUCCESS'" title="Success" small style="color: #4caf50; margin-left:9px;">fas fa-check</v-icon>
          <v-icon v-else-if="item.status == 'WARNING'" title="Some queries failed" small style="color: #ff9800; margin-left:9px;">fas fa-check</v-icon>
          <v-icon v-else-if="item.status == 'FAILED'" title="Failed" small style="color: #e74c3c; margin-left:11px;">fas fa-times</v-icon>
          <v-icon v-else-if="item.status == 'STOPPING'" title="Stopping" small style="color: #ff9800; margin-left:8px;">fas fa-ban</v-icon>
          <v-icon v-else-if="item.status == 'STOPPED'" title="Stopped" small style="color: #e74c3c; margin-left:8px;">fas fa-ban</v-icon>
        </template>
        <template v-slot:[`item.scheduled`]="{ item }">
          <span>{{ item.scheduled === null ? '' : item.scheduled.slice(0,-3) }}</span>
        </template>
      </v-data-table>
    </v-card>

    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script>
import axios from 'axios';
import moment from 'moment';

export default {
  data: () => ({
    headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Release', align: 'left', value: 'release' },
      { text: 'Environment', align: 'left', value: 'environment' },
      { text: 'Mode', align: 'left', value: 'mode' },
      { text: 'Method', align: 'left', value: 'method' },
      { text: 'Status', align:'left', value: 'status' },
      { text: 'Created', align: 'left', value: 'created' },
      { text: 'Started', align: 'left', value: 'started' },
      { text: 'Ended', align: 'left', value: 'ended' },
      { text: 'Overall', align: 'left', value: 'overall' }
    ],
    items: [],
    selected: [],
    search: '',
    loading: true,

    // Inline Editing
    releases_items: [],
    inline_editing_name: '',
    inline_editing_release: '',

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  created() {
    this.getDeployments()
  },
  methods: {
    getDeployments() {
      axios.get('/deployments')
        .then((response) => {
          // Deployments
          this.items = response.data.deployments.map(x => ({...x, created: this.dateFormat(x.created), scheduled: this.dateFormat(x.scheduled), started: this.dateFormat(x.started), ended: this.dateFormat(x.ended)}))
          this.parseScheduled()
          // Releases
          for (var i = 0; i < response.data.releases.length; ++i) this.releases_items.push(response.data.releases[i]['name'])
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
    },
    parseScheduled() {
      // Check if 'Scheduled' column exists in headers
      var column_found = false
      for (var h = 0; h < this.headers.length; ++h) {
        if (this.headers[h]['text'] == 'Scheduled') { column_found = true; break; }
      }
      // Check if exists a scheduled deployment
      var scheduled_found = false
      for (var i = 0; i < this.items.length; ++i) {
        if (this.items[i]['scheduled']) { scheduled_found = true; break; }
      }
      // Add or remove the 'Scheduled' column in headers
      if (scheduled_found && !column_found) this.headers.splice(7, 0, { text: 'Scheduled', value: 'scheduled', sortable: false })
      else if (!scheduled_found && column_found) this.headers.splice(7, 1)
    },
    openName(item) {
      this.inline_editing_name = item.name
    },
    saveName(item) {
      if (this.inline_editing_name == item.name) {
        this.notification('Deployment edited successfully', '#00b16a')
        return
      }
      this.loading = true
      // Edit release name in the DB
      const payload = {
        put: 'name',
        id: item.id,
        name: this.inline_editing_name
      }
      axios.put('/deployments', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          // Reload Deployments Data
          this.getDeployments()
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        }) 
    },
    openRelease(item) {
      this.inline_editing_release = item.release
    },
    saveRelease(item) {
      if (this.inline_editing_release == item.release) {
        this.notification('Deployment edited successfully', '#00b16a')
        return
      }
      this.loading = true
      // Edit deployment release in the DB
      const payload = {
        put: 'release',
        id: item.id,
        release: this.inline_editing_release
      }
      axios.put('/deployments', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          // Reload Deployments Data
          this.getDeployments()
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        }) 
    },
    getModeColor (mode) {
      if (mode == 'BASIC') return 'rgb(250, 130, 49)'
      else if (mode == 'PRO') return 'rgb(235, 95, 93)'
    },
    getMethodColor (method) {
      if (method == 'DEPLOY') return '#e74c3c'
      else if (method == 'TEST') return '#ff9800'
      else if (method == 'VALIDATE') return '#4caf50'
    },
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
    newDeploy() {
      this.$router.push({ name:'deployments.new' })
    },
    infoDeploy() {
      const id = this.selected[0]['mode'].substring(0, 1) + this.selected[0]['execution_id']
      this.$router.push({ name:'deployment', params: { id: id }})
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  }
}
</script>