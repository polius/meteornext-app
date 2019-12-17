<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title>SLACK</v-toolbar-title>
      </v-toolbar>
      <v-container fluid grid-list-lg>
        <v-layout row wrap>
          <v-flex xs12>
            <v-form style="padding:0px 10px 10px 10px;">
              <v-text-field :loading="loading" :disabled="loading" v-model="channel_name" label="Channel Name"></v-text-field>
              <v-text-field :loading="loading" :disabled="loading" v-model="webhook_url" label="Webhook URL" style="padding-top:0px;"></v-text-field>
              <v-switch :disabled="loading" v-model="enabled" label="Enable Notifications" style="margin-top:0px;"></v-switch>
              <v-divider style="margin-top:-5px;"></v-divider>
              <div style="margin-top:20px;">
                <v-btn :loading="loading" color="primary" style="margin-left:0px;" @click="saveSlack()">SAVE</v-btn>
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
          if (error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    saveSlack() {
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
          this.notification(response.data.message, 'success')
        })
        .catch((error) => {
          if (error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
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