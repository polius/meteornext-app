<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">INFORMATION</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-btn v-if="information_items.length != 0 && ['QUEUED','STARTING','IN PROGRESS','STOPPING'].includes(information_items[0]['status'])" :disabled="stop || (information_items.length != 0 && information_items[0]['status'] == 'STOPPING')" text title="Stop Execution" @click="stopClone" style="height:100%"><v-icon small style="margin-right:10px">fas fa-ban</v-icon>STOP</v-btn>
        <v-divider v-if="information_items.length != 0 && ['QUEUED','STARTING','IN PROGRESS','STOPPING'].includes(information_items[0]['status'])" class="mx-3" inset vertical></v-divider>
        <div v-if="information_items.length != 0 && information_items[0]['status'] == 'QUEUED'" class="subtitle-1" style="margin-left:5px;">Queue Position: <b>{{ information_items[0]['queue'] }}</b></div>
        <div v-if="information_items.length != 0 && information_items[0]['status'] == 'STARTING' && !stop" class="subtitle-1">Starting the execution...</div>
        <div v-if="information_items.length != 0 && information_items[0]['status'] == 'IN PROGRESS' && !stop" class="subtitle-1">Execution in progress...</div>
        <div v-if="(information_items.length != 0 && information_items[0]['status'] == 'STOPPING') || stop" class="subtitle-1">Stopping the execution...</div>
        <v-progress-circular v-if="information_items.length != 0 && ['QUEUED','STARTING','IN PROGRESS','STOPPING'].includes(information_items[0]['status'])" :size="22" indeterminate color="white" width="2" style="margin-left:20px"></v-progress-circular>
        <v-spacer></v-spacer>
        <div v-if="information_items.length != 0 && information_items[0]['updated'] != null" class="subheading font-weight-regular" style="padding-right:10px;">Updated on <b>{{ dateFormat(information_items[0]['updated']) }}</b></div>
        <v-divider class="ml-3 mr-1" inset vertical></v-divider>
        <v-btn icon @click="goBack()"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
      </v-toolbar>
      <v-card-text>
        <!-- SUMMARY -->
        <v-card>
          <v-data-table :headers="information_headers" :items="information_items" hide-default-footer class="elevation-1" mobile-breakpoint="0">
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
            <template v-slot:[`item.source_server`]="{ item }">
              <v-btn @click="getServer(item.source_server)" text class="text-body-2" style="text-transform:inherit; padding:0 5px; margin-left:-5px">
                <v-icon small :title="item.source_server_shared ? item.source_server_secured ? 'Shared (Secured)' : 'Shared' : item.source_server_secured ? 'Personal (Secured)' : 'Personal'" :color="item.source_server_shared ? '#EB5F5D' : 'warning'" :style="`margin-bottom:2px; ${!item.source_server_secured ? 'padding-right:8px' : ''}`">{{ item.source_server_shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                <v-icon v-if="item.source_server_secured" :title="item.source_server_shared ? 'Shared (Secured)' : 'Personal (Secured)'" :color="item.source_server_shared ? '#EB5F5D' : 'warning'" style="font-size:12px; padding-left:2px; padding-top:2px; padding-right:8px">fas fa-lock</v-icon>
                {{ item.source_server_name }}
              </v-btn>
            </template>
            <template v-slot:[`item.destination_server`]="{ item }">
              <v-btn @click="getServer(item.destination_server)" text class="text-body-2" style="text-transform:inherit; padding:0 5px; margin-left:-5px">
                <v-icon small :title="item.destination_server_shared ? item.destination_server_secured ? 'Shared (Secured)' : 'Shared' : item.destination_server_secured ? 'Personal (Secured)' : 'Personal'" :color="item.destination_server_shared ? '#EB5F5D' : 'warning'" :style="`margin-bottom:2px; ${!item.destination_server_secured ? 'padding-right:8px' : ''}`">{{ item.destination_server_shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                <v-icon v-if="item.destination_server_secured" :title="item.destination_server_shared ? 'Shared (Secured)' : 'Personal (Secured)'" :color="item.destination_server_shared ? '#EB5F5D' : 'warning'" style="font-size:12px; padding-left:2px; padding-top:2px; padding-right:8px">fas fa-lock</v-icon>
                {{ item.destination_server_name }}
              </v-btn>
            </template>
            <template v-slot:[`item.size`]="{ item }">
              {{ formatBytes(item.size) }}
            </template>
            <template v-slot:[`item.status`]="{ item }">
              <v-icon v-if="item.status == 'QUEUED'" :title="`${'Queued: ' + item.queue}`" small style="color: #3498db; margin-left:8px;">fas fa-clock</v-icon>
              <v-icon v-else-if="item.status == 'STARTING'" title="Starting" small style="color: #3498db; margin-left:8px;">fas fa-spinner</v-icon>
              <v-icon v-else-if="item.status == 'IN PROGRESS'" title="In Progress" small style="color: #ff9800; margin-left:8px;">fas fa-spinner</v-icon>
              <v-icon v-else-if="item.status == 'SUCCESS'" title="Success" small style="color: #4caf50; margin-left:9px;">fas fa-check</v-icon>
              <v-icon v-else-if="item.status == 'FAILED'" title="Failed" small style="color: #EF5354; margin-left:11px;">fas fa-times</v-icon>
              <v-icon v-else-if="item.status == 'STOPPED'" title="Stopped" small style="color: #EF5354; margin-left:8px;">fas fa-ban</v-icon>
            </template>
          </v-data-table>
        </v-card>
        <div v-if="information_items.length > 0">
          <!-- PROGRESS -->
          <div class="title font-weight-regular" style="margin-top:15px; margin-left:1px">PROGRESS</div>
          <v-card style="margin-top:10px; margin-left:1px">
            <v-card-text style="padding:15px">
              <div v-if="information_items[0].status == 'QUEUED'" class="text-body-1"><v-icon title="Queued" small style="color: #3498db; margin-right:10px; margin-bottom:2px">fas fa-clock</v-icon>Cloning process queued. Waiting to be started...</div>
              <div v-else-if="information_items[0].status == 'STARTING'" class="text-body-1"><v-icon title="Starting" small style="color: #3498db; margin-right:10px; margin-bottom:2px">fas fa-spinner</v-icon>Starting the execution...</div>
              <div v-else-if="information_items[0].status == 'IN PROGRESS'" class="text-body-1"><v-icon title="In Progress" small style="color: #ff9800; margin-right:10px; margin-bottom:2px">fas fa-spinner</v-icon>{{ `[${step}/2] Clone in progress. Please wait...` }}</div>
              <div v-else-if="information_items[0].status == 'SUCCESS'" class="text-body-1"><v-icon title="Success" small style="color: #4caf50; margin-right:10px; margin-bottom:2px">fas fa-check</v-icon>Clone successfully finished.</div>
              <div v-else-if="information_items[0].status == 'FAILED'" class="text-body-1"><v-icon title="Failed" small style="color: #EF5354; margin-right:10px; margin-bottom:2px">fas fa-times</v-icon>An error occurred while cloning the database.</div>
              <div v-else-if="information_items[0].status == 'STOPPED'" class="text-body-1"><v-icon title="Stopped" small style="color: #EF5354; margin-right:10px; margin-bottom:2px">fas fa-ban</v-icon>Clone successfully stopped.</div>
              <v-progress-linear v-if="progress != null" :color="getProgressColor(information_items[0].status)" height="5" :indeterminate="information_items[0]['status'] == 'IN PROGRESS' && (progress == null || progress.value == 0)" :value="progress == null ? 0 : information_items[0].status == 'SUCCESS' ? 100 : progress.value" style="margin-top:10px"></v-progress-linear>
              <div v-if="progress != null" class="text-body-1" style="margin-top:10px">Progress: <span class="white--text" style="font-weight:500">{{ information_items[0].status == 'SUCCESS' ? '100 %' : (progress.value + ' %') }}</span></div>
              <v-divider v-if="progress != null" style="margin-top:10px"></v-divider>
              <div v-if="progress != null" class="text-body-1" style="margin-top:10px">Data Transferred: <span class="white--text">{{ progress.transferred }}</span></div>
              <div v-if="progress != null && progress.rate != null" class="text-body-1" style="margin-top:10px">Data Transfer Rate: <span class="white--text">{{ progress.rate }}</span></div>
              <div v-if="progress != null && progress.elapsed != null" class="text-body-1" style="margin-top:10px">Elapsed Time: <span class="white--text">{{ progress.elapsed }}</span></div>
              <div v-if="progress != null && progress.eta != null" class="text-body-1" style="margin-top:10px">ETA: <span class="white--text">{{ progress.eta }}</span></div>
            </v-card-text>
          </v-card>
          <!-- ERROR -->
          <div v-if="information_items[0].status == 'FAILED'">
            <div class="title font-weight-regular" style="margin-top:15px; margin-left:1px">ERROR</div>
            <v-card style="margin-top:10px; margin-left:1px">
              <v-card-text style="padding:15px">
                <div v-if="information_items[0].error != null" class="text-body-1">{{ information_items[0].error }}</div>
              </v-card-text>
            </v-card>
          </div>
          <!-- SETUP -->
          <div class="title font-weight-regular" style="margin-top:15px; margin-left:1px">SETUP</div>
          <v-card style="margin-top:10px; margin-left:1px">
            <v-card-text style="padding:15px">
              <div class="text-body-1 white--text">MODE</div>
              <v-radio-group readonly v-model="information_items[0]['mode']" style="margin-top:10px; margin-bottom:15px" hide-details>
                <v-radio value="full">
                  <template v-slot:label>
                    FULL
                  </template>
                </v-radio>
                <v-radio value="partial">
                  <template v-slot:label>
                    PARTIAL
                  </template>
                </v-radio>
              </v-radio-group>
              <div class="text-body-1 white--text">SETTINGS</div>
              <v-checkbox v-if="information_items[0]['create_database']" readonly v-model="information_items[0]['create_database']" label="Create database" hide-details style="margin-top:10px"></v-checkbox>
              <v-checkbox v-else readonly v-model="information_items[0]['recreate_database']" label="Recreate database" hide-details style="margin-top:10px"></v-checkbox>
              <v-checkbox readonly v-model="information_items[0]['export_schema']" label="Export Schema (Add CREATE TABLE statements)." hide-details style="margin-top:10px"></v-checkbox>
              <v-checkbox readonly v-model="information_items[0]['export_data']" label="Export Data (Dump table contents)." hide-details style="margin-top:10px"></v-checkbox>
              <v-checkbox readonly :disabled="!information_items[0]['export_schema']" v-model="information_items[0]['add_drop_table']" label="Add Drop Table (Add DROP TABLE statement before each CREATE TABLE statement)." hide-details style="margin-top:10px"></v-checkbox>
            </v-card-text>
          </v-card>
          <!-- OBJECTS -->
          <div v-if="information_items[0]['mode'] == 'partial'" class="title font-weight-regular" style="margin-top:15px; margin-left:1px">OBJECTS</div>
          <v-card v-if="information_items[0]['mode'] == 'partial'" style="margin-top:10px; margin-left:1px">
            <v-card-text style="padding:15px">
              <v-data-table :headers="objectsHeaders" :items="objectsItems" class="elevation-1" mobile-breakpoint="0">
                <template v-slot:[`item.s`]="{ item }">
                  {{ formatBytes(item.s) }}
                </template>
              </v-data-table>
              <div class="text-body-1" style="margin-top:15px">Size: <span class="white--text" style="font-weight:500">{{ formatBytes(information_items[0]['size']) }}</span></div>
              <div class="text-body-1 white--text" style="margin-top:15px">OPTIONS</div>
              <v-checkbox readonly v-model="information_items[0]['export_triggers']" label="Export Triggers" hide-details style="margin-top:10px"></v-checkbox>
              <v-checkbox readonly v-model="information_items[0]['export_routines']" label="Export Routines (Functions and Procedures)" hide-details style="margin-top:10px"></v-checkbox>
              <v-checkbox readonly v-model="information_items[0]['export_events']" label="Export Events" hide-details style="margin-top:10px"></v-checkbox>
            </v-card-text>
          </v-card>
        </div>
      </v-card-text>
    </v-card>
    <!----------------->
    <!-- STOP DIALOG -->
    <!----------------->
    <v-dialog v-model="stopDialog" persistent max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-ban</v-icon>STOP</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" icon @click="stopDialog = false"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <div class="subtitle-1" style="margin-bottom:10px">Are you sure you want to stop the clone?</div>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :disabled="loading" color="#00b16a" @click="stopSubmit()">Confirm</v-btn>
                  <v-btn :disabled="loading" color="#EF5354" @click="stopDialog = false" style="margin-left:5px;">Cancel</v-btn>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<style scoped>
.v-data-table
  ::v-deep tr:hover:not(.v-data-table__selected) {
  background: transparent !important;
}
</style>

<script>
import moment from 'moment'
import axios from 'axios'
import pretty from 'pretty-bytes'
import EventBus from '../event-bus'

export default {
  data() {
    return {
      loading: false,
      timer: null,
      // Information
      information_headers: [
        { text: 'Mode', value: 'mode', sortable: false },
        { text: 'S.Server', align: 'left', value: 'source_server' },
        { text: 'S.Database', align: 'left', value: 'source_database' },
        { text: 'D.Server', align: 'left', value: 'destination_server' },
        { text: 'D.Database', align: 'left', value: 'destination_database' },
        { text: 'Size', value: 'size', sortable: false },
        { text: 'Status', value: 'status', sortable: false },
        { text: 'Started', value: 'started', sortable: false },
        { text: 'Ended', value: 'ended', sortable: false },
        { text: 'Overall', value: 'overall', sortable: false },
      ],
      information_items: [],
      // Progress
      progress: null,
      step: 1,
      stop: false,
      // Objects
      objectsHeaders: [
        { text: 'Name', value: 'n' },
        { text: 'Rows', value: 'r' },
        { text: 'Size', value: 's' },
      ],
      objectsItems: [],
      objectsSize: 0,
      // Stop Dialog
      stopDialog: false,
      // Previous Route
      prevRoute: null
    }
  },
  beforeRouteEnter(to, from, next) {
    next(vm => {
      vm.prevRoute = from
    })
  },
  created() {
    this.getClone()
  },
  methods: {
    onGridReady(params) {
      this.gridApi = params.api
      this.columnApi = params.columnApi
    },
    resizeTable() {
      setTimeout(() => {
        var allColumnIds = [];
        this.columnApi.getAllColumns().forEach(function(column) {
          allColumnIds.push(column.colId);
        })
        this.columnApi.autoSizeColumns(allColumnIds);
      },0)
    },
    getClone() {
      axios.get('/utils/clones', { params: { uri: this.$route.params.uri } })
        .then((response) => {
          this.information_items = [response.data.clone].map(x => ({...x, created: this.dateFormat(x.created), started: this.dateFormat(x.started), ended: this.dateFormat(x.ended)}))
          // Get Tables (if mode == 'partial')
          if (this.information_items[0]['mode'] == 'partial') this.objectsItems = JSON.parse(this.information_items[0]['tables'])['t']
          // Calculate progress
          if (this.information_items[0]['progress_import'] != null) {
            this.step = 2
            this.progress = this.parseProgress(this.information_items[0]['progress_import'])
          }
          else this.progress = this.parseProgress(this.information_items[0]['progress_export'])
          // Retrieve again
          if (['QUEUED','STARTING','IN PROGRESS'].includes(this.information_items[0]['status'])) {
            clearTimeout(this.timer)
            this.timer = setTimeout(this.getClone, 1000)
          }
          this.parseOverall()
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    parseProgress(progress) {
      if (progress == null) return null
      const data = {
        value: parseInt(progress.value.slice(0, -1)),
        transferred: this.parseMetric(progress.transferred),
        rate: this.parseMetric(progress.rate),
        elapsed: progress.elapsed,
        eta: progress.eta
      }
      return data
    },
    parseOverall() {
      if (this.information_items[0]['started'] == null) return null
      let diff = (this.information_items[0]['ended'] == null) ? moment.utc().diff(moment(this.information_items[0]['started'])) : moment(this.information_items[0]['ended']).diff(moment(this.information_items[0]['started']))
      this.information_items[0]['overall'] = moment.utc(diff).format("HH:mm:ss")
    },
    parseMetric(val) {
      for (let i = val.length; i >= 0; --i) {
        if (Number.isInteger(parseInt(val[i]))) {
          return val.substring(0, i+1) + ' ' + val.substring(i+1, val.length)
        }
      }
      return val
    },
    goBack() {
      if (this.prevRoute.path == '/admin/utils/clones') this.$router.push('/admin/utils/clones')
      else this.$router.push('/utils/clones')
    },
    getServer(server_id) {
      EventBus.$emit('get-server', server_id)
    },
    stopClone() {
      this.stopDialog = true
    },
    stopSubmit() {
      this.loading = true
      this.stop = true
      const payload = { uri: this.$route.params.uri }
      axios.post('/utils/clones/stop', payload)
      .then(() => {
        this.stopDialog = false
      })
      .catch((error) => {
        this.stop = false
        if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
        else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
      })
      .finally(() => this.loading = false)
    },
    copyClipboard(text) {
        navigator.clipboard.writeText(text)
        EventBus.$emit('send-notification', 'Link copied to clipboard', '#00b16a', Number(2000))
      },
    getProgressColor(status) {
      if (status == 'QUEUED') return '#2196f3'
      if (status == 'STARTING') return '#3498db'
      if (status == 'IN PROGRESS') return '#ff9800'
      if (status == 'SUCCESS') return '#4caf50'
      if (['FAILED','STOPPED'].includes('FAILED')) return '#EF5354'
    },
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
    formatBytes(size) {
      if (size == null) return null
      return pretty(size, {binary: true}).replace('i','')
    },
  },
}
</script>