<template>
  <v-flex xs12 style="margin:5px">
    <div class="text-h6 font-weight-regular"><v-icon small style="margin-right:10px; margin-bottom:3px; color:#fa8131">fas fa-shield-alt</v-icon>SECURITY</div>
    <div class="subtitle-1" style="margin-top:10px; color:#fa8131">PASSWORD POLICY</div>
    <v-select :loading="loading" :disabled="loading" v-model="security.password_age" :items="[{id: 0, text: 'Never'}, {id: 90, text: '3 Months'}, {id: 180, text: '6 Months'}, {id: 365, text: '1 Year'}]" item-value="id" item-text="text" label="Maximum Password Age" style="margin-top:15px" hide-details></v-select>
    <v-text-field :loading="loading" :disabled="loading" v-model="security.password_min" label="Minimum Password Length" :rules="[v => v == parseInt(v) && v > 4 || '']" style="margin-top:15px" hide-details></v-text-field>
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
    <div class="subtitle-1" style="margin-top:20px; color:#fa8131">FORCE MFA</div>
    <div class="body-1 font-weight-regular" style="margin-top:10px;">Force all users to have the MFA enabled.</div>
    <v-switch :loading="loading" :disabled="loading" v-model="security.force_mfa" label="Force Multi-Factor Authentication (MFA)" color="info" style="margin-top:10px" hide-details></v-switch>
    <div class="subtitle-1" style="margin-top:20px; color:#fa8131">SECURE ADMIN</div>
    <div class="body-1 font-weight-regular" style="margin-top:10px;">Restrict access to the Administration panel only to a specific IP address or domain.</div>
    <v-text-field :loading="loading" :disabled="loading" v-model="security.restrict_url" label="Administration URL" :placeholder="currentUrl" style="margin-top:10px" required :rules="[v => v ? this.validURL(v) : true || '' ]" hide-details></v-text-field>
    <v-btn :loading="loading" color="#00b16a" style="margin-top:25px" @click="saveSecurity()">SAVE</v-btn>
    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </v-flex>
</template>

<script>
import axios from 'axios'

export default {
  data: () => ({
    security: {},
    currentUrl: '',
    loading: false,
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarColor: '',
    snackbarText: ''
  }),
  props: ['info','init'],
  created() {
    if (Object.keys(this.info).length > 0) {
      this.security = JSON.parse(JSON.stringify(this.info))
      this.currentUrl = this.security['current']
      delete this.security.current
    }
  },
  watch: {
    info: function(val) {
      this.security = JSON.parse(JSON.stringify(val))
      this.currentUrl = this.security['current']
      delete this.security.current
    },
    init: function(val) {
      this.loading = val
    }
  },
  methods: {
    saveSecurity() {
      // Parse URL value
      if (this.security.restrict_url.length > 0 && this.security.restrict_url.endsWith('/')) {
        this.security.restrict_url = this.restrict_url.url.slice(0, -1)
      }
      // Build payload
      this.loading = true
      const payload = this.security
      // Update Security values to the DB
      axios.post('/admin/settings/security', payload)
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
    },
  }
}
</script>