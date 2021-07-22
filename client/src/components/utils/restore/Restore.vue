<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">RESTORE</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text @click="newRestore()"><v-icon small style="padding-right:10px;">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn :disabled="selected.length != 1" text @click="infoRestore()"><v-icon small style="padding-right:10px; padding-bottom:2px">fas fa-info</v-icon>INFORMATION</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="getRestore" text><v-icon small style="margin-right:10px">fas fa-sync-alt</v-icon>REFRESH</v-btn>
        </v-toolbar-items>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="execution_id" show-select class="elevation-1" style="padding-top:5px;">
        <template v-ripple v-slot:[`header.data-table-select`]="{}">
          <v-simple-checkbox
            :value="items.length == 0 ? false : selected.length == items.length"
            :indeterminate="selected.length > 0 && selected.length != items.length"
            @click="selected.length == items.length ? selected = [] : selected = JSON.parse(JSON.stringify(items))">
          </v-simple-checkbox>
        </template>
        <template v-slot:[`item.name`]="{ item }">
          <v-edit-dialog :return-value.sync="item.name" lazy @open="openName(item)" @save="saveName(item)"> 
            {{ item.name }}
            <template v-slot:input>
              <v-text-field v-model="inline_editing_name" label="Name" single-line hide-details style="margin-bottom:20px;"></v-text-field>
            </template>
          </v-edit-dialog>
        </template>
        <template v-slot:[`item.mode`]="{ item }">
          <v-icon v-if="item.mode == 'file'" :title="`File - ${JSON.parse(item.source).file} (${JSON.parse(item.source).size})`" small style="margin-left:8px; color:#2196f3">fas fa-file</v-icon>
          <v-icon v-else-if="item.mode == 'url'" title="URL" small style="margin-left:5px; color:#2196f3">fas fa-cloud</v-icon>
          <v-icon v-else-if="item.mode == 's3'" title="Amazon S3" style="font-size:22; margin-left:1px; color:#2196f3">fab fa-aws</v-icon>
        </template>
        <template v-slot:[`item.status`]="{ item }">
          <v-icon v-if="item.status == 'CREATED'" title="Created" small style="color: #3498db; margin-left:9px;">fas fa-check</v-icon>
          <v-icon v-else-if="item.status == 'SCHEDULED'" :title="`Scheduled: ${item.scheduled.slice(0,-3)}`" small style="color: #ff9800; margin-left:8px;">fas fa-clock</v-icon>
          <v-icon v-else-if="item.status == 'QUEUED'" :title="`Queued: ${item.queue}`" small style="color: #3498db; margin-left:8px;">fas fa-clock</v-icon>
          <v-icon v-else-if="item.status == 'STARTING'" title="Starting" small style="color: #3498db; margin-left:8px;">fas fa-spinner</v-icon>
          <v-icon v-else-if="item.status == 'IN PROGRESS'" title="In Progress" small style="color: #ff9800; margin-left:8px;">fas fa-spinner</v-icon>
          <v-icon v-else-if="item.status == 'SUCCESS'" title="Success" small style="color: #4caf50; margin-left:9px;">fas fa-check</v-icon>
          <v-icon v-else-if="item.status == 'WARNING'" title="Some queries failed" small style="color: #ff9800; margin-left:9px;">fas fa-check</v-icon>
          <v-icon v-else-if="item.status == 'FAILED'" title="Failed" small style="color: #EF5354; margin-left:11px;">fas fa-times</v-icon>
          <v-icon v-else-if="item.status == 'STOPPING'" title="Stopping" small style="color: #ff9800; margin-left:8px;">fas fa-ban</v-icon>
          <v-icon v-else-if="item.status == 'STOPPED'" title="Stopped" small style="color: #EF5354; margin-left:8px;">fas fa-ban</v-icon>
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
      { text: 'Mode', align: 'left', value: 'mode' },
      { text: 'Server', align: 'left', value: 'server' },
      { text: 'Database', align: 'left', value: 'database' },
      { text: 'Status', align:'left', value: 'status' },
      // { text: 'Created', align: 'left', value: 'created' },
      { text: 'Started', align: 'left', value: 'started' },
      { text: 'Ended', align: 'left', value: 'ended' },
      { text: 'Overall', align: 'left', value: 'overall' }
    ],
    items: [],
    selected: [],
    search: '',
    loading: false,

    // Inline Editing
    inline_editing_name: '',

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  created() {
    this.getRestore()
  },
  methods: {
    getRestore() {
      this.loading = true
      // Get Restores
      axios.get('/restore')
        .then((response) => {
          this.items = response.data.restore.map(x => ({...x, created: this.dateFormat(x.created), started: this.dateFormat(x.started), ended: this.dateFormat(x.ended)}))
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    openName(item) {
      this.inline_editing_name = item.name
    },
    saveName(item) {
      if (this.inline_editing_name == item.name) {
        this.notification('Restore edited successfully', '#00b16a')
        return
      }
      this.loading = true
      // Edit release name in the DB
      const payload = {
        put: 'name',
        id: item.id,
        name: this.inline_editing_name
      }
      axios.put('/restore', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.getRestore()
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        }) 
    },
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
    newRestore() {
      this.$router.push({ name: 'utils.restore.new' })
    },
    infoRestore() {
      this.$router.push({ name: 'utils.restore.info', params: { id: this.selected[0]['id'] }})
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color
      this.snackbar = true
    }
  }
}
</script>