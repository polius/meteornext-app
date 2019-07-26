<template>
  <div>
    <v-content :style="{ backgroundImage: 'url(' + require('@/assets/bg.jpg') + ')', backgroundRepeat: 'no-repeat', backgroundSize: 'cover' }">
      <v-container grid-list-xl text-xs-center style="padding-top:0px;">
        <v-layout row wrap>
          <v-flex xs6 offset-xs3>
            <v-slide-y-transition mode="out-in">
              <v-card class="ma-5 pa-1" style="border-radius:5px;">
                <v-card-text>
                  <v-avatar :size="150" style="margin-top:10px;"><img :src="require('../assets/logo.png')" /></v-avatar>
                  <div class="display-2" style="margin-top:10px; margin-bottom:30px;"><b>Meteor</b> Next</div>
                  <v-text-field box v-model="username" name="username" label="Username" required append-icon="person"></v-text-field>
                  <v-text-field box v-model="password" name="password" label="Password" required append-icon="lock" type="password"></v-text-field>
                  <v-btn type="submit" color="info" :loading="loading" large block style="margin-top:0px;" @click="login()">Login</v-btn>
                </v-card-text>
              </v-card>
            </v-slide-y-transition>
          </v-flex>
        </v-layout>
      </v-container>
    </v-content>

    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn color="white" flat @click="snackbar = false">Close</v-btn>
    </v-snackbar>
  </div>
</template>

<script>
  export default {
    data: () => ({
      // Login Form
      username: '',
      password: '',
      loading: false,

      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarColor: '',
      snackbarText: ''
    }),
    methods: {
      login() {
        if (this.username == '' || this.password == '') this.notification('Please enter the username and password.', 'warning')
        else this.login_submit()
      },
      login_submit() {
        this.loading = true
        let username = this.username 
        let password = this.password
        this.$store.dispatch('login', { username, password })
        .then(() => this.$router.push('/'))
        .catch((err) => {
          this.loading = false
          this.notification(err.response.data.message, 'error')
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