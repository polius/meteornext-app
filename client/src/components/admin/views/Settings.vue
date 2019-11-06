<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title>SETTINGS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down" style="padding-left:0px;">
          <v-btn text @click="setSetting('sql')"><v-icon small style="padding-right:10px">fas fa-database</v-icon>SQL</v-btn>
          <v-btn text @click="setSetting('api')"><v-icon small style="padding-right:10px">fas fa-plug</v-icon>API</v-btn>
          <v-btn text @click="setSetting('logs')"><v-icon small style="padding-right:10px">fas fa-paper-plane</v-icon>LOGS</v-btn>
        </v-toolbar-items>
      </v-toolbar>
      <v-container fluid grid-list-lg>
        <v-layout row wrap>
          <!-- SQL -->
          <v-flex v-if="setting_mode == 'sql'" xs12 style="margin-top:5px; margin-bottom:5px;">
            <div class="headline font-weight-regular" style="margin-left:10px;">SQL</div>
            <div v-if="!loading" class="body-1 font-weight-light font-italic" style="margin-left:10px; margin-top:10px; margin-bottom:25px;">{{ sql.path }}</div>
            <v-text-field readonly :loading="loading" :disabled="loading" v-model="sql.hostname" label="Hostname" style="margin-left:10px; padding-top:0px;" required :rules="[v => !!v || '']"></v-text-field>
            <v-text-field readonly :loading="loading" :disabled="loading" v-model="sql.username" label="Username" style="margin-left:10px; padding-top:0px;" required :rules="[v => !!v || '']"></v-text-field>
            <v-text-field readonly :loading="loading" :disabled="loading" v-model="sql.password" label="Password" style="margin-left:10px; padding-top:0px;" @click:append="show_password = !show_password" :append-icon="show_password ? 'visibility' : 'visibility_off'" :type="show_password ? 'text' : 'password'" required :rules="[v => !!v || '']"></v-text-field>
            <v-text-field readonly :loading="loading" :disabled="loading" v-model="sql.port" label="Port" style="margin-left:10px; padding-top:0px;" required :rules="[v => !!v || '']"></v-text-field>
            <v-text-field readonly :loading="loading" :disabled="loading" v-model="sql.database" label="Database" style="margin-left:10px; padding-top:0px;" required :rules="[v => !!v || '']"></v-text-field>
          </v-flex>

          <!-- API -->
          <v-flex v-else-if="setting_mode == 'api'" xs12 style="margin-top:5px; margin-bottom:5px;">
            <div class="headline font-weight-regular" style="margin-left:10px;">API</div>
            <div v-if="!loading" class="body-1 font-weight-light font-italic" style="margin-left:10px; margin-top:10px; margin-bottom:25px;">{{ api.path }}</div>
            <v-text-field readonly :loading="loading" :disabled="loading" v-model="api.host" label="Hostname" style="margin-left:10px; padding-top:0px;" required :rules="[v => !!v || '']"></v-text-field>
            <v-text-field readonly :loading="loading" :disabled="loading" v-model="api.port" label="Port" style="margin-left:10px; padding-top:0px;" required :rules="[v => !!v || '']"></v-text-field>
            <v-switch readonly :loading="loading" :disabled="loading" v-model="api.ssl" label="SSL Connection" color="success" style="margin-left:10px; margin-top:0px; margin-bottom:5px;" hide-details></v-switch>
          </v-flex>

          <!-- LOGS -->
          <v-flex v-else-if="setting_mode == 'logs'" xs12 style="margin-top:5px; margin-bottom:5px;">
            <div class="headline font-weight-regular" style="margin-left:10px; margin-bottom:10px;">LOGS</div>
            <v-btn :loading="loading" color="secondary" style="margin-left:10px;" @click="logs_mode = (logs_mode == 'local') ? '' : 'local'">LOCAL</v-btn>
            <v-btn :loading="loading" color="secondary" style="margin-left:10px;" @click="logs_mode = (logs_mode == 'amazon_s3') ? '' : 'amazon_s3'">AMAZON S3</v-btn>

            <v-card v-if="logs_mode == 'local'" style="margin-left:10px; margin-right:10px; margin-top:15px;">
              <v-toolbar flat dense color="#2e3131" style="margin-top:10px;">
                <v-toolbar-title class="white--text">LOCAL</v-toolbar-title>
                <v-divider class="mx-3" inset vertical></v-divider>
                <v-toolbar-items class="hidden-sm-and-down">
                 <v-btn text :disabled="loading" color="primary" @click="saveLogs()" style="margin-left:0px;">SAVE</v-btn>
                </v-toolbar-items>
              </v-toolbar>
              <v-divider></v-divider>
              <v-card-text style="padding-top:5px; padding-bottom:0px;">
                <v-form ref="form" style="padding:5px 5px 0px 5px;">
                  <v-text-field :loading="loading" :disabled="loading" v-model="logs.local" label="Absolute Path" required :rules="[v => !!v || '']" hide-details></v-text-field>
                  <v-switch :loading="loading" :disabled="loading" label="Expire Logs" style="margin-top:15px;" hide-details></v-switch>
                  <v-text-field :loading="loading" :disabled="loading" label="Log Retention Days" required :rules="[v => !!v || '', v => !isNaN(parseFloat(v)) && isFinite(v) && v >= 0 || '']" style="margin-top:15px;"></v-text-field>
                </v-form>
              </v-card-text>
            </v-card>

            <v-card v-else-if="logs_mode == 'amazon_s3'" style="margin-left:10px; margin-right:10px; margin-top:15px;">
              <v-toolbar flat dense color="#2e3131" style="margin-top:10px;">
                <v-toolbar-title class="white--text">Amazon S3</v-toolbar-title>
                <v-divider class="mx-3" inset vertical></v-divider>
                <v-toolbar-items class="hidden-sm-and-down">
                 <v-btn text :disabled="loading" color="primary" @click="saveLogs()" style="margin-left:0px;">SAVE</v-btn>
                </v-toolbar-items>
              </v-toolbar>
              <v-divider></v-divider>
              <v-card-text style="padding-top: 5px; padding-bottom:0px;">
                <v-form ref="form" style="padding:5px 5px 0px 5px;">
                  <v-text-field :loading="loading" :disabled="loading" v-model="logs.amazon_s3.aws_access_key" label="AWS Access Key" required :rules="[v => !!v || '']"></v-text-field>
                  <v-text-field :loading="loading" :disabled="loading" v-model="logs.amazon_s3.aws_secret_access_key" label="AWS Secret Access Key" style="padding-top:0px;" required :rules="[v => !!v || '']"></v-text-field>
                  <v-text-field :loading="loading" :disabled="loading" v-model="logs.amazon_s3.region_name" label="Region Name" style="padding-top:0px;" required :rules="[v => !!v || '']"></v-text-field>
                  <v-text-field :loading="loading" :disabled="loading" v-model="logs.amazon_s3.bucket_name" label="Bucket Name" style="padding-top:0px;" required :rules="[v => !!v || '']"></v-text-field>
                  <v-switch :loading="loading" :disabled="loading" v-model="logs.amazon_s3.enabled" label="Upload Logs to Amazon S3" style="margin-top:0px;"></v-switch>
                </v-form>
              </v-card-text>
            </v-card>
          </v-flex>

        </v-layout>
      </v-container>
    </v-card>

    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn color="white" text @click="snackbar = false">Close</v-btn>
    </v-snackbar>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data: () => ({
    // Settings
    setting_mode: 'sql',

    // SQL
    sql: {},
    show_password: false,

    // API
    api: {},

    // Logs
    logs: { local: '', amazon_s3: {} },
    logs_mode: 'local',

    // Loading
    loading: true,

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarColor: '',
    snackbarText: ''
  }),
  created() {
    this.getSettings()
  },
  methods: {
    getSettings() {
      const path = this.$store.getters.url + '/admin/settings'
      axios.get(path)
        .then((response) => {
          // Get Settings
          var settings = response.data.data
          settings['sql']['path'] += '/credentials.json'
          this.sql = settings['sql']
          this.api = settings['api']
          this.logs = settings['logs']

          // Disable Loading
          this.loading = false
        })
        .catch((error) => {
          if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
          // eslint-disable-next-line
          console.error(error)
        })
    },
    setSetting(setting) {
      this.setting_mode = setting
    },
    saveLogs() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please fill the required fields', 'error')
        return
      }
      // Disable the fields while updating fields to the DB
      this.loading = true
      // Parse local absolute path
      this.logs.local = (this.logs.local.endsWith('/')) ? this.logs.local : this.logs.local + '/'
      // Construct path & payload
      const path = this.$store.getters.url + '/admin/settings'
      const payload = { 
        name: 'logs',
        value: JSON.stringify(this.logs)
      }
      // Update Logs values to the DB
      axios.put(path, payload)
        .then((response) => {
          this.notification(response.data.message, 'success')
          this.loading = false
        })
        .catch((error) => {
          if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
          this.loading = false
          // eslint-disable-next-line
          console.error(error)
        })
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  }
}
</script>