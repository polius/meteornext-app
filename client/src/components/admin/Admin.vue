<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title>ADMINISTRATION</v-toolbar-title>
      </v-toolbar>
      <v-container fluid grid-list-lg>
        <v-layout row wrap>
          <v-flex xs12>
            <div class="title font-weight-regular" style="margin-left:10px; margin-top:5px;">LOGS</div>
            <div class="body-1 font-weight-regular" style="margin-left:10px; margin-top:10px; margin-bottom:10px;">Choose the logs location:</div>
            <v-btn :loading="loading" color="secondary" style="margin-left:10px;" @click="logs_mode = (logs_mode == 'local') ? '' : 'local'">LOCAL</v-btn>
            <v-btn :loading="loading" color="secondary" style="margin-left:10px;" @click="logs_mode = (logs_mode == 'amazon_s3') ? '' : 'amazon_s3'">AMAZON S3</v-btn>

            <v-card v-if="logs_mode == 'local'" style="margin-left:10px; margin-right:10px; margin-top:15px; margin-bottom:10px;">
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
                  <v-text-field :loading="loading" :disabled="loading" v-model="logs.absolute_path" label="Absolute Path" required :rules="[v => !!v || '']"></v-text-field>
                </v-form>
              </v-card-text>
            </v-card>

            <v-card v-else-if="logs_mode == 'amazon_s3'" style="margin-left:10px; margin-right:10px; margin-top:15px; margin-bottom:10px;">
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
                  <v-text-field :loading="loading" :disabled="loading" v-model="logs.aws_access_key" label="AWS Access Key" required :rules="[v => !!v || '']"></v-text-field>
                  <v-text-field :loading="loading" :disabled="loading" v-model="logs.aws_secret_access_key" label="AWS Secret Access Key" style="padding-top:0px;" required :rules="[v => !!v || '']"></v-text-field>
                  <v-text-field :loading="loading" :disabled="loading" v-model="logs.region_name" label="Region Name" style="padding-top:0px;" required :rules="[v => !!v || '']" @change="buildUrl()"></v-text-field>
                  <v-text-field :loading="loading" :disabled="loading" v-model="logs.bucket_name" label="Bucket Name" style="padding-top:0px;" required :rules="[v => !!v || '']" @change="buildUrl()"></v-text-field>
                  <v-text-field :loading="loading" :disabled="loading" v-model="logs.url" label="Logs URL" style="padding-top:0px;" required :rules="[v => !!v || '']"></v-text-field>
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
    // Logs
    logs: {},
    logs_mode: '',

    // Loading
    loading: true,

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarColor: '',
    snackbarText: ''
  }),
  created() {
    this.getLogs()
  },
  methods: {
    getLogs() {
      const path = this.$store.getters.url + '/deployments/logs'
      axios.get(path)
        .then((response) => {
          if (response.data.data.length > 0) this.logs = JSON.parse(response.data.data[0]['data'])
          this.loading = false
        })
        .catch((error) => {
          if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
          // eslint-disable-next-line
          console.error(error)
        })
    },
    saveLogs() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please fill the required fields', 'error')
        return
      }
      // Disable the fields while updating fields to the DB
      this.loading = true
      // Construct path & payload
      const path = this.$store.getters.url + '/deployments/logs'
      const payload = { 
        mode: this.logs_mode,
        data: JSON.stringify(this.logs)
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
    buildUrl() {
      this.logs.url = 'https://' + this.logs.bucket_name + '.' + this.logs.region_name + '.amazonaws.com'
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  }
}
</script>