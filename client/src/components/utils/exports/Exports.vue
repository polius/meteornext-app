<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">EXPORTS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items>
          <v-btn text @click="newExport()"><v-icon small style="margin-right:10px;">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn :disabled="selected.length != 1" text @click="infoExport()"><v-icon small style="padding-right:10px">fas fa-bookmark</v-icon>DETAILS</v-btn>
          <v-btn :disabled="selected.length == 0" text @click="deleteExport()"><v-icon small style="margin-right:10px;">fas fa-minus</v-icon>DELETE</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="getExports" text><v-icon small style="margin-right:10px">fas fa-sync-alt</v-icon>REFRESH</v-btn>
        </v-toolbar-items>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
        <v-divider class="mx-3" inset vertical style="margin-right:4px!important"></v-divider>
        <v-btn @click="openColumnsDialog" icon title="Show/Hide columns" style="margin-right:-10px; width:40px; height:40px;"><v-icon small>fas fa-cog</v-icon></v-btn>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="computedHeaders" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="id" show-select class="elevation-1" style="padding-top:5px;" mobile-breakpoint="0">
        <template v-ripple v-slot:[`header.data-table-select`]="{}">
          <v-simple-checkbox
            :value="items.length == 0 ? false : selected.length == items.length"
            :indeterminate="selected.length > 0 && selected.length != items.length"
            @click="selected.length == items.length ? selected = [] : selected = [...items]">
          </v-simple-checkbox>
        </template>
        <template v-slot:[`item.mode`]="{ item }">
          <div v-if="item.mode == 'full'">
            <v-icon small color="#EF5354" style="margin-right:5px; margin-bottom:4px">fas fa-star</v-icon>
            Full
          </div>
          <div v-else-if="item.mode == 'partial'">
            <v-icon small color="#ff9800" style="margin-right:5px; margin-bottom:4px">fas fa-star-half</v-icon>
            Partial
          </div>
        </template>
        <template v-slot:[`item.server_id`]="{ item }">
          <v-btn @click="getServer(item.server_id)" text class="text-body-2" style="text-transform:inherit; padding:0 5px; margin-left:-5px">
            <v-icon small :title="item.server_shared ? 'Shared' : 'Personal'" :color="item.server_shared ? '#EB5F5D' : 'warning'" style="margin-right:8px">
              {{ item.server_shared ? 'fas fa-users' : 'fas fa-user' }}
            </v-icon>
            {{ item.server_name }}
          </v-btn>
        </template>
        <template v-slot:[`item.size`]="{ item }">
          {{ formatBytes(item.size) }}
        </template>
        <template v-slot:[`item.status`]="{ item }">
          <v-icon v-if="item.status == 'QUEUED'" :title="`Queued: ${item.queue}`" small style="color: #3498db; margin-left:8px;">fas fa-clock</v-icon>
          <v-icon v-else-if="item.status == 'STARTING'" title="Starting" small style="color: #3498db; margin-left:8px;">fas fa-spinner</v-icon>
          <v-icon v-else-if="item.status == 'IN PROGRESS'" title="In Progress" small style="color: #ff9800; margin-left:8px;">fas fa-spinner</v-icon>
          <v-icon v-else-if="item.status == 'SUCCESS'" title="Success" small style="color: #4caf50; margin-left:9px;">fas fa-check</v-icon>
          <v-icon v-else-if="item.status == 'FAILED'" title="Failed" small style="color: #EF5354; margin-left:11px;">fas fa-times</v-icon>
          <v-icon v-else-if="item.status == 'STOPPED'" title="Stopped" small style="color: #EF5354; margin-left:8px;">fas fa-ban</v-icon>
        </template>
      </v-data-table>
    </v-card>
    <v-dialog v-model="deleteDialog" persistent max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-minus</v-icon>DELETE</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" icon @click="deleteDialog = false"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <div class="subtitle-1" style="margin-bottom:10px">Are you sure you want to delete the selected exports?</div>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :disabled="loading" color="#00b16a" @click="deleteSubmit()">Confirm</v-btn>
                  <v-btn :disabled="loading" color="#EF5354" @click="deleteDialog = false" style="margin-left:5px;">Cancel</v-btn>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!-------------------->
    <!-- COLUMNS DIALOG -->
    <!-------------------->
    <v-dialog v-model="columnsDialog" max-width="600px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="text-subtitle-1 white--text">FILTER COLUMNS</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="selectAllColumns" text title="Select all columns" style="height:100%"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-check-square</v-icon>Select all</v-btn>
          <v-btn @click="deselectAllColumns" text title="Deselect all columns" style="height:100%"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-square</v-icon>Deselect all</v-btn>
          <v-spacer></v-spacer>
          <v-btn icon @click="columnsDialog = false" style="width:40px; height:40px"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 0px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:15px; margin-bottom:20px;">
                  <div class="text-body-1" style="margin-bottom:10px">Select the columns to display:</div>
                  <v-checkbox v-model="columnsRaw" label="Mode" value="mode" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Server" value="server_id" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Database" value="database" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Size" value="size" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Status" value="status" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Started" value="started" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Ended" value="ended" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Overall" value="overall" hide-details style="margin-top:5px"></v-checkbox>
                  <v-divider style="margin-top:15px;"></v-divider>
                  <div style="margin-top:20px;">
                    <v-btn @click="filterColumns" :loading="loading" color="#00b16a">Confirm</v-btn>
                    <v-btn :disabled="loading" color="#EF5354" @click="columnsDialog = false" style="margin-left:5px;">Cancel</v-btn>
                  </div>
                </v-form>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import axios from 'axios';
