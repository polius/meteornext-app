<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">SETTINGS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down" style="padding-left:0px;">
          <v-btn text @click="setSetting('license')"><v-icon small style="padding-right:10px">fas fa-certificate</v-icon>LICENSE</v-btn>
          <v-btn text @click="setSetting('sql')"><v-icon small style="padding-right:10px">fas fa-database</v-icon>SQL</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn text @click="setSetting('logs')"><v-icon small style="padding-right:10px">fas fa-folder-open</v-icon>LOGS</v-btn>
          <v-btn text @click="setSetting('security')"><v-icon small style="padding-right:10px">fas fa-shield-alt</v-icon>SECURITY</v-btn>
        </v-toolbar-items>
      </v-toolbar>
      <v-container fluid grid-list-lg>
        <v-layout row wrap>
          <!-- LICENSE -->
          <v-flex v-if="setting_mode == 'license'" xs12 style="margin:5px">
            <div class="text-h6 font-weight-regular">LICENSE</div>
            <div class="body-1 font-weight-regular" style="margin-top:10px">This copy of Meteor Next is <span class="body-1 font-weight-medium" style="color:#00b16a;">LICENSED</span>.</div>
            <v-text-field readonly :loading="loading" :disabled="loading" v-model="license.email" label="Email" style="margin-top:15px" required :rules="[v => !!v || '']"></v-text-field>
            <v-text-field readonly :loading="loading" :disabled="loading" v-model="license.key" label="Key" style="padding-top:0px;" @click:append="show_key = !show_key" :append-icon="show_key ? 'visibility' : 'visibility_off'" :type="show_key ? 'text' : 'password'" required :rules="[v => !!v || '']"></v-text-field>
            <v-text-field readonly :loading="loading" :disabled="loading" v-model="license.expiration" label="Expiration" style="padding-top:0px; margin-bottom:5px" required :rules="[v => !!v || '']" hide-details></v-text-field>
          </v-flex>
          <!-- SQL -->
          <v-flex v-else-if="setting_mode == 'sql'" xs12 style="margin:5px">
            <div class="text-h6 font-weight-regular">SQL</div>
            <div class="body-1 font-weight-regular" style="margin-top:10px">The SQL credentials where Meteor Next is stored.</div>
            <v-text-field readonly :loading="loading" :disabled="loading" v-model="sql.hostname" label="Hostname" style="margin-top:15px;" required :rules="[v => !!v || '']"></v-text-field>
            <v-text-field readonly :loading="loading" :disabled="loading" v-model="sql.port" label="Port" style="padding-top:0px;" required :rules="[v => !!v || '']"></v-text-field>
            <v-text-field readonly :loading="loading" :disabled="loading" v-model="sql.username" label="Username" style="padding-top:0px;" required :rules="[v => !!v || '']"></v-text-field>
            <v-text-field readonly :loading="loading" :disabled="loading" v-model="sql.password" label="Password" style="padding-top:0px;" @click:append="show_password = !show_password" :append-icon="show_password ? 'visibility' : 'visibility_off'" :type="show_password ? 'text' : 'password'" required :rules="[v => !!v || '']"></v-text-field>
            <v-text-field readonly :loading="loading" :disabled="loading" v-model="sql.database" label="Database" style="padding-top:0px; margin-bottom:5px" required :rules="[v => !!v || '']" hide-details></v-text-field>
            <v-card v-if="sql.ssl_client_key != null || sql.ssl_client_certificate != null || sql.ssl_ca_certificate != null" style="height:52px; margin-top:15px">
              <v-row no-gutters>
                <v-col cols="auto" style="display:flex; margin:15px">
                  <v-icon color="#00b16a" style="font-size:20px">fas fa-key</v-icon>
                </v-col>
                <v-col>
                  <div class="text-body-1" style="color:#00b16a; margin-top:15px">{{ 'Using a SSL connection (' + ssl_active + ')' }}</div>
                </v-col>
              </v-row>
            </v-card>
          </v-flex>
          <!-- LOGS -->
          <v-flex v-else-if="setting_mode == 'logs'" xs12 style="margin:5px">
            <div class="text-h6 font-weight-regular" style="margin-bottom:10px;">LOGS</div>
            <div class="body-1 font-weight-regular" style="margin-top:10px; margin-bottom:15px">The path where all the Deployments are stored.</div>
            <v-btn :loading="loading" color="secondary" @click="logs_mode = 'local'">LOCAL</v-btn>
            <v-btn :loading="loading" color="secondary" style="margin-left:10px;" @click="logs_mode = 'amazon_s3'">AMAZON S3</v-btn>
            <v-card v-if="logs_mode == 'local'" style="margin-top:15px">
              <v-toolbar flat dense color="#2e3131" style="margin-top:10px">
                <v-toolbar-title class="white--text subtitle-1">LOCAL</v-toolbar-title>
                <v-divider class="mx-3" inset vertical></v-divider>
                <v-toolbar-items class="hidden-sm-and-down">
                <v-btn text :disabled="loading" @click="saveLogs()">SAVE</v-btn>
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
            <v-card v-else-if="logs_mode == 'amazon_s3'" style="margin-top:15px">
              <v-toolbar flat dense color="#2e3131" style="margin-top:10px;">
                <v-toolbar-title class="white--text subtitle-1">AMAZON S3</v-toolbar-title>
                <v-divider class="mx-3" inset vertical></v-divider>
                <v-toolbar-items class="hidden-sm-and-down">
                 <v-btn text :disabled="loading" @click="saveLogs()" style="margin-left:0px;">SAVE</v-btn>
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
          <v-flex v-else-if="setting_mode == 'security'" xs12 style="margin:5px">
            <div class="text-h6 font-weight-regular">SECURITY</div>
            <div class="subtitle-1" style="margin-top:10px; color:#fa8131">Password Policy</div>
            <v-select :loading="loading" :disabled="loading" v-model="security.password_age" :items="[{id: 0, text: 'Never'}, {id: 90, text: '3 Months'}, {id: 180, text: '6 Months'}, {id: 365, text: '1 Year'}]" item-value="id" item-text="text" label="Maximum Password Age" style="margin-top:10px" hide-details></v-select>
            <v-select :loading="loading" :disabled="loading" v-model="security.password_min" :items="password_min" label="Minimum Password Length" style="margin-top:15px" hide-details></v-select>
            <v-checkbox v-model="security.password_lowercase" hide-details>
              <template v-slot:label>
                <div style="margin-left:5px">
                  <div class="body-1">Require lowercase character</div>
                  <div class="font-weight-regular caption" style="font-size:0.85rem !important">Password must contain at least one lowercase character.</div>
                </div>
              </template>
            </v-checkbox>
            <v-checkbox v-model="security.password_uppercase" hide-details>
              <template v-slot:label>
                <div style="margin-left:5px">
                  <div class="body-1">Require uppercase character</div>
                  <div class="font-weight-regular caption" style="font-size:0.85rem !important">Password must contain at least one uppercase character.</div>
                </div>
              </template>
            </v-checkbox>
            <v-checkbox v-model="security.password_number" hide-details>
              <template v-slot:label>
                <div style="margin-left:5px">
                  <div class="body-1">Require number</div>
                  <div class="font-weight-regular caption" style="font-size:0.85rem !important">Password must contain at least one number.</div>
                </div>
              </template>
            </v-checkbox>
            <v-checkbox v-model="security.password_special" hide-details>
              <template v-slot:label>
                <div style="margin-left:5px">
                  <div class="body-1">Require special character</div>
                  <div class="font-weight-regular caption" style="font-size:0.85rem !important">Password must contain at least one special character.</div>
                </div>
              </template>
            </v-checkbox>
            <div class="subtitle-1" style="margin-top:20px; color:#fa8131">Force MFA</div>
            <div class="body-1 font-weight-regular" style="margin-top:10px;">Force all users to have the MFA enabled.</div>
            <v-switch :loading="loading" :disabled="loading" v-model="security.mfa" label="Force Multi-Factor Authentication (MFA)" color="info" style="margin-top:10px" hide-details></v-switch>
            <div class="subtitle-1" style="margin-top:20px; color:#fa8131">Secure Access</div>
            <div class="body-1 font-weight-regular" style="margin-top:10px;">Restrict access to the Administration panel only to a specific IP address or domain.</div>
            <v-text-field :loading="loading" :disabled="loading" v-model="security.url" label="Administration URL" :placeholder="security.current" style="margin-top:10px" required :rules="[v => v ? this.validURL(v) : true || '' ]" hide-details></v-text-field>
            <v-btn :loading="loading" color="#00b16a" style="margin-top:25px" @click="saveSecurity()">SAVE</v-btn>
          </v-flex>
        </v-layout>
      </v-container>
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
    password_min: [],

    // Loading
    loading: true,

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarColor: '',
    snackbarText: ''
  }),
  created() {
    this.password_min = [...Array(60).keys()].map(i => i + 5)
    this.getSettings()
  },
  computed: {
    ssl_active: function() {
      let elements = []
      if (this.sql.ssl_client_key != null) elements.push('Client Key')
      if (this.sql.ssl_client_certificate != null) elements.push('Client Certificate')
      if (this.sql.ssl_ca_certificate != null) elements.push('CA Certificate')
      return elements.join(' + ')
    }
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
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    setSetting(setting) {
      this.setting_mode = setting
    },
    saveLogs() {
      // Check if all fields are filled
      if (!this.$refs.logs_form.validate()) {
        this.notification('Please fill the required fields', '#EF5354')
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
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
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
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
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