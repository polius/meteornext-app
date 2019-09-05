<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title>AMAZON S3</v-toolbar-title>
      </v-toolbar>
      <v-container fluid grid-list-lg>
        <v-layout row wrap>
          <v-flex xs12>
            <v-form style="padding:0px 10px 10px 10px;">
              <v-text-field :loading="loading" :disabled="loading" v-model="aws_access_key" label="AWS Access Key"></v-text-field>
              <v-text-field :loading="loading" :disabled="loading" v-model="aws_secret_access_key" label="AWS Secret Access Key" style="padding-top:0px;"></v-text-field>
              <v-text-field :loading="loading" :disabled="loading" v-model="region_name" label="Region Name" hint="Example: eu-west-1" style="padding-top:0px;"></v-text-field>
              <v-text-field :loading="loading" :disabled="loading" v-model="bucket_name" label="Bucket Name" style="padding-top:0px;"></v-text-field>
              <v-switch :disabled="loading" v-model="enabled" label="Enable Uploading Logs" style="margin-top:0px;"></v-switch>
              <v-divider style="margin-top:-5px;"></v-divider>
              <div style="margin-top:20px;">
                <v-btn :loading="loading" color="primary" @click="saveS3()" style="margin-left:0px;">SAVE</v-btn>
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
    enabled: false,
    loading: true,

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarColor: '',
    snackbarText: ''
  }),
  created() {
    this.getS3()
  },
  methods: {
    getS3() {
      const path = this.$store.getters.url + '/deployments/s3'
      axios.get(path)
        .then((response) => {
          if (response.data.data.length > 0) {
            this.aws_access_key = response.data.data[0]['aws_access_key']
            this.aws_secret_access_key = response.data.data[0]['aws_secret_access_key']
            this.region_name = response.data.data[0]['region_name']
            this.bucket_name = response.data.data[0]['bucket_name']
            this.enabled = response.data.data[0]['enabled']
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
    saveS3() {
      // Disable the fields while updating fields to the DB
      this.loading = true
      // Edit item in the DB
      const path = this.$store.getters.url + '/deployments/s3'
      const payload = { 
        aws_access_key: this.aws_access_key,
        aws_secret_access_key: this.aws_secret_access_key,
        region_name: this.region_name,
        bucket_name: this.bucket_name,
        enabled: this.enabled
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