<template>
  <v-flex xs12 style="margin:5px">
    <div class="text-h6 font-weight-regular" style="margin-bottom:10px;"><v-icon small style="margin-right:10px; margin-bottom:3px; color:#fa8131">fas fa-folder-open</v-icon>FILES</div>
    <div class="body-1 font-weight-regular" style="margin-top:10px; margin-bottom:15px">The path where the application files are stored.</div>
    <v-form ref="files_form">
      <v-text-field :disabled="loading" v-model="files.local.path" label="Absolute Path" required :rules="[v => (v === undefined || v.startsWith('/'))]" hide-details></v-text-field>
      <v-text-field :disabled="loading" v-model="files.local.expire" label="Retention Days" :rules="[v => (v === undefined || (v == parseInt(v) && v > 0))]" style="margin-top:15px" hide-details></v-text-field>
      <v-switch :disabled="loading" v-model="files.amazon_s3.enabled" label="Store Deployments in Amazon S3" style="margin-top:20px" hide-details></v-switch>
      <div v-if="files.amazon_s3.enabled" style="margin-top:20px; margin-bottom:25px">
        <v-text-field :disabled="loading" v-model="files.amazon_s3.aws_access_key" label="AWS Access Key" :rules="[v => (!!v || !files.amazon_s3.enabled) || '']" :append-icon="showAccessKey ? 'mdi-eye' : 'mdi-eye-off'" :type="showAccessKey ? 'text' : 'password'" @click:append="showAccessKey = !showAccessKey"></v-text-field>
        <v-text-field :disabled="loading" v-model="files.amazon_s3.aws_secret_access_key" label="AWS Secret Access Key" style="padding-top:0px;" required :rules="[v => (!!v || !files.amazon_s3.enabled) || '']" :append-icon="showSecretAccessKey ? 'mdi-eye' : 'mdi-eye-off'" :type="showSecretAccessKey ? 'text' : 'password'" @click:append="showSecretAccessKey = !showSecretAccessKey"></v-text-field>
        <v-text-field :disabled="loading" v-model="files.amazon_s3.region" label="Region Name" placeholder="us-east-1, eu-west-1, ..." style="padding-top:0px;" required :rules="[v => (!!v || !logfiless.amazon_s3.enabled) || '']"></v-text-field>
        <v-text-field :disabled="loading" v-model="files.amazon_s3.bucket" label="Bucket Name" style="padding-top:0px;" required :rules="[v => (!!v || !files.amazon_s3.enabled) || '']" hide-details></v-text-field>
      </div>
    </v-form>
    <div style="margin-top:20px">
      <v-btn :disabled="loading" color="#00b16a" @click="saveFiles()">SAVE</v-btn>
      <v-btn v-if="files.amazon_s3.enabled" :loading="loading" color="primary" style="margin-left:10px" @click="testCredentials()">TEST CREDENTIALS</v-btn>
    </div>
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
    files: { local: {}, amazon_s3: {} },
    showAccessKey: false,
    showSecretAccessKey: false,
    loading: false,
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarColor: '',
    snackbarText: ''
  }),
  props: ['info','init'],
  mounted() {
    if (Object.keys(this.info).length > 0) this.files = JSON.parse(JSON.stringify(this.info))
  },
  watch: {
    info: function(val) {
      this.files = JSON.parse(JSON.stringify(val))
    },
    init: function(val) {
      this.loading = val
    }
  },
  methods: {
    saveFiles() {
      // Check if all fields are filled
      if (!this.$refs.files_form.validate()) {
        this.notification('Please fill the required fields', '#EF5354')
        return
      }
      // Disable the fields while updating fields to the DB
      this.loading = true
      // Parse local absolute path
      this.files.local.path = (this.files.local.path.endsWith('/')) ? this.files.local.path.slice(0, -1) : this.files.local.path
      // Parse local expiration
      if (!this.files.local.expire) this.files.local.expire = null
      // Parse amazon_s3 enable
      this.files.amazon_s3.enabled = ('enabled' in this.files.amazon_s3) ? this.files.amazon_s3.enabled : false
      // Construct path & payload
      const payload = this.files
      // Update Files values to the DB
      axios.post('/admin/settings/files', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    testCredentials() {
      this.loading = true
      const payload = this.files['amazon_s3']
      axios.post('/admin/settings/files/test', payload)
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