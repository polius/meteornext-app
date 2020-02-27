<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title>SLACK</v-toolbar-title>
      </v-toolbar>
      <v-container fluid grid-list-lg>
        <v-layout row wrap>
          <v-flex xs12>
            <v-form ref="form" style="padding:0px 10px 10px 10px;">
              <v-text-field :loading="loading" :disabled="loading" v-model="channel_name" label="Channel Name" :rules="[v => enabled ? v.length > 0 : true || '']"></v-text-field>
              <v-text-field :loading="loading" :disabled="loading" v-model="webhook_url" label="Webhook URL" :rules="[v => enabled ? v.length > 0 && (v.startsWith('http://') || v.startsWith('https://')) : true || '']" style="padding-top:0px;"></v-text-field>
              <v-switch :disabled="loading" v-model="enabled" label="Enable Notifications" color="info" style="margin-top:0px;"></v-switch>
              <v-divider style="margin-top:-5px;"></v-divider>
              <div style="margin-top:20px;">
                <v-btn :loading="loading" color="#00b16a" style="margin-left:0px;" @click="saveSlack()">SAVE</v-btn>
                <v-btn :loading="loading" color="info" style="margin-left:10px;" @click="testSlack()">TEST</v-btn>
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
    channel_name: '',
    webhook_url: '',
    enabled: false,
    loading: true,

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarColor: '',
    snackbarText: ''
  }),
  created() {
    this.getSlack()
  },
  methods: {
    getSlack() {
      axios.get('/deployments/slack')
        .then((response) => {
          if (response.data.data.length > 0) {
            this.channel_name = response.data.data[0]['channel_name']
            this.webhook_url = response.data.data[0]['webhook_url']
            this.enabled = response.data.data[0]['enabled']
          }
          this.loading = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    saveSlack() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      // Disable the fields while updating fields to the DB
      this.loading = true
      // Edit item in the DB
      const payload = {
        channel_name: this.channel_name,
        webhook_url: this.webhook_url,
        enabled: this.enabled
      }
      axios.put('/deployments/slack', payload)
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
    testSlack() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      // Test Slack Webhook URL
      axios.get('/deployments/slack/test', { params: { webhook_url: this.webhook_url } })
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
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  }
}
</script>