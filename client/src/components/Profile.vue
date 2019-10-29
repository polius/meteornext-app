<template>
  <v-slide-y-transition mode="out-in">
    <v-container fluid>
      <v-content>
        <v-card>
          <v-toolbar flat color="primary">
            <v-toolbar-title>PROFILE</v-toolbar-title>
          </v-toolbar>
          <v-card-text style="padding: 20px 20px 20px;">
            <v-container fluid grid-list-lg style="padding:0px">
              <v-layout row wrap>
                <v-flex xs12>
                  <div class="headline font-weight-regular">Hello <b>{{ this.username }}</b> <v-chip color="teal" text-color="white" style="margin-left:10px; letter-spacing: 1px;">{{ this.group.toUpperCase() }}</v-chip></div>
                  <v-text-field v-model="email" :disabled="loading" label="Email" type="email" append-icon="email" style="margin-top:10px;"></v-text-field>
                  <v-text-field v-model="newPassword" :disabled="loading" label="Password" type="password" :placeholder="password" append-icon="lock" style="padding-top:0px;"></v-text-field>
                  <v-btn color="primary" :loading="loading" @click="saveProfile()" style="margin-left:0px;">Save</v-btn>    
                </v-flex>
              </v-layout>
            </v-container>
          </v-card-text>
        </v-card>

        <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
          {{ snackbarText }}
          <v-btn color="white" text @click="snackbar = false">Close</v-btn>
        </v-snackbar>
      </v-content>
    </v-container>
  </v-slide-y-transition>
</template>

<script>
import axios from 'axios';

export default {
  data: () => ({
    username: '',
    group: '...',
    email: '',
    password: '',
    newPassword: '',
    loading: true,

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarColor: '',
    snackbarText: ''
  }),
  created() {
    this.getProfile()
  },
  methods: {
    getProfile() {
      const path = this.$store.getters.url + '/profile'
      axios.get(path)
        .then((response) => {
          this.username = response.data.data[0]['username']
          this.group = response.data.data[0]['group']
          this.email = response.data.data[0]['email']
          var hiddenPassword = ''
          for (var i = 0; i < response.data.data[0]['password'].length; ++i) hiddenPassword += '·'
          this.password = hiddenPassword
          this.loading = false
        })
        .catch((error) => {
          if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
          // eslint-disable-next-line
          console.error(error)
        })
    },
    saveProfile() {
      // Disable the fields while updating fields to the DB
      this.loading = true
      // Edit item in the DB
      const path = this.$store.getters.url + '/profile'
      const payload = { 
        email: this.email,
        password: this.newPassword
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