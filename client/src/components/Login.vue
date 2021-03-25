<template>
  <div style="height:100%">
    <v-main :style="{ height:'100%', padding:'0px', backgroundImage: 'url(' + require('@/assets/bg.jpg') + ')', backgroundRepeat: 'no-repeat', backgroundSize: 'cover' }">
      <v-container grid-list-xl text-center style="height:100%; display:flex; justify-content:center; align-items:center;">
        <v-layout row wrap align-center style="max-width:500px;">
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
                      <v-text-field ref="username" filled v-model="username" name="username" label="Username" :rules="[v => !!v || '']" required append-icon="person" v-on:keyup.enter="login()" style="margin-bottom:20px;" hide-details></v-text-field>
                      <v-text-field ref="password" filled v-model="password" name="password" label="Password" :rules="[v => !!v || '']" required append-icon="lock" type="password" v-on:keyup.enter="login()" style="margin-bottom:20px;" hide-details></v-text-field>
                    </div>
                    <div v-if="mode == 2">
                      <div class="body-1 font-weight-regular">Multi-Factor Authentication (<span class="body-1 font-weight-medium" style="color:rgb(250, 130, 49);">MFA</span>) is required</div>
                      <v-card style="width:220px; margin:10px auto 15px; padding:10px 0px 2px 0px; margin-left:auto; margin-right:auto;">
                        <v-card-text style="padding:0px">
                          <qrcode-vue size="200" :value="mfa_uri" level="H" background="#ffffff" foreground="#000000"></qrcode-vue>
                        </v-card-text>
                      </v-card>
                    </div>
                    <div v-if="[1,2].includes(mode)">
                      <v-text-field ref="mfa" filled v-model="mfa" name="mfa" label="MFA Code" append-icon="vpn_key" maxlength="6" :rules="[v => !!v || '']" v-on:keyup.enter="login()" style="margin-bottom:20px;" hide-details></v-text-field>
                    </div>
                  </v-form>
                  <v-btn x-large type="submit" color="info" :loading="loading" block style="margin-top:0px;" @click="login()">LOGIN</v-btn>
                  <v-checkbox v-if="mode == 0" v-model="remember" label="Remember username" hide-details style="margin-bottom:2px"></v-checkbox>
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
  import QrcodeVue from 'qrcode.vue'

  export default {
    data: () => ({
      // Login Form
      mode: 0,
      username: '',
      password: '',
      mfa: '',
      remember: false,
      loading: false,
      show_alert: false,

      // MFA
      mfa_hash: null,
      mfa_uri: null,

      // Previous Route
      prevRoute: '',

      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarColor: '',
      snackbarText: ''
    }),
    props:['url'],
    components: { QrcodeVue },
    beforeRouteEnter(to, from, next) {
      next((vm) => {
        vm.prevRoute = from['path']
        vm.from = from
      })
    },
    mounted() {
      if (this.rememberVuex) {
        this.username = this.usernameVuex
        this.remember = true
        this.$nextTick(() => this.$refs.password.focus())
      }
      else this.$nextTick(() => this.$refs.username.focus())
    },
    computed: {
      rememberVuex: function() { return this.$store.getters['app/remember'] },
      usernameVuex: function() { return this.$store.getters['app/username'] },
    },
    methods: {
      login() {
        if (!this.$refs.form.validate()) {
          this.notification('Please make sure all required fields are filled out correctly', 'warning')
          return
        }
        this.loading = true
        var payload = {
          username: this.username,
          password: this.password,
          remember: this.remember,
        }
        if (this.mfa.length > 0) payload.mfa = this.mfa
        if (this.mfa_hash) payload.mfa_hash = this.mfa_hash
        this.$store.dispatch('app/login', payload)
        .then((response) => {
          if (response.status == 202) {
            if (response.data.code == 'mfa_request') this.mode = 1
            else if (response.data.code == 'mfa_setup') {
              this.mfa_hash = response.data.mfa_hash
              this.mfa_uri = response.data.mfa_uri
              this.mode = 2
            }
            this.$nextTick(() => { this.$refs.mfa.focus(); this.$refs.form.resetValidation(); })
          }
          else this.login_success()
        })
        .catch((error) => {
          if (this.$refs.mfa !== undefined) { this.mfa = ''; this.$refs.mfa.focus() }
          if (error.response === undefined) this.notification("No internet connection", 'error')
          else if (error.response.status == 401) this.notification(error.response.data.message, 'error')
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
            if (error.response.status != 400) this.notification("Can't establish a connection to the server", 'error')
            else this.notification(error.response.data.message, 'error')
          })
          .finally(() => this.loading = false)
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