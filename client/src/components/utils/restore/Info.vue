<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">INFORMATION</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-btn v-if="information_items.length != 0 && information_items[0]['status'] == 'IN PROGRESS'" :disabled="stop" text title="Stop Execution" @click="stopRestore" style="height:100%"><v-icon small style="margin-right:10px">fas fa-ban</v-icon>STOP</v-btn>
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
          <v-data-table :headers="information_headers" :items="information_items" hide-default-footer class="elevation-1">
            <template v-slot:[`item.mode`]="{ item }">
              <div v-if="item.mode == 'file'">
                <v-icon :title="`${item.source} (${formatBytes(item.size)})`" small color="#23cba7" style="margin-right:5px; margin-bottom:3px">fas fa-file</v-icon>
                File
              </div>
              <div v-else-if="item.mode == 'url'">
                <v-icon :title="`${item.source} (${formatBytes(item.size)})`" small color="#19b5fe" style="margin-right:5px; margin-bottom:2px">fas fa-cloud</v-icon>
                URL
              </div>
              <div v-else-if="item.mode == 's3'">
                <v-icon :title="`${item.source} (${formatBytes(item.size)})`" color="#e47911" style="font-size:22; margin-right:5px; margin-bottom:2px">fab fa-aws</v-icon>
                Amazon S3
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
            <template v-slot:[`item.status`]="{ item }">
              <v-icon v-if="item.status == 'IN PROGRESS'" title="In Progress" small style="color: #ff9800; margin-left:8px;">fas fa-spinner</v-icon>
              <v-icon v-else-if="item.status == 'SUCCESS'" title="Success" small style="color: #4caf50; margin-left:9px;">fas fa-check</v-icon>
              <v-icon v-else-if="item.status == 'FAILED'" title="Failed" small style="color: #EF5354; margin-left:11px;">fas fa-times</v-icon>
              <v-icon v-else-if="item.status == 'STOPPED'" title="Stopped" small style="color: #EF5354; margin-left:8px;">fas fa-ban</v-icon>
            </template>
          </v-data-table>
        </v-card>
        <div v-if="information_items.length > 0">
          <!-- SOURCE -->
          <div class="title font-weight-regular" style="margin-top:15px; margin-left:1px">SOURCE</div>
          <v-card style="margin-top:10px; margin-left:1px">
            <v-card-text style="padding:15px">
              <div class="text-body-1 font-weight-regular">{{ `${information_items[0].source} (${formatBytes(information_items[0].size)})` }}</div>
              <div v-if="information_items[0].selected != null" style="margin-top:15px">
                <v-toolbar dense flat color="#2e3131" style="border-top-left-radius:5px; border-top-right-radius:5px;">
                  <v-text-field v-model="selectedSearch" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
                </v-toolbar>
                <v-data-table readonly :headers="selectedHeaders" :items="information_items[0].selected" :search="selectedSearch" :hide-default-footer="information_items[0].selected.length < 11" loading-text="Loading... Please wait" item-key="file" class="elevation-1">
                  <template v-slot:[`item.size`]="{ item }">
                    {{ formatBytes(item.size) }}
                  </template>
                </v-data-table>
                <div class="text-body-1" style="margin-top:20px">Total Size: <span class="white--text" style="font-weight:500">{{ formatBytes(information_items[0].selected.reduce((a, b) => a + b.size, 0)) }}</span></div>
              </div>
            </v-card-text>
          </v-card>
          <!-- PROGRESS -->
          <div class="title font-weight-regular" style="margin-top:15px; margin-left:1px">PROGRESS</div>
          <v-card style="margin-top:10px; margin-left:1px">
            <v-card-text style="padding:15px">
              <div v-if="information_items[0].status == 'IN PROGRESS'" class="text-body-1"><v-icon title="In Progress" small style="color: #ff9800; margin-right:10px">fas fa-spinner</v-icon>Importing file. Please wait...</div>
              <div v-else-if="information_items[0].status == 'SUCCESS'" class="text-body-1"><v-icon title="Success" small style="color: #4caf50; margin-right:10px">fas fa-check</v-icon>File was successfully imported.</div>
              <div v-else-if="information_items[0].status == 'FAILED'" class="text-body-1"><v-icon title="Failed" small style="color: #EF5354; margin-right:10px">fas fa-times</v-icon>An error occurred while importing the file.</div>
              <v-progress-linear :color="getProgressColor(information_items[0].status)" height="5" :value="progress.value" style="margin-top:10px"></v-progress-linear>
              <div class="text-body-1" style="margin-top:10px">Progress: <span :style="`font-weight:500; color:${getProgressColor(information_items[0].status)}`">{{ `${progress.value} %` }}</span></div>
              <v-divider style="margin-top:10px"></v-divider>
              <div class="text-body-1" style="margin-top:10px">Bytes Transferred: <span class="white--text">{{ progress.transferred }}</span></div>
              <div class="text-body-1" style="margin-top:10px">Data Transfer Rate: <span class="white--text">{{ progress.rate }}</span></div>
              <div class="text-body-1" style="margin-top:10px">Elapsed Time: <span class="white--text">{{ progress.elapsed }}</span></div>
              <div v-if="progress.eta != null" class="text-body-1" style="margin-top:10px">ETA: <span class="white--text">{{ progress.eta }}</span></div>
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
        </div>
      </v-card-text>
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
                    <v-col cols="8" style="padding-right:10px">
                      <v-text-field readonly v-model="server.name" label="Name"></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-left:10px">
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
                <div class="subtitle-1" style="margin-bottom:10px">Are you sure you want to stop the restore?</div>
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
        { text: 'Status', value: 'status', sortable: false },
        { text: 'Started', value: 'started', sortable: false },
        { text: 'Ended', value: 'ended', sortable: false },
        { text: 'Overall', value: 'overall', sortable: false },
      ],
      information_items: [],
      
      // Selected
      selectedHeaders: [
        { text: 'File', value: 'file',  width: '10%' },
        { text: 'Size', value: 'size' },
      ],
      selectedSearch: '',

      // Progress
      progress: {},
      stop: false,

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
    }
  },
  created() {
    this.getRestore()
  },
  methods: {
    getRestore() {
      axios.get('/utils/restore', { params: { id: this.$route.params.id } })
        .then((response) => {
          this.information_items = [response.data.restore].map(x => ({...x, selected: x.selected != null ? JSON.parse(x.selected) : null, created: this.dateFormat(x.created), started: this.dateFormat(x.started), ended: this.dateFormat(x.ended)}))
          this.parseProgress(this.information_items[0]['progress'])
          if (this.information_items[0]['status'] == 'IN PROGRESS') {
            clearTimeout(this.timer)
            this.timer = setTimeout(this.getRestore, 1000)
          }
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    parseProgress(progress) {
      let data = progress.split(' ')
      this.progress = {
        value: data[0].slice(0, -1),
        transferred: this.parseMetric(data[1]),
        rate: this.parseMetric(data[2]),
        elapsed: data[3],
        eta: data.length == 5 ? data[4] : null
      }
      // Calculate Overall
      let diff = (this.information_items[0]['ended'] == null) ? moment.utc().diff(moment(this.information_items[0]['started'])) : moment(this.information_items[0]['ended']).diff(moment(this.information_items[0]['started']))
      this.information_items[0]['overall'] = moment.utc(diff).format("HH:mm:ss")
    },
    parseMetric(val) {
      console.log(val)
      for (let i = val.length; i >= 0; --i) {
        if (Number.isInteger(parseInt(val[i]))) {
          return val.substring(0, i+1) + ' ' + val.substring(i+1, val.length)
        }
      }
      return val
    },
    goBack() {
      this.$router.back()
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
          if (response.data.servers[0].usage.includes('D')) usage.push('Deployments')
          if (response.data.servers[0].usage.includes('M')) usage.push('Monitoring')
          if (response.data.servers[0].usage.includes('U')) usage.push('Utils')
          if (response.data.servers[0].usage.includes('C')) usage.push('Client')
          // Add server
          this.server = {...response.data.servers[0], usage: usage.join(', ')}
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
        region_id: this.server.region_id,
        server: { engine: this.server.engine, hostname: this.server.hostname, port: this.server.port, username: this.server.username, password: this.server.password }
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
    stopRestore() {
      this.stopDialog = true
    },
    stopSubmit() {
      this.loading = true
      this.stop = true
      const payload = { id: this.$route.params.id }
      axios.post('/utils/restore/stop', payload)
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
    getProgressColor(status) {
      if (status == 'IN PROGRESS') return '#ff9800'
      if (status == 'SUCCESS') return '#4caf50'
      if (status == 'FAILED') return '#EF5354'
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