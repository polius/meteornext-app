<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title>LOGS</v-toolbar-title>
      </v-toolbar>
      <v-container fluid grid-list-lg>
        <v-layout row wrap>
          <v-flex xs12>
            <div class="title font-weight-regular" style="margin-left:10px; margin-top:5px;">Amazon S3</div>
            <v-form ref="form" style="padding:0px 10px 10px 10px;">
              <v-text-field :loading="loading" :disabled="loading" v-model="aws_access_key" label="AWS Access Key" required :rules="[v => !!v || '']"></v-text-field>
              <v-text-field :loading="loading" :disabled="loading" v-model="aws_secret_access_key" label="AWS Secret Access Key" style="padding-top:0px;" required :rules="[v => !!v || '']"></v-text-field>
              <v-text-field :loading="loading" :disabled="loading" v-model="region_name" label="Region Name" hint="Example: eu-west-1" style="padding-top:0px;" required :rules="[v => !!v || '']"></v-text-field>
              <v-text-field :loading="loading" :disabled="loading" v-model="bucket_name" label="Bucket Name" style="padding-top:0px;" required :rules="[v => !!v || '']"></v-text-field>
              <v-text-field :loading="loading" :disabled="loading" v-model="url" label="Logs Url" style="padding-top:0px;" required :rules="[v => !!v || '']"></v-text-field>
              <v-divider style="margin-top:-5px;"></v-divider>
              <div style="margin-top:20px;">
                <v-btn :loading="loading" color="primary" @click="saveLogs()" style="margin-left:0px;">SAVE</v-btn>
              </div>
            </v-form>
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
    aws_access_key: '',
    aws_secret_access_key: '',
    region_name: '',
    bucket_name: '',
    url: '',
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
          if (response.data.data.length > 0) {
            this.aws_access_key = response.data.data[0]['aws_access_key']
            this.aws_secret_access_key = response.data.data[0]['aws_secret_access_key']
            this.region_name = response.data.data[0]['region_name']
            this.bucket_name = response.data.data[0]['bucket_name']
            this.url = response.data.data[0]['url']
          }
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
      // Edit item in the DB
      const path = this.$store.getters.url + '/deployments/logs'
      const payload = { 
        aws_access_key: this.aws_access_key,
        aws_secret_access_key: this.aws_secret_access_key,
        region_name: this.region_name,
        bucket_name: this.bucket_name,
        url: this.url
      }
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