import moment from 'moment';
import pretty from 'pretty-bytes';
import EventBus from '../event-bus'

export default {
  data: () => ({
    headers: [
      { text: 'Mode', align: 'left', value: 'mode' },
      { text: 'Server', align: 'left', value: 'server_id' },
      { text: 'Database', align: 'left', value: 'database' },
      { text: 'Size', align: 'left', value: 'size' },
      { text: 'Status', align:'left', value: 'status' },
      { text: 'Started', align: 'left', value: 'started' },
      { text: 'Ended', align: 'left', value: 'ended' },
      { text: 'Overall', align: 'left', value: 'overall' }
    ],
    items: [],
    selected: [],
    search: '',
    loading: false,
    // Delete Dialog
    deleteDialog: false,
    // Filter Columns Dialog
    columnsDialog: false,
    columns: ['mode','server_id','database','size','status','started','ended','overall'],
    columnsRaw: [],
  }),
  created() {
    this.getExports()
  },
  computed: {
    computedHeaders() { return this.headers.filter(x => this.columns.includes(x.value)) },
  },
  methods: {
    getExports() {
      this.loading = true
      // Get Exports
      axios.get('/utils/exports')
        .then((response) => {
          this.items = response.data.exports.map(x => ({...x, created: this.dateFormat(x.created), started: this.dateFormat(x.started), ended: this.dateFormat(x.ended), overall: this.parseOverall(x)}))
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    getServer(server_id) {
      EventBus.$emit('get-server', server_id)
    },
    deleteExport() {
      this.deleteDialog = true
    },
    deleteSubmit() {
      // Check export status
      if (this.selected.some(x => x.status == 'IN PROGRESS')) {
        EventBus.$emit('send-notification', "Can't delete exports that are in progress", '#EF5354')
        this.deleteDialog = false
        return
      }
      // Delete Exports
      this.loading = true
      const payload = this.selected.map(x => x.uri)
      axios.delete('/utils/exports', { data: payload })
        .then(() => {
          this.selected = []
          this.deleteDialog = false
          this.getExports()
          EventBus.$emit('send-notification', "Selected exports deleted", '#00b16a')
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    parseOverall(item) {
      if (item['started'] == null) return null
      let diff = (item['ended'] == null) ? moment.utc().diff(moment(item['started'])) : moment(item['ended']).diff(moment(item['started']))
      return moment.utc(diff).format("HH:mm:ss")
    },
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
    formatBytes(size) {
      if (size == null) return null
      return pretty(size, {binary: true}).replace('i','')
    },
    newExport() {
      this.$router.push({ name: 'utils.exports.new' })
    },
    infoExport() {
      this.$router.push({ name: 'utils.exports.info', params: { uri: this.selected[0]['uri'] }})
    },
    openColumnsDialog() {
      this.columnsRaw = [...this.columns]
      this.columnsDialog = true
    },
    selectAllColumns() {
      this.columnsRaw = ['mode','server_id','database','size','status','started','ended','overall']
    },
    deselectAllColumns() {
      this.columnsRaw = []
    },
    filterColumns() {
      this.columns = [...this.columnsRaw]
      this.columnsDialog = false
    },
  }
}
</script>