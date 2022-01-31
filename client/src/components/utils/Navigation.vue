<template>
  <v-main>
    <div>
      <v-tabs background-color="#019875" color="white" slider-color="white" slot="extension" class="elevation-2">
        <v-tabs-slider></v-tabs-slider>
        <v-tab disabled style="opacity:1"><span class="pl-2 pr-2 white--text"><v-icon small style="margin-right:10px">fas fa-database</v-icon>UTILS</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-tab to="/utils/imports"><span class="pl-2 pr-2"><v-icon size="14" style="margin-right:10px">fas fa-arrow-up</v-icon>Imports</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-tab to="/utils/exports"><span class="pl-2 pr-2"><v-icon size="14" style="margin-right:10px">fas fa-arrow-down</v-icon>Exports</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-tab to="/utils/clones"><span class="pl-2 pr-2"><v-icon size="14" style="margin-right:10px">fas fa-clone</v-icon>Clones</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
      </v-tabs>
    </div>
    <v-container fluid style="padding:10px!important">
      <v-main style="padding-top:0px; padding-bottom:0px">
        <v-slide-y-transition mode="out-in">
          <router-view/>
        </v-slide-y-transition>
      </v-main>
    </v-container>
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
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form">
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
                  <v-row v-if="'hostname' in server" no-gutters>
                    <v-col cols="8" style="padding-right:10px">
                      <v-text-field readonly v-model="server.hostname" label="Hostname" style="padding-top:0px;"></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-left:10px">
                      <v-text-field readonly v-model="server.port" label="Port" style="padding-top:0px;"></v-text-field>
                    </v-col>
                  </v-row>
                  <v-text-field v-if="'username' in server" readonly v-model="server.username" label="Username" style="padding-top:0px;"></v-text-field>
                  <v-text-field v-if="'password' in server" readonly v-model="server.password" label="Password" :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'" :type="showPassword ? 'text' : 'password'" @click:append="showPassword = !showPassword" style="padding-top:0px;" :hide-details="!server.ssl && !server.ssh"></v-text-field>
                  <!-- SSL -->
                  <v-card v-if="server.ssl" style="height:52px; margin-bottom:15px">
                    <v-row no-gutters>
                      <v-col cols="auto" style="display:flex; margin:15px">
                        <v-icon color="#00b16a" style="font-size:20px">fas fa-key</v-icon>
                      </v-col>
                      <v-col>
                        <div class="text-body-1" style="color:#00b16a; margin-top:15px">Using a SSL connection</div>
                      </v-col>
                    </v-row>
                  </v-card>
                  <!-- SSH -->
                  <v-card v-if="server.ssh" style="height:52px; margin-bottom:15px">
                    <v-row no-gutters>
                      <v-col cols="auto" style="display:flex; margin:15px">
                        <v-icon color="#2196f3" style="font-size:20px">fas fa-terminal</v-icon>
                      </v-col>
                      <v-col>
                        <div class="text-body-1" style="color:#2196f3; margin-top:15px">Using a SSH connection</div>
                      </v-col>
                    </v-row>
                  </v-card>
                  <v-text-field readonly outlined v-model="server.usage" label="Usage" hide-details :style="`${'hostname' in server || server.ssl || server.ssh ? 'margin-top:20px' : ''}`"></v-text-field>
                </v-form>
                <v-divider style="margin-top:15px"></v-divider>
                <v-row no-gutters style="margin-top:15px">
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
  </v-main>
</template>

<script>
import axios from 'axios'
import EventBus from './event-bus'

export default {
  data() {
    return {
      // Server Dialog
      loading: false,
      serverDialog: false,
      server: {},
      showPassword: false,

      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarText: '',
      snackbarColor: ''
    }
  },
  mounted() {
    EventBus.$on('get-server', this.getServer)
    EventBus.$on('send-notification', this.notification)
  },
  methods: {
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
        server: this.server.id,
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
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color
      this.snackbar = true
    },
  }
}
</script>