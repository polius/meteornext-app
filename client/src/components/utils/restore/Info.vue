<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">INFORMATION</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-spacer></v-spacer>
        <div class="subheading font-weight-regular" style="padding-right:10px;">Updated on <b>{{ /* dateFormat(last_updated) */ }}</b></div>
        <v-divider class="ml-3 mr-1" inset vertical></v-divider>
        <v-btn icon @click="goBack()"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
      </v-toolbar>
      <v-card-text>
        <!-- SUMMARY -->
        <v-card>
          <v-data-table :headers="information_headers" :items="information_items" hide-default-footer class="elevation-1">
            <template v-slot:[`item.mode`]="{ item }">
              <v-icon v-if="item.mode == 'file'" title="File" small style="margin-left:8px; color:#2196f3">fas fa-file</v-icon>
              <v-icon v-else-if="item.mode == 'url'" title="URL" small style="margin-left:5px; color:#2196f3">fas fa-cloud</v-icon>
              <v-icon v-else-if="item.mode == 's3'" title="Amazon S3" style="font-size:22; margin-left:1px; color:#2196f3">fab fa-aws</v-icon>
            </template>
            <template v-slot:[`item.server`]="{ item }">
              <v-btn @click="getServer(item.server_id)" text class="body-2" style="text-transform:inherit; padding:0 5px; margin-left:-5px">
                <v-icon small :title="item.shared ? 'Shared' : 'Personal'" :color="item.shared ? '#EB5F5D' : 'warning'" style="margin-right:6px; margin-bottom:2px;">
                  {{ item.shared ? 'fas fa-users' : 'fas fa-user' }}
                </v-icon>
                {{ item.server }}
              </v-btn>
            </template>
            <template v-slot:[`item.status`]="{ item }">
              <v-icon v-if="item.status == 'CREATED'" title="Created" small style="color: #3498db; margin-left:9px;">fas fa-check</v-icon>
              <v-icon v-else-if="item.status == 'SCHEDULED'" title="Scheduled" small style="color: #ff9800; margin-left:8px;">fas fa-clock</v-icon>
              <v-icon v-else-if="item.status == 'QUEUED'" :title="`${'Queued: ' + item.queue}`" small style="color: #3498db; margin-left:8px;">fas fa-clock</v-icon>
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
        <!-- FILE -->
        <div v-if="file != null" class="title font-weight-regular" style="margin-top:15px; margin-left:1px">FILE</div>
        <v-card v-if="file != null" style="margin-top:10px; margin-left:1px">
          <v-card-text style="padding:15px">
            <div class="body-1 font-weight-regular">{{ `${file.file} (${file.size})` }}</div>
          </v-card-text>
        </v-card>
        <!-- PROGRESS -->
        <div class="title font-weight-regular" style="margin-top:15px; margin-left:1px">PROGRESS</div>
        <v-card style="margin-top:10px; margin-left:1px">
          <v-card-text style="padding:15px">
            <div class="text-body-1 warning--text">Importing file. Please wait...</div>
            <div class="text-body-1 success--text" style="margin-top:10px">File was successfully imported.</div>
            <v-progress-linear color="info" height="5" :value="progressValue" style="margin-top:10px"></v-progress-linear>
          </v-card-text>
        </v-card>
        <!-- ERROR -->
        <div class="title font-weight-regular" style="margin-top:15px; margin-left:1px">ERROR</div>
        <v-card style="margin-top:10px">
          <v-card-text style="padding:15px">
            <div class="body-1 error--text">Message</div>
          </v-card-text>
        </v-card>
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
    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script>
import moment from 'moment'
import axios from 'axios'

export default {
  data() {
    return {
      loading: false,
      // Information
      information_headers: [
        { text: 'Name', value: 'name', sortable: false },
        { text: 'Mode', value: 'mode', sortable: false },
        { text: 'Server', value: 'server', sortable: false },
        { text: 'Database', value: 'database', sortable: false },
        { text: 'Status', value: 'status', sortable: false },
        { text: 'Started', value: 'started', sortable: false },
        { text: 'Ended', value: 'ended', sortable: false },
        { text: 'Overall', value: 'overall', sortable: false },
      ],
      information_items: [],

      // File
      file: null,

      // Progress
      progressValue: 0,
      error: '',

      // Server Dialog
      serverDialog: false,
      server: {},
      showPassword: false,

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
      axios.get('/restore', { params: { id: this.$route.params.id } })
        .then((response) => {
          this.information_items = [response.data.restore].map(x => ({...x, created: this.dateFormat(x.created), started: this.dateFormat(x.started), ended: this.dateFormat(x.ended)}))
          this.file = JSON.parse(this.information_items[0].source)
        })
        .catch((error) => {
          console.log(error)
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    goBack() {
      this.$router.push('/utils/restore')
    },
    getServer(server_id) {
      // Get Server
      this.loading = true
      this.showPassword = false
      this.serverDialog = true
      const payload = { server_id: server_id }
      axios.get('/admin/inventory/servers', { params: payload })
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
      axios.post('/admin/inventory/servers/test', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  },
}
</script>