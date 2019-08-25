<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title>WEB</v-toolbar-title>
      </v-toolbar>
      <v-container fluid grid-list-lg>
        <v-layout row wrap>
          <v-flex xs12>
            <v-text-field :loading="loading" :disabled="loading" v-model="url" label="Public Web URL" required></v-text-field>
            <v-btn :loading="loading" color="primary" @click="saveWeb()" style="margin-left:0px;">Save</v-btn>    
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
    url: '',
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
      const path = this.$store.getters.url + '/deployments/web'
      axios.get(path)
        .then((response) => {
          if (response.data.data.length > 0) {
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
    saveWeb() {
      // Disable the fields while updating fields to the DB
      this.loading = true
      // Edit item in the DB
      const path = this.$store.getters.url + '/deployments/web'
      const payload = { 
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