<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title>SETTINGS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down" style="padding-left:0px;">
          <v-btn text @click="setSetting('license')"><v-icon small style="padding-right:10px">fas fa-certificate</v-icon>LICENSE</v-btn>
          <v-btn text @click="setSetting('sql')"><v-icon small style="padding-right:10px">fas fa-database</v-icon>SQL</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn text @click="setSetting('logs')"><v-icon small style="padding-right:10px">fas fa-scroll</v-icon>LOGS</v-btn>
          <v-btn text @click="setSetting('security')"><v-icon small style="padding-right:10px">fas fa-shield-alt</v-icon>SECURITY</v-btn>
        </v-toolbar-items>
      </v-toolbar>
      <v-container fluid grid-list-lg>
        <v-layout row wrap>
          <!-- LICENSE -->
          <v-flex v-if="setting_mode == 'license'" xs12 style="margin-top:5px; margin-bottom:5px;">
            <div class="headline font-weight-regular" style="margin-left:10px;">LICENSE</div>
            <div class="body-1 font-weight-regular" style="margin-left:10px; margin-top:10px;">This copy of Meteor Next is <span class="body-1 font-weight-medium" style="color:#00b16a;">LICENSED</span></div>
            <v-text-field readonly :loading="loading" :disabled="loading" v-model="license.email" label="Email" style="margin-left:10px; padding-top:25px;" required :rules="[v => !!v || '']"></v-text-field>
            <v-text-field readonly :loading="loading" :disabled="loading" v-model="license.key" label="Key" style="margin-left:10px; padding-top:0px;" @click:append="show_key = !show_key" :append-icon="show_key ? 'visibility' : 'visibility_off'" :type="show_key ? 'text' : 'password'" required :rules="[v => !!v || '']"></v-text-field>
          </v-flex>

          <!-- SQL -->
          <v-flex v-else-if="setting_mode == 'sql'" xs12 style="margin-top:5px; margin-bottom:5px;">
            <div class="headline font-weight-regular" style="margin-left:10px;">SQL</div>
            <div class="body-1 font-weight-regular" style="margin-left:10px; margin-top:10px;">The SQL credentials where Meteor Next is stored</div>
            <v-text-field readonly :loading="loading" :disabled="loading" v-model="sql.hostname" label="Hostname" style="margin-left:10px; padding-top:25px;" required :rules="[v => !!v || '']"></v-text-field>
            <v-text-field readonly :loading="loading" :disabled="loading" v-model="sql.username" label="Username" style="margin-left:10px; padding-top:0px;" required :rules="[v => !!v || '']"></v-text-field>
            <v-text-field readonly :loading="loading" :disabled="loading" v-model="sql.password" label="Password" style="margin-left:10px; padding-top:0px;" @click:append="show_password = !show_password" :append-icon="show_password ? 'visibility' : 'visibility_off'" :type="show_password ? 'text' : 'password'" required :rules="[v => !!v || '']"></v-text-field>
            <v-text-field readonly :loading="loading" :disabled="loading" v-model="sql.port" label="Port" style="margin-left:10px; padding-top:0px;" required :rules="[v => !!v || '']"></v-text-field>
            <v-text-field readonly :loading="loading" :disabled="loading" v-model="sql.database" label="Database" style="margin-left:10px; padding-top:0px;" required :rules="[v => !!v || '']"></v-text-field>
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
                <v-form ref="logs_form" style="padding:5px 5px 0px 5px;">
                  <v-text-field :loading="loading" :disabled="loading" v-model="logs.local.path" label="Absolute Path" required :rules="[v => !!v || '', v => v.startsWith('/') || '']" hide-details></v-text-field>
                  <v-text-field :loading="loading" :disabled="loading" v-model="logs.local.expire" label="Log Retention Days" :rules="[v => v ? v == parseInt(v) && v > 0 : true || '']" style="margin-top:15px;"></v-text-field>
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
                <v-form ref="logs_form" style="padding:5px 5px 0px 5px;">
                  <v-text-field :loading="loading" :disabled="loading" v-model="logs.amazon_s3.aws_access_key" label="AWS Access Key" :rules="[v => (!!v || !logs.amazon_s3.enabled) || '']"></v-text-field>
                  <v-text-field :loading="loading" :disabled="loading" v-model="logs.amazon_s3.aws_secret_access_key" label="AWS Secret Access Key" style="padding-top:0px;" required :rules="[v => (!!v || !logs.amazon_s3.enabled) || '']"></v-text-field>
                  <v-text-field :loading="loading" :disabled="loading" v-model="logs.amazon_s3.region_name" label="Region Name" style="padding-top:0px;" required :rules="[v => (!!v || !logs.amazon_s3.enabled) || '']"></v-text-field>
                  <v-text-field :loading="loading" :disabled="loading" v-model="logs.amazon_s3.bucket_name" label="Bucket Name" style="padding-top:0px;" required :rules="[v => (!!v || !logs.amazon_s3.enabled) || '']"></v-text-field>
                  <v-switch :loading="loading" :disabled="loading" v-model="logs.amazon_s3.enabled" label="Upload Logs to Amazon S3" color="info" style="margin-top:0px;"></v-switch>
                </v-form>
              </v-card-text>
            </v-card>
          </v-flex>

          <!-- SECURITY -->
          <v-flex v-else-if="setting_mode == 'security'" xs12 style="margin-top:5px; margin-bottom:5px;">
            <div class="headline font-weight-regular" style="margin-left:10px;">SECURITY</div>
            <div class="body-1 font-weight-regular" style="margin-left:10px; margin-top:10px;">Restrict access to the <span class="body-1 font-weight-medium" style="color:rgb(250, 130, 49);">Administration</span> panel only to a specific IP address or domain</div>
            <v-text-field :loading="loading" :disabled="loading" v-model="security.url" label="Administration URL" :placeholder="security.current" style="margin-left:10px; margin-top:12px;" required :rules="[v => v ? this.validURL(v) : true || '' ]"></v-text-field>
            <v-btn :loading="loading" color="#00b16a" style="margin-left:10px;" @click="saveSecurity()">SAVE</v-btn>
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
    setting_mode: 'license',

    // LICENSE
    license: {},
    show_key: false,

    // SQL
    sql: {},
    show_password: false,

    // Logs
    logs: { local: {}, amazon_s3: {} },
    logs_mode: 'local',

    // Security
    security: {},

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
      axios.get('/admin/settings')
        .then((response) => {
          // Get Settings
          var settings = response.data.data
          this.license = settings['license']
          this.sql = settings['sql']
          this.logs = settings['logs']
          this.security = settings['security']

          // Disable Loading
          this.loading = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    setSetting(setting) {
      this.setting_mode = setting
    },
    saveLogs() {
      // Check if all fields are filled
      if (!this.$refs.logs_form.validate()) {
        this.notification('Please fill the required fields', 'error')
        return
      }
      // Disable the fields while updating fields to the DB
      this.loading = true
      // Parse local absolute path
      this.logs.local.path = (this.logs.local.path.endsWith('/')) ? this.logs.local.path.slice(0, -1) : this.logs.local.path
      // Parse local expiration
      if (!this.logs.local.expire) this.logs.local.expire = null
      // Parse amazon_s3 enable
      this.logs.amazon_s3.enabled = ('enabled' in this.logs.amazon_s3) ? this.logs.amazon_s3.enabled : false
      // Construct path & payload
      const payload = { 
        name: 'logs',
        value: JSON.stringify(this.logs)
      }
      // Update Logs values to the DB
      axios.put('/admin/settings', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
        })
    },
    saveSecurity() {
      // Parse URL value
      this.security.url = (this.security.url.endsWith('/')) ? this.security.url.slice(0, -1) : this.security.url
      // Delete current url value
      delete this.security.current
      // Build payload
      this.loading = true
      const payload = { 
        name: 'security',
        value: JSON.stringify(this.security)
      }
      // Update Security values to the DB
      axios.put('/admin/settings', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
        })
    },
    validURL(str) {
      var pattern = new RegExp('^(https?:\\/\\/)?'+ // protocol
        '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|'+ // domain name
        '((\\d{1,3}\\.){3}\\d{1,3}))'+ // OR ip (v4) address
        '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*'+ // port and path
        '(\\?[;&a-z\\d%_.~+=-]*)?'+ // query string
        '(\\#[-a-z\\d_]*)?$','i'); // fragment locator
      return !!pattern.test(str);
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  }
}
</script>