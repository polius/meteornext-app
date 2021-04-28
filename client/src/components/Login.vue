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
                      <v-text-field ref="username" filled v-model="username" name="username" label="Username" :rules="[v => !!v || '']" required v-on:keyup.enter="login()" style="margin-bottom:20px;" hide-details>
                        <template v-slot:append><v-icon small style="margin-top:4px; margin-right:4px">fas fa-user</v-icon></template>
                      </v-text-field>
                      <v-text-field ref="password" filled v-model="password" name="password" label="Password" :rules="[v => !!v || '']" required type="password" v-on:keyup.enter="login()" style="margin-bottom:20px;" hide-details>
                        <template v-slot:append><v-icon small style="margin-top:4px; margin-right:4px">fas fa-lock</v-icon></template>
                      </v-text-field>
                    </div>
                    <div v-else-if="mode == 1">
                      <div v-if="mfa == '2fa'">
                        <v-text-field ref="2fa" filled v-model="twoFactor['value']" label="2FA Code" maxlength="6" :rules="[v => !!v || '']" v-on:keyup.enter="login()" style="margin-bottom:20px;" hide-details>
                          <template v-slot:append><v-icon small style="margin-top:3px; margin-right:4px">fas fa-key</v-icon></template>
                        </v-text-field>
                      </div>
                      <div v-else-if="mfa == 'webauthn'">
                        <v-card>
                          <v-progress-linear v-show="loading" indeterminate></v-progress-linear>
                          <v-card-text>
                            <div class="text-h5 white--text" style="text-align:center">Verify your identity</div>
                            <v-icon :style="`display:table; margin-left:auto; margin-right:auto; margin-top:20px; margin-bottom:20px; color:${ webauthn.status == 'init' ? '#046cdc' : webauthn.status == 'ok' ? '#00b16a' : '#ff5252'}`" size="55">fas fa-fingerprint</v-icon>
                            <div class="text-subtitle-1 white--text" style="text-align:center; font-size:1.1rem !important;">{{ webauthn.status == 'init' ? 'Touch sensor' : webauthn.status == 'ok' ? 'Fingerprint recognized' : 'Fingerprint not recognized' }}</div>
                          </v-card-text>
                        </v-card>
                      </div>
                    </div>
                    <div v-else-if="mode == 2">
                      <div class="body-1 font-weight-regular">Multi-Factor Authentication (<span class="body-1 font-weight-medium" style="color:rgb(250, 130, 49);">MFA</span>) is required</div>
                      <v-card style="width:220px; margin:10px auto 15px; padding:10px 0px 2px 0px; margin-left:auto; margin-right:auto;">
                        <v-card-text style="padding:0px">
                          <qrcode-vue size="200" :value="twoFactor['uri']" level="H" background="#ffffff" foreground="#000000"></qrcode-vue>
                          <v-btn @click="twoFactorCodeDialog = true" text block hide-details>CAN'T SCAN THE QR?</v-btn>
                        </v-card-text>
                      </v-card>
                      <v-text-field ref="2fa" filled v-model="twoFactor['value']" label="2FA Code" maxlength="6" :rules="[v => !!v || '']" v-on:keyup.enter="login()" style="margin-bottom:20px;" hide-details>
                        <template v-slot:append><v-icon small style="margin-top:3px; margin-right:4px">fas fa-key</v-icon></template>
                      </v-text-field>
                    </div>
                  </v-form>
                  <v-btn v-if="!(mode == 1 && mfa == 'webauthn')" x-large type="submit" color="info" :loading="loading" block style="margin-top:0px;" @click="login()">LOGIN</v-btn>
                  <v-checkbox v-if="mode == 0" v-model="remember" label="Remember username" hide-details style="margin-bottom:2px"></v-checkbox>
                </v-card-text>
              </v-card>
            </v-slide-y-transition>
          </v-flex>
        </v-layout>
      </v-container>
    </v-main>

    <v-dialog v-model="twoFactorCodeDialog" max-width="512px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:3px">fas fa-qrcode</v-icon>QR CODE</v-toolbar-title>
        </v-toolbar>
        <v-card-text style="padding:0px">
          <v-container>
            <v-layout wrap>
              <v-flex xs12>
                <div style="font-size:18px; letter-spacing:0.08em; text-align:center;">{{ twoFactor['hash'] }}</div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

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
import { webauthnLogin } from './mfa/webauthn.js'

export default {
  data: () => ({
    // Login Form
    mode: 0,
    username: '',
    password: '',
    mfa: null,
    remember: false,
    loading: false,
    show_alert: false,

    // MFA
    twoFactorCodeDialog: false,
    twoFactor: {
      hash: null,
      uri: null,
      value: ''
    },
    webauthn: { 
      status: 'init'
    },

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
      if (this.twoFactor['value'].length > 0) payload['mfa'] = this.twoFactor['value']
      if (this.twoFactor['hash'] != null) payload['2fa_hash'] = this.twoFactor['hash']

      this.$store.dispatch('app/login', payload)
      .then((response) => {
        if (response.status == 202) {
          if (response.data.code == 'mfa_setup') {
            this.mfa_hash = response.data.mfa_hash
            this.mfa_uri = response.data.mfa_uri
            this.mode = 2
          }
          else {
            this.mode = 1
            this.mfa = response.data.code
            if (this.mfa == '2fa') {
              this.$nextTick(() => { 
                this.$refs['2fa'].focus()
                this.$refs.form.resetValidation()
              })
            }
            else if (this.mfa == 'webauthn') {
              webauthnLogin(response.data.data)
              .then((mfa) => {
                this.loading = true
                this.webauthn = { status: 'ok' }
                this.$store.dispatch('app/login', { ...payload, mfa, host: window.location.host })
                .then(() => {
                  this.login_success()
                })
                .catch((error) => {
                  this.webauthn = { status: 'ko' }
                  this.notification(error.response.data.message, 'error')
                })
              })
              .catch((error) => {
                this.webauthn = { status: 'ko' }
                this.notification(error.response.data.message, 'error')
              })
            }
          }
          
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