<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title>SLACK</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-btn :color="mode == 'deployments' ? 'primary' : '#779ecb'" @click="mode = 'deployments'" style="margin-right:10px;">Deployments</v-btn>
        <v-btn :color="mode == 'monitoring' ? 'primary' : '#779ecb'" @click="mode = 'monitoring'" style="margin-right:10px;">Monitoring</v-btn>
      </v-toolbar>
      <v-container fluid grid-list-lg>
        <v-layout row wrap>
          <!-- DEPLOYMENTS -->
          <v-flex v-if="mode == 'deployments'" xs12>
            <v-form ref="form" style="padding:0px 10px 10px 10px;">
              <div class="title font-weight-regular" style="margin-top:5px;">DEPLOYMENTS</div>
              <div class="body-1 font-weight-regular" style="margin-top:10px; margin-bottom:15px;">Send a <span class="body-1 font-weight-medium" style="color:rgb(250, 130, 49);">Slack</span> message everytime a deployment finishes.</div>
              <v-text-field :loading="loading" :disabled="loading" v-model="deployments.channel_name" label="Channel Name" :rules="[v => !!v || '']"></v-text-field>
              <v-text-field :loading="loading" :disabled="loading" v-model="deployments.webhook_url" label="Webhook URL" :rules="[v => !!v && (v.startsWith('http://') || v.startsWith('https://')) || '']" style="padding-top:0px;"></v-text-field>
              <v-switch :disabled="loading" v-model="deployments.enabled" label="Enable Notifications" color="info" style="margin-top:0px;"></v-switch>
              <v-divider style="margin-top:-5px;"></v-divider>
              <div style="margin-top:20px;">
                <v-btn :loading="loading" color="#00b16a" style="margin-left:0px;" @click="saveSlack('deployments')">SAVE</v-btn>
                <v-btn :loading="loading" color="info" style="margin-left:10px;" @click="testSlack('deployments')">TEST</v-btn>
              </div>
            </v-form>
          </v-flex>

          <!-- MONITORING -->
          <v-flex v-else-if="mode == 'monitoring'" xs12>
            <v-form ref="form" style="padding:0px 10px 10px 10px;">
              <div class="title font-weight-regular" style="margin-top:5px;">MONITORING</div>
              <div class="body-1 font-weight-regular" style="margin-top:10px; margin-bottom:15px;">Send a <span class="body-1 font-weight-medium" style="color:rgb(250, 130, 49);">Slack</span> message when a monitored server becomes available or unavailable.</div>
              <v-text-field :loading="loading" :disabled="loading" v-model="monitoring.channel_name" label="Channel Name" :rules="[v => !!v || '']"></v-text-field>
              <v-text-field :loading="loading" :disabled="loading" v-model="monitoring.webhook_url" label="Webhook URL" :rules="[v => !!v && (v.startsWith('http://') || v.startsWith('https://')) || '']" style="padding-top:0px;"></v-text-field>
              <v-switch :disabled="loading" v-model="monitoring.enabled" label="Enable Notifications" color="info" style="margin-top:0px;"></v-switch>
              <v-divider style="margin-top:-5px;"></v-divider>
              <div style="margin-top:20px;">
                <v-btn :loading="loading" color="#00b16a" style="margin-left:0px;" @click="saveSlack('monitoring')">SAVE</v-btn>
                <v-btn :loading="loading" color="info" style="margin-left:10px;" @click="testSlack('monitoring')">TEST</v-btn>
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
    loading: true,

    // Slack Data
    deployments: { channel_name: '', webhook_url: '', enabled: false },
    monitoring: { channel_name: '', webhook_url: '', enabled: false },
    mode: 'deployments',

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
      axios.get('/inventory/slack')
        .then((response) => {
          this.parseSlack(response.data.data)
          this.loading = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    parseSlack(data) {
      for (let i = 0; i < data.length; ++i) {
        if (data[i]['mode'] == 'DEPLOYMENTS') this.deployments = data[i]
        else if (data[i]['mode'] == 'MONITORING') this.monitoring = data[i]
      }
    },
    saveSlack(mode) {
      // Disable the fields while updating fields to the DB
      this.loading = true

      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }

      // Build Payload
      var payload = (mode == 'deployments') ? this.deployments : this.monitoring
      payload['mode'] = mode

      // Post new data into DB
      axios.post('/inventory/slack', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.loading = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    testSlack(mode) {
      // Disable the fields while updating fields to the DB
      this.loading = true

      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      // Test Slack Webhook URL
      const url = (mode == 'deployments') ? this.deployments.webhook_url : this.monitoring.webhook_url
      axios.get('/inventory/slack/test', { params: { webhook_url: url } })
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