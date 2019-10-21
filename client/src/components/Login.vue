<template>
  <div style="height:100%">
    <v-content style="height:100%" :style="{ backgroundImage: 'url(' + require('@/assets/bg.jpg') + ')', backgroundRepeat: 'no-repeat', backgroundSize: 'cover' }">
      <v-container grid-list-xl text-center style="padding-top:0px;">
        <v-layout row wrap align-center style="max-width:500px; margin: 0 auto;">
          <v-flex>
            <v-slide-y-transition mode="out-in">
              <v-card style="border-radius:5px;">
                <v-card-text>
                  <v-avatar :size="150" style="margin-top:10px;"><img :src="require('../assets/logo.png')" /></v-avatar>
                  <div class="display-2" style="margin-top:10px; margin-bottom:30px;"><b>Meteor</b> Next</div>
                  <v-text-field filled v-model="username" name="username" label="Username" required append-icon="person" v-on:keyup.enter="login()"></v-text-field>
                  <v-text-field filled v-model="password" name="password" label="Password" required append-icon="lock" type="password" v-on:keyup.enter="login()"></v-text-field>
                  <v-btn x-large type="submit" color="info" :loading="loading" block style="margin-top:0px;" @click="login()"><b>LOGIN</b></v-btn>
                </v-card-text>
              </v-card>
            </v-slide-y-transition>
          </v-flex>
        </v-layout>
      </v-container>
    </v-content>

    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn hover text color="white" @click="snackbar = false">Close</v-btn>
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

      // Previous Route
      prevRoute: '',

      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarColor: '',
      snackbarText: ''
    }),
    props:['url'],
    beforeRouteEnter(to, from, next) {
      next((vm) => {
        vm.prevRoute = from['path']
        vm.from = from
      })
    },
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
        .then(() => {
          if (!this.$route.query.url === undefined) this.$router.push(this.prevRoute)
          else this.$router.push({ path: this.$route.query.url })
        })
        .catch((error) => {
          this.loading = false
          this.notification(error.response.data.message, 'error')
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