<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">INFORMATION</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-btn v-if="information_items.length != 0 && information_items[0]['status'] == 'IN PROGRESS'" :disabled="stop" text title="Stop Execution" @click="stopExport" style="height:100%"><v-icon small style="margin-right:10px">fas fa-ban</v-icon>STOP</v-btn>
        <v-divider v-if="information_items.length != 0 && information_items[0]['status'] == 'IN PROGRESS'" class="mx-3" inset vertical></v-divider>
        <div v-if="information_items.length != 0 && information_items[0]['status'] == 'IN PROGRESS' && !stop" class="subtitle-1">Execution in progress...</div>
        <div v-if="information_items.length != 0 && information_items[0]['status'] == 'IN PROGRESS' && stop" class="subtitle-1">Stopping the execution...</div>
        <v-progress-circular v-if="information_items.length != 0 && information_items[0]['status'] == 'IN PROGRESS'" :size="22" indeterminate color="white" width="2" style="margin-left:20px"></v-progress-circular>
        <v-spacer></v-spacer>
        <div v-if="information_items.length != 0" class="subheading font-weight-regular" style="padding-right:10px;">Updated on <b>{{ dateFormat(information_items[0]['updated']) }}</b></div>
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
            <template v-slot:[`item.server`]="{ item }">
              <v-btn @click="getServer(item.server_id)" text class="text-body-2" style="text-transform:inherit; padding:0 5px; margin-left:-5px">
                <v-icon small :title="item.shared ? 'Shared' : 'Personal'" :color="item.shared ? '#EB5F5D' : 'warning'" style="margin-right:6px; margin-bottom:2px;">
                  {{ item.shared ? 'fas fa-users' : 'fas fa-user' }}
                </v-icon>
                {{ item.server }}
              </v-btn>
            </template>
            <template v-slot:[`item.size`]="{ item }">
              {{ formatBytes(item.size) }}
            </template>
            <template v-slot:[`item.status`]="{ item }">
              <v-icon v-if="item.status == 'IN PROGRESS'" title="In Progress" small style="color: #ff9800; margin-left:8px;">fas fa-spinner</v-icon>
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
              <div v-if="information_items[0].status == 'IN PROGRESS'" class="text-body-1"><v-icon title="In Progress" small style="color: #ff9800; margin-right:10px">fas fa-spinner</v-icon>Export in progress. Please wait...</div>
              <div v-else-if="information_items[0].status == 'SUCCESS'" class="text-body-1"><v-icon title="Success" small style="color: #4caf50; margin-right:10px">fas fa-check</v-icon>Export successfully finished.</div>
              <div v-else-if="information_items[0].status == 'FAILED'" class="text-body-1"><v-icon title="Failed" small style="color: #EF5354; margin-right:10px">fas fa-times</v-icon>An error occurred while exporting the database.</div>
              <div v-else-if="information_items[0].status == 'STOPPED'" class="text-body-1"><v-icon title="Stopped" small style="color: #EF5354; margin-right:10px">fas fa-ban</v-icon>Export successfully stopped.</div>
              <v-progress-linear :color="getProgressColor(information_items[0].status)" height="5" :indeterminate="information_items[0]['status'] == 'IN PROGRESS' && (progress == null || progress.value == 0)" :value="progress == null ? 0 : information_items[0].status == 'SUCCESS' ? 100 : progress.value" style="margin-top:10px"></v-progress-linear>
              <div v-if="progress != null" class="text-body-1" style="margin-top:10px">Progress: <span class="white--text" style="font-weight:500">{{ information_items[0].status == 'SUCCESS' ? '100 %' : (progress.value + ' %') }}</span></div>
              <v-divider v-if="progress != null" style="margin-top:10px"></v-divider>
              <div v-if="progress != null" class="text-body-1" style="margin-top:10px">Data Transferred: <span class="white--text">{{ progress.transferred }}</span></div>
              <div v-if="progress != null && progress.rate != null" class="text-body-1" style="margin-top:10px">Data Transfer Rate: <span class="white--text">{{ progress.rate }}</span></div>
              <div v-if="progress != null && progress.elapsed != null" class="text-body-1" style="margin-top:10px">Elapsed Time: <span class="white--text">{{ progress.elapsed }}</span></div>
              <div v-if="progress != null && progress.eta != null" class="text-body-1" style="margin-top:10px">ETA: <span class="white--text">{{ progress.eta }}</span></div>
              <v-divider v-if="information_items[0].status == 'SUCCESS'" style="margin-top:10px"></v-divider>
              <v-row v-if="information_items[0].status == 'SUCCESS'" no-gutters style="margin-top:15px">
                <v-col cols="auto">
                  <v-btn :href="information_items[0]['url']" target="_blank" color="primary">DOWNLOAD EXPORT</v-btn>
                </v-col>
                <v-col cols="auto" style="margin-left:5px">
                  <v-btn @click="copyClipboard(information_items[0]['url'])" title="Copy link" color="primary" style="min-width:50px"><v-icon size="0.875rem">fas fa-link</v-icon></v-btn>
                </v-col>
              </v-row>
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
              <div class="text-body-1 white--text">FORMAT</div>
              <v-radio-group readonly v-model="information_items[0]['format']" style="margin-top:10px; margin-bottom:15px" hide-details>
                <v-radio value="sql">
                  <template v-slot:label>
                    SQL
                  </template>
                </v-radio>
                <v-radio disabled value="csv">
                  <template v-slot:label>
                    CSV
                  </template>
                </v-radio>
              </v-radio-group>
              <div class="text-body-1 white--text">SETTINGS</div>
              <v-checkbox readonly v-model="information_items[0]['export_schema']" label="Export Schema (Add CREATE TABLE statements)." hide-details style="margin-top:10px"></v-checkbox>
              <v-checkbox readonly v-model="information_items[0]['export_data']" label="Export Data (Dump table contents)." hide-details style="margin-top:10px"></v-checkbox>
              <v-checkbox readonly :disabled="!information_items[0]['export_schema']" v-model="information_items[0]['add_drop_table']" label="Add Drop Table (Add DROP TABLE statement before each CREATE TABLE statement)." hide-details style="margin-top:10px"></v-checkbox>
            </v-card-text>
          </v-card>
          <!-- OBJECTS -->
          <div v-if="information_items[0]['mode'] == 'partial'" class="title font-weight-regular" style="margin-top:15px; margin-left:1px">OBJECTS</div>
          <v-card v-if="information_items[0]['mode'] == 'partial'" style="margin-top:10px; margin-left:1px">
            <v-card-text style="padding:15px">
              <v-data-table :headers="objectsHeaders" :items="objectsItems" hide-default-footer class="elevation-1" mobile-breakpoint="0">
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
    <!------------------->
    <!-- SERVER DIALOG -->
    <!------------------->
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
                    <v-col cols="6" style="padding-right:10px">
                      <v-text-field readonly v-model="server.name" label="Name"></v-text-field>
                    </v-col>
                    <v-col cols="6" style="padding-left:10px">
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
                <div class="subtitle-1" style="margin-bottom:10px">Are you sure you want to stop the export?</div>
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
    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
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

export default {
  data() {
    return {
      loading: false,
      timer: null,
      // Information
      information_headers: [
        { text: 'Mode', value: 'mode', sortable: false },
        { text: 'Server', value: 'server', sortable: false },
        { text: 'Database', value: 'database', sortable: false },
        { text: 'Size', value: 'size', sortable: false },
        { text: 'Status', value: 'status', sortable: false },
        { text: 'Started', value: 'started', sortable: false },
        { text: 'Ended', value: 'ended', sortable: false },
        { text: 'Overall', value: 'overall', sortable: false },
      ],
      information_items: [],
      // Progress
      progress: null,
      stop: false,
      // Objects
      objectsHeaders: [
        { text: 'Name', value: 'n' },
        { text: 'Rows', value: 'r' },
        { text: 'Size', value: 's' },
      ],
      objectsItems: [],
      objectsSize: 0,
      // Server Dialog
      serverDialog: false,
      server: {},
      showPassword: false,
      // Stop Dialog
      stopDialog: false,
      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarText: '',
      snackbarColor: '',
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
    this.getExport()
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
    getExport() {
      axios.get('/utils/export', { params: { uri: this.$route.params.uri } })
        .then((response) => {
          this.information_items = [response.data.export].map(x => ({...x, created: this.dateFormat(x.created), started: this.dateFormat(x.started), ended: this.dateFormat(x.ended)}))
          if (this.information_items[0]['mode'] == 'partial') this.objectsItems = JSON.parse(this.information_items[0]['tables'])['t']
          if (this.information_items[0]['progress'] != null) this.parseProgress(this.information_items[0]['progress'])
          if (this.information_items[0]['status'] == 'IN PROGRESS') {
            clearTimeout(this.timer)
            this.timer = setTimeout(this.getExport, 1000)
          }
          this.parseOverall()
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    parseProgress(progress) {
      this.progress = {
        value: parseInt(progress.value.slice(0, -1)),
        transferred: this.parseMetric(progress.transferred),
        rate: this.parseMetric(progress.rate),
        elapsed: progress.elapsed,
        eta: progress.eta
      }
    },
    parseOverall() {
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
      if (this.prevRoute.path == '/admin/utils/export') this.$router.push('/admin/utils/export')
      else this.$router.push('/utils/export')
    },
    getServer(server_id) {
      // Get Server
      this.loading = true
      this.showPassword = false
      this.serverDialog = true
      const payload = { server_id: server_id }
      axios.get('/inventory/servers', { params: payload })
        .then((response) => {
          // Build usage
          let usage = []
          if (response.data.data[0].usage.includes('D')) usage.push('Deployments')
          if (response.data.data[0].usage.includes('M')) usage.push('Monitoring')
          if (response.data.data[0].usage.includes('U')) usage.push('Utils')
          if (response.data.data[0].usage.includes('C')) usage.push('Client')
          // Add server
          this.server = {...response.data.data[0], usage: usage.join(', ')}
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    testConnection() {
      // Test Connection
      this.notification('Testing Server...', 'info')
      this.loading = true
      const payload = {
        region: this.server.region_id,
        server: this.server.id
      }
      axios.post('/inventory/servers/test', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    stopExport() {
      this.stopDialog = true
    },
    stopSubmit() {
      this.loading = true
      this.stop = true
      const payload = { uri: this.$route.params.uri }
      axios.post('/utils/export/stop', payload)
      .then(() => {
        this.stopDialog = false
      })
      .catch((error) => {
        this.stop = false
        if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
        else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
      })
      .finally(() => this.loading = false)
    },
    copyClipboard(text) {
        navigator.clipboard.writeText(text)
        this.notification('Link copied to clipboard', '#00b16a', Number(2000))
      },
    getProgressColor(status) {
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
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  },
}
</script>