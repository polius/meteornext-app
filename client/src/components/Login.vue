<template>
  <div style="height:100%">
    <v-main style="height:100%" :style="{ backgroundImage: 'url(' + require('@/assets/bg.jpg') + ')', backgroundRepeat: 'no-repeat', backgroundSize: 'cover' }">
      <v-container grid-list-xl text-center style="padding-top:0px;">
        <v-layout row wrap align-center style="max-width:500px; margin: 0 auto;">
          <v-flex>
            <v-slide-y-transition mode="out-in">
              <v-card style="border-radius:5px;">
                <v-card-text>
                  <v-avatar :size="150" style="margin-top:10px;"><img :src="require('../assets/logo.png')" /></v-avatar>
                  <div class="display-2" style="margin-top:10px;"><b>Meteor</b> Next</div>
                  <div class="headline" style="margin-top:10px; margin-bottom:20px;">LOGIN</div>
                  <v-divider></v-divider>
                  <v-alert v-if="show_alert" prominent dense type="warning">
                    <v-row align="center">
                      <v-col align="left">A setup is required before login</v-col>
                      <v-col class="shrink">
                        <v-btn @click="setup()">SETUP</v-btn>
                      </v-col>
                    </v-row>
                  </v-alert>
                  <v-form ref="form" @submit.prevent style="margin-top:20px">
                    <div v-if="mode == 0">
                      <v-text-field filled v-model="username" name="username" label="Username" required append-icon="person" v-on:keyup.enter="login()" style="margin-bottom:20px;" hide-details></v-text-field>
                      <v-text-field filled v-model="password" name="password" label="Password" required append-icon="lock" type="password" v-on:keyup.enter="login()" style="margin-bottom:20px;" hide-details></v-text-field>
                    </div>
                    <div v-else-if="mode == 1">
                      <v-text-field ref="mfa" filled v-model="mfa" name="mfa" label="MFA Code" append-icon="vpn_key" v-on:keyup.enter="login()" style="margin-bottom:20px;" hide-details></v-text-field>
                    </div>
                  </v-form>
                  <v-btn x-large type="submit" color="info" :loading="loading" block style="margin-top:0px;" @click="login()">LOGIN</v-btn>
                </v-card-text>
              </v-card>
            </v-slide-y-transition>
          </v-flex>
        </v-layout>
      </v-container>
    </v-main>

    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script>
  import axios from 'axios'

  export default {
    data: () => ({
      // Login Form
      mode: 0,
      username: '',
      password: '',
      mfa: '',
      loading: false,
      show_alert: false,

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
        if (!this.$refs.form.validate()) {
          this.notification('Please enter the username and password', 'warning')
          return
        }
        this.loading = true
        const payload = {
          username: this.username,
          password: this.password,
          mfa: this.mfa
        }
        this.$store.dispatch('app/login', payload)
        .then((response) => {
          if (response.status == 202) {
            this.mode = 1
            this.$nextTick(() => { this.$refs.mfa.focus() })
          }
          else this.login_success()
        })
        .catch((error) => {
          if (error.response.status == 401) this.notification(error.response.data.message, 'error')
          else this.checkSetup()
        })
        .finally(() => {
          this.loading = false
        })
      },
      checkSetup() {
        this.loading = true
        axios.get('/setup')
          .then((response) => {
            if (response.data.setup) this.show_alert = true
            else this.login_success()
          })
          .catch((error) => {
            if (error.response.status == 404) this.notification("Can't establish a connection to the server", 'error')
            else this.notification(error.response.data.message, 'error')
          })
          .finally(() => {
            this.loading = false
          })
      },
      login_success() {
        if (this.$route.query.url !== undefined) this.$router.push({ path: this.$route.query.url })
        else if (['', '/setup'].includes(this.prevRoute)) this.$router.push('/')
        else this.$router.push(this.prevRoute)
      },
      setup() {
        this.$router.push('/setup')
      },
      notification(message, color) {
        this.snackbarText = message
        this.snackbarColor = color 
        this.snackbar = true
      }
    }
  }
</script>