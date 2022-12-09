<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">INFORMATION</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-btn v-if="information_items.length != 0 && ['QUEUED','STARTING','IN PROGRESS','STOPPING'].includes(information_items[0]['status'])" :disabled="stop || (information_items.length != 0 && information_items[0]['status'] == 'STOPPING')" text title="Stop Execution" @click="stopImport" style="height:100%"><v-icon small style="margin-right:10px">fas fa-ban</v-icon>STOP</v-btn>
        <v-divider v-if="information_items.length != 0 && ['QUEUED','STARTING','IN PROGRESS','STOPPING'].includes(information_items[0]['status'])" class="mx-3" inset vertical></v-divider>
        <div v-if="information_items.length != 0 && information_items[0]['status'] == 'QUEUED'" class="subtitle-1" style="margin-left:5px;">Queue Position: <b>{{ information_items[0]['queue'] }}</b></div>
        <div v-else-if="information_items.length != 0 && information_items[0]['status'] == 'STARTING' && !stop" class="subtitle-1">Starting the execution...</div>
        <div v-else-if="information_items.length != 0 && information_items[0]['status'] == 'IN PROGRESS' && !stop" class="subtitle-1">Execution in progress...</div>
        <div v-else-if="information_items.length != 0 && (information_items[0]['status'] == 'STOPPING' || (information_items[0]['status'] != 'STOPPED' && stop))" class="subtitle-1">Stopping the execution...</div>
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
              <div v-if="item.mode == 'file'">
                <v-icon :title="`${item.source} (${formatBytes(item.size)})`" small color="#23cba7" style="margin-right:5px; margin-bottom:3px">fas fa-file</v-icon>
                File
              </div>
              <div v-else-if="item.mode == 'url'">
                <v-icon :title="`${item.source} (${formatBytes(item.size)})`" small color="#ff9800" style="margin-right:5px; margin-bottom:2px">fas fa-link</v-icon>
                URL
              </div>
              <div v-else-if="item.mode == 'cloud'">
                <v-icon :title="`${item.source} (${formatBytes(item.size)})`" color="#19b5fe" style="font-size:18px; margin-right:5px; margin-bottom:3px">fas fa-cloud</v-icon>
                Cloud
              </div>
            </template>
            <template v-slot:[`item.server_id`]="{ item }">
              <v-btn @click="getServer(item.server_id)" text class="text-body-2" style="text-transform:inherit; padding:0 5px; margin-left:-5px">
                <v-icon small :title="item.server_shared ? item.server_secured ? 'Shared (Secured)' : 'Shared' : item.server_secured ? 'Personal (Secured)' : 'Personal'" :color="item.server_shared ? '#EB5F5D' : 'warning'" :style="`margin-bottom:2px; ${!item.server_secured ? 'padding-right:8px' : ''}`">{{ item.server_shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                <v-icon v-if="item.server_secured" :title="item.server_shared ? 'Shared (Secured)' : 'Personal (Secured)'" :color="item.server_shared ? '#EB5F5D' : 'warning'" style="font-size:12px; padding-left:2px; padding-top:2px; padding-right:8px">fas fa-lock</v-icon>
                {{ item.server_name }}
              </v-btn>
            </template>
            <template v-slot:[`item.status`]="{ item }">
              <v-icon v-if="item.status == 'QUEUED'" :title="`${'Queued: ' + item.queue}`" small style="color: #3498db; margin-left:8px;">fas fa-clock</v-icon>
              <v-icon v-else-if="item.status == 'STARTING'" title="Starting" small style="color: #3498db; margin-left:8px;">fas fa-spinner</v-icon>
              <v-icon v-else-if="item.status == 'IN PROGRESS'" title="In Progress" small style="color: #ff9800; margin-left:8px;">fas fa-spinner</v-icon>
              <v-icon v-else-if="item.status == 'SUCCESS'" title="Success" small style="color: #4caf50; margin-left:9px;">fas fa-check</v-icon>
              <v-icon v-else-if="item.status == 'FAILED'" title="Failed" small style="color: #EF5354; margin-left:11px;">fas fa-times</v-icon>
              <v-icon v-else-if="item.status == 'STOPPING'" title="Stopping" small style="color: #ff9800; margin-left:8px;">fas fa-ban</v-icon>
              <v-icon v-else-if="item.status == 'STOPPED'" title="Stopped" small style="color: #EF5354; margin-left:8px;">fas fa-ban</v-icon>
            </template>
          </v-data-table>
        </v-card>
        <div v-if="information_items.length > 0">
          <!-- PROGRESS -->
          <div class="title font-weight-regular" style="margin-top:15px; margin-left:1px">PROGRESS</div>
          <v-card style="margin-top:10px; margin-left:1px">
            <v-card-text style="padding:15px">
              <div v-if="information_items[0].status == 'QUEUED'" class="text-body-1"><v-icon title="Queued" small style="color: #3498db; margin-right:10px; margin-bottom:2px">fas fa-clock</v-icon>Importing process queued. Waiting to be started...</div>
              <div v-else-if="information_items[0].status == 'STARTING'" class="text-body-1"><v-icon title="Starting" small style="color: #3498db; margin-right:10px; margin-bottom:2px">fas fa-spinner</v-icon>Starting the execution...</div>
              <div v-else-if="information_items[0].status == 'IN PROGRESS'" class="text-body-1"><v-icon title="In Progress" small style="color: #ff9800; margin-right:10px; margin-bottom:2px">fas fa-spinner</v-icon>{{ (information_items[0]['progress'] == null && information_items[0]['upload'] != null) ? "Transferring file to server's region. Please wait..." : 'Importing the file. Please wait...' }}</div>
              <div v-else-if="information_items[0].status == 'SUCCESS'" class="text-body-1"><v-icon title="Success" small style="color: #4caf50; margin-right:10px; margin-bottom:2px">fas fa-check</v-icon>File successfully imported.</div>
              <div v-else-if="information_items[0].status == 'FAILED'" class="text-body-1"><v-icon title="Failed" small style="color: #EF5354; margin-right:10px; margin-bottom:2px">fas fa-times</v-icon>An error occurred while importing the file.</div>
              <div v-else-if="information_items[0].status == 'STOPPING'" class="text-body-1"><v-icon title="Stopping" small style="color: #ff9800; margin-right:10px; margin-bottom:2px">fas fa-ban</v-icon>Stopping the execution...</div>
              <div v-else-if="information_items[0].status == 'STOPPED'" class="text-body-1"><v-icon title="Stopped" small style="color: #EF5354; margin-right:10px; margin-bottom:2px">fas fa-ban</v-icon>Import successfully stopped.</div>
              <v-progress-linear v-if="progress != null" :color="getProgressColor(information_items[0].status)" height="5" :indeterminate="information_items[0]['status'] == 'IN PROGRESS' && (progress == null || progress.value == 0)" :value="progress == null ? 0 : progress.value" style="margin-top:10px"></v-progress-linear>
              <div v-if="progress != null && progress.value != null" class="text-body-1" style="margin-top:10px">Progress: <span class="white--text" style="font-weight:500">{{ `${progress.value} %` }}</span></div>
              <v-divider v-if="progress != null && progress.transferred != null" style="margin-top:10px"></v-divider>
              <div v-if="progress != null && progress.transferred != null" class="text-body-1" style="margin-top:10px">Data Transferred: <span class="white--text">{{ progress.transferred }}</span></div>
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
                <div v-if="information_items[0].error != null" class="text-body-1">
                  {{ information_items[0].error.startsWith('[CHECK]') ? information_items[0].error.slice(8) : information_items[0].error }}
                  <span v-if="information_items[0].error.startsWith('[CHECK]')">See the <a href="https://docs.meteornext.io/requirements.html#utils" target="_blank">requirements</a>.</span>
                </div>
              </v-card-text>
            </v-card>
          </div>
          <!-- SOURCE -->
          <div class="title font-weight-regular" style="margin-top:15px; margin-left:1px">SOURCE</div>
          <v-card style="margin-top:10px; margin-left:1px">
            <v-card-text style="padding:15px">
              <div v-if="['file','url'].includes(information_items[0]['mode'])" class="text-body-1 font-weight-regular">{{ `${information_items[0].source} ${formatBytes(information_items[0].size) == null ? '' : ('(' + formatBytes(information_items[0].size) + ')')}` }}</div>
              <div v-else>
                <div class="subtitle-1 white--text" style="margin-bottom:15px">CLOUD KEY</div>
                <v-data-table :headers="cloudKeysHeaders" :items="cloudKeysItems" item-key="id" hide-default-footer class="elevation-1" mobile-breakpoint="0">
                  <template v-slot:item="{ item }">
                    <tr>
                      <td v-for="header in cloudKeysHeaders" :key="header.value">
                        <div v-if="header.value == 'type'">
                          <v-icon v-if="item.type == 'aws'" size="22" color="#e47911" title="Amazon Web Services">fab fa-aws</v-icon>
                          <v-icon v-else-if="item.type == 'google'" size="20" color="#4285F4" title="Google Cloud" style="margin-left:4px">fab fa-google</v-icon>
                        </div>
                        <div v-else-if="header.value == 'shared'">
                          <v-icon v-if="!item.shared" small title="Personal" color="warning" style="margin-right:6px; margin-bottom:2px">fas fa-user</v-icon>
                          <v-icon v-else small title="Shared" color="#EB5F5D" style="margin-right:6px; margin-bottom:2px">fas fa-users</v-icon>
                          {{ !item.shared ? 'Personal' : 'Shared' }}
                        </div>
                        <div v-else>
                          {{ item[header.value] }}
                        </div>
                      </td>
                    </tr>
                  </template>
                </v-data-table>
                <div class="subtitle-1 white--text" style="margin-top:15px; margin-bottom:15px">OBJECT</div>
                <div class="text-body-1" style="margin-bottom:15px">{{ bucket + '/' + awsObjectsItems[0]['key'] }}</div>
                <v-data-table :headers="awsObjectsHeaders" :items="awsObjectsItems" item-key="name" hide-default-footer class="elevation-1" mobile-breakpoint="0">
                  <template v-slot:item="{ item }">
                    <tr>
                      <td v-for="header in awsObjectsHeaders" :key="header.value">
                        <span v-if="header.value == 'name'">
                          <v-icon size="16" :color="item['name'].endsWith('/') ? '#e47911' : '#23cba7'" style="margin-right:10px; margin-bottom:2px">{{ item['name'].endsWith('/') ? 'fas fa-folder' : 'far fa-file'}}</v-icon>
                          {{ item.name }}
                        </span>
                        <span v-else-if="header.value == 'type'">
                          {{ item['name'].endsWith('/') ? 'Folder' : item['name'].indexOf('.') == '-1' ? '-' : item['name'].substring(item['name'].lastIndexOf(".") + 1) }}
                        </span>
                        <span v-else-if="header.value == 'size'">
                          {{ formatBytes(item.size) }}
                        </span>
                        <span v-else>{{ item[header.value] }}</span>
                      </td>
                    </tr>
                  </template>
                </v-data-table>
              </div>
              <div v-if="selectedItems != null">
                <div class="subtitle-1 white--text" style="margin-top:15px; margin-bottom:15px">FILES</div>
                <v-toolbar dense flat color="#2e3131" style="border-top-left-radius:5px; border-top-right-radius:5px;">
                  <v-text-field v-model="selectedSearch" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
                </v-toolbar>
                <v-data-table readonly :headers="selectedHeaders" :items="selectedItems" :search="selectedSearch" :hide-default-footer="selectedItems.length < 11" loading-text="Loading... Please wait" item-key="file" class="elevation-1" mobile-breakpoint="0">
                  <template v-slot:[`item.size`]="{ item }">
                    {{ formatBytes(item.size) }}
                  </template>
                </v-data-table>
                <div class="text-body-1" style="margin-top:20px">Total Size: <span class="white--text" style="font-weight:500">{{ formatBytes(selectedItems.reduce((a, b) => a + b.size, 0)) }}</span></div>
              </div>
            </v-card-text>
          </v-card>
          <div class="title font-weight-regular" style="margin-top:15px; margin-left:1px">SETUP</div>
          <v-card style="margin-top:10px; margin-left:1px">
            <v-card-text style="padding:15px">
              <v-checkbox v-if="information_items[0]['create_database']" readonly v-model="information_items[0]['create_database']" label="Create database" hide-details style="margin:0px; padding:0px"></v-checkbox>
              <v-checkbox v-else readonly v-model="information_items[0]['recreate_database']" label="Recreate database" hide-details style="margin:0px; padding:0px"></v-checkbox>
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
                <div class="subtitle-1" style="margin-bottom:10px">Are you sure you want to stop the import?</div>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :loading="loading" color="#00b16a" @click="stopSubmit()">Confirm</v-btn>
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
        { text: 'Server', value: 'server_id', sortable: false },
        { text: 'Database', value: 'database', sortable: false },
        { text: 'Status', value: 'status', sortable: false },
        { text: 'Started', value: 'started', sortable: false },
        { text: 'Ended', value: 'ended', sortable: false },
        { text: 'Overall', value: 'overall', sortable: false },
      ],
      information_items: [],
      // Cloud
      cloudKeysHeaders: [
        { text: 'Name', align: 'left', value: 'name' },
        { text: 'Type', align: 'left', value: 'type' },
        { text: 'Access Key', align: 'left', value: 'access_key'},
        { text: 'Scope', align: 'left', value: 'shared' },
      ],
      cloudKeysItems: [],
      // AWS Objects
      bucket: null,
      awsObjectsHeaders: [
        { text: 'Name', align: 'left', value: 'name' },
        { text: 'Type', align: 'left', value: 'type' },
        { text: 'Last Modified', align: 'left', value: 'last_modified' },
        { text: 'Size', align: 'left', value: 'size' },
        { text: 'Storage Class', align: 'left', value: 'storage_class' },
      ],
      awsObjectsItems: [],
      // Selected
      selectedHeaders: [
        { text: 'File', value: 'file',  width: '50%' },
        { text: 'Size', value: 'size' },
      ],
      selectedItems: [],
      selectedSearch: '',
      // Progress
      progress: null,
      stop: false,
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
    this.getImport()
  },
  methods: {
    getImport() {
      axios.get('/utils/imports', { params: { uri: this.$route.params.uri } })
        .then((response) => {
          this.information_items = [response.data.import].map(x => ({...x, source: x.mode == 'cloud' ? JSON.parse(x.details)['bucket'] + '/' + x.source : x.source, created: this.dateFormat(x.created), started: this.dateFormat(x.started), ended: this.dateFormat(x.ended)}))
          if (this.information_items[0]['mode'] == 'cloud') {
            const details = JSON.parse(this.information_items[0]['details'])
            this.cloudKeysItems = [details['cloud']]
            this.bucket = details['bucket']
            this.awsObjectsItems = [details['object']]
          }
          this.selectedItems = this.information_items[0]['selected']
          if (this.information_items[0]['upload'] != null) this.parseUpload(this.information_items[0]['upload'])
          if (this.information_items[0]['progress'] != null) this.parseProgress(this.information_items[0]['progress'])
          if (['QUEUED','STARTING','IN PROGRESS','STOPPING'].includes(this.information_items[0]['status'])) {
            clearTimeout(this.timer)
            this.timer = setTimeout(this.getImport, 1000)
          }
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    parseUpload(upload) {
      this.progress = {
        value: upload.value,
        transferred: this.formatBytes(upload.transferred)
      }
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
    parseMetric(val) {
      for (let i = val.length; i >= 0; --i) {
        if (Number.isInteger(parseInt(val[i]))) {
          return val.substring(0, i+1) + ' ' + val.substring(i+1, val.length)
        }
      }
      return val
    },
    goBack() {
      if (this.prevRoute == null) this.$router.push('/utils/imports')
      this.$router.back()
    },
    getServer(server_id) {
      EventBus.$emit('get-server', server_id)
    },
    stopImport() {
      this.stopDialog = true
    },
    stopSubmit() {
      this.loading = true
      this.stop = true
      const payload = { uri: this.$route.params.uri }
      axios.post('/utils/imports/stop', payload)
      .then(() => {
        this.stopDialog = false
      })
      .catch((error) => {
        this.stop = false
        if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
        else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
      })
      .finally(() => this.loading = false)
    },
    getProgressColor(status) {
      if (status == 'QUEUED') return '#2196f3'
      if (status == 'STARTING') return '#3498db'
      if (['IN PROGRESS','STOPPING'].includes(status)) return '#ff9800'
      if (status == 'SUCCESS') return '#4caf50'
      if (['FAILED','STOPPED'].includes('FAILED')) return '#EF5354'
    },
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
    formatBytes(size) {
      if (size == null || size === undefined) return null
      return pretty(size, {binary: true}).replace('i','')
    },
  },
}
</script>