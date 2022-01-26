<template>
  <v-flex xs12 style="margin:5px">
    <div class="text-h6 font-weight-regular" style="margin-bottom:10px;"><v-icon style="font-size:20px; margin-right:10px; color:#fa8131">fab fa-aws</v-icon>AMAZON S3</div>
    <div class="body-1 font-weight-regular" style="margin-top:10px; margin-bottom:15px">The AWS credentials to use the Amazon S3 storage engine.</div>
    <div class="body-2 font-weight-regular" style="margin-top:10px; margin-bottom:15px">Meteor Next works better with AWS. We strongly recommend to use Amazon S3 to ensure the data persistent of the application.</div>
    <v-form ref="amazon_form">
      <v-switch :disabled="loading" v-model="amazon.enabled" label="Use Amazon S3" style="margin-top:15px" hide-details></v-switch>
      <div v-if="amazon.enabled" style="margin-top:20px; margin-bottom:25px">
        <v-text-field :disabled="loading" v-model="amazon.aws_access_key" label="AWS Access Key" :rules="[v => (!!v || !amazon.enabled) || '']" :append-icon="showAccessKey ? 'mdi-eye' : 'mdi-eye-off'" :type="showAccessKey ? 'text' : 'password'" @click:append="showAccessKey = !showAccessKey"></v-text-field>
        <v-text-field :disabled="loading" v-model="amazon.aws_secret_access_key" label="AWS Secret Access Key" style="padding-top:0px;" required :rules="[v => (!!v || !amazon.enabled) || '']" :append-icon="showSecretAccessKey ? 'mdi-eye' : 'mdi-eye-off'" :type="showSecretAccessKey ? 'text' : 'password'" @click:append="showSecretAccessKey = !showSecretAccessKey"></v-text-field>
        <v-text-field :disabled="loading" v-model="amazon.region" label="Region Name" placeholder="us-east-1, eu-west-1, ..." style="padding-top:0px;" required :rules="[v => (!!v || !amazon.enabled) || '']"></v-text-field>
        <v-text-field :disabled="loading" v-model="amazon.bucket" label="Bucket Name" style="padding-top:0px;" required :rules="[v => (!!v || !amazon.enabled) || '']" hide-details></v-text-field>
      </div>
    </v-form>
    <div style="margin-top:20px">
      <v-btn :disabled="loading" color="#00b16a" @click="saveAmazon()"><v-icon small style="margin-right:10px">fas fa-save</v-icon>SAVE</v-btn>
      <v-btn v-if="amazon.enabled" :loading="loading" color="primary" style="margin-left:10px" @click="testCredentials()">TEST CREDENTIALS</v-btn>
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
    amazon: {},
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
    if (Object.keys(this.info).length > 0) this.amazon = JSON.parse(JSON.stringify(this.info))
  },
  watch: {
    info: function(val) {
      this.amazon = JSON.parse(JSON.stringify(val))
    },
    init: function(val) {
      this.loading = val
    }
  },
  methods: {
    saveAmazon() {
      // Check if all fields are filled
      if (!this.$refs.amazon_form.validate()) {
        this.notification('Please fill the required fields', '#EF5354')
        return
      }
      // Disable the fields while updating fields to the DB
      this.loading = true
      // Parse amazon enable
      this.amazon.enabled = ('enabled' in this.amazon) ? this.amazon.enabled : false
      // Construct path & payload
      const payload = { name: 'AMAZON', value: this.amazon }
      // Update Amazon values to the DB
      axios.post('/admin/settings', payload)
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
      const payload = this.amazon
      axios.post('/admin/settings/amazon/test', payload)
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