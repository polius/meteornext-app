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
                  <v-alert v-if="showInstall" dense color="#fb8c00">
                    <v-row align="center">
                      <v-col align="left"><v-icon small style="margin-bottom:2px; margin-right:12px">fas fa-exclamation-triangle</v-icon>A setup is required before login</v-col>
                      <v-col class="shrink">
                        <v-btn @click="install">INSTALL</v-btn>
                      </v-col>
                    </v-row>
                  </v-alert>
                  <v-form ref="form" @submit.prevent style="margin-top:20px">
                    <div v-if="mfa == null">
                      <v-text-field :disabled="showInstall" ref="username" filled v-model="username" name="username" label="Username" :rules="[v => !!v || '']" required v-on:keyup.enter="login()" style="margin-bottom:20px;" hide-details>
                        <template v-slot:append><v-icon small style="margin-top:4px; margin-right:4px">fas fa-user</v-icon></template>
                      </v-text-field>
                      <v-text-field :disabled="showInstall" ref="password" filled v-model="password" name="password" label="Password" :rules="[v => !!v || '']" required type="password" v-on:keyup.enter="login()" style="margin-bottom:20px;" hide-details>
                        <template v-slot:append><v-icon small style="margin-top:4px; margin-right:4px">fas fa-lock</v-icon></template>
                      </v-text-field>
                    </div>
                    <div v-else-if="mfa == '2fa'">
                      <v-text-field ref="2fa" filled v-model="twoFactor['value']" label="2FA Code" maxlength="6" :rules="[v => !!v || '']" v-on:keyup.enter="login()" style="margin-bottom:20px;" hide-details>
                        <template v-slot:append><v-icon small style="margin-top:3px; margin-right:4px">fas fa-key</v-icon></template>
                      </v-text-field>
                    </div>
                    <div v-else-if="mfa == 'webauthn'">
                      <v-card>
                        <v-progress-linear v-show="loading" indeterminate></v-progress-linear>
                        <v-card-text>
                          <div class="text-h5 font-weight-light white--text" style="text-align:center; font-size:1.4rem !important">Verify your identity</div>
                          <v-icon :style="`display:table; margin-left:auto; margin-right:auto; margin-top:20px; margin-bottom:20px; color:${ webauthn.status == 'init' ? '#046cdc' : webauthn.status == 'ok' ? '#00b16a' : webauthn.status == 'ko' ? '#ff5252' : '#fa8131'}`" size="55">fas fa-fingerprint</v-icon>
                          <div class="text-subtitle-1 white--text" style="text-align:center; font-size:1.1rem !important;">{{ ['init','validating'].includes(webauthn.status) ? 'Touch sensor' : webauthn.status == 'ok' ? 'Fingerprint recognized' : 'Fingerprint not recognized' }}</div>
                        </v-card-text>
                      </v-card>
                    </div>
                  </v-form>
                  <v-btn v-if="!(mfa == 'webauthn')" :disabled="showInstall" x-large type="submit" color="info" :loading="loading" block style="margin-top:0px;" @click="login()">LOGIN</v-btn>
                  <v-checkbox :disabled="showInstall" v-if="mfa == null" v-model="remember" label="Remember username" hide-details style="margin-bottom:2px"></v-checkbox>
                </v-card-text>
              </v-card>
            </v-slide-y-transition>
          </v-flex>
        </v-layout>
      </v-container>
    </v-main>
    <v-dialog v-model="passwordDialog" max-width="512px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1">CHANGE PASSWORD</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn @click="passwordDialog = false" icon><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:20px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="passwordForm" @submit.prevent>
                  <v-text-field ref="passwordCurrent" v-model="passwordItem.current" :readonly="loadingDialog" label="Current password" type="password" :rules="[v => !!v || '']" required style="padding-top:5px" autocomplete="new-password"></v-text-field>
                  <v-text-field v-model="passwordItem.new" :readonly="loadingDialog" label="New password" type="password" :rules="[v => !!v || '']" required style="padding-top:0px" autocomplete="new-password"></v-text-field>
                  <v-text-field v-model="passwordItem.repeat" :readonly="loadingDialog" label="Repeat new password" type="password" :rules="[v => !!v || '']" required style="padding-top:0px" autocomplete="new-password" v-on:keyup.enter="submitPassword"></v-text-field>
                </v-form>
                <v-divider></v-divider>
                <v-row no-gutters style="margin-top:20px;">
                  <v-btn :loading="loadingDialog" color="#00b16a" @click="submitPassword">CONFIRM</v-btn>
                  <v-btn :disabled="loadingDialog" color="#EF5354" @click="passwordDialog = false" style="margin-left:5px">CANCEL</v-btn>
                </v-row>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <MFA :enabled="mfaDialog" @update="mfaDialog = $event" mode="login" :user="{'username': username, 'password': password}"/>
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
import { webauthnLogin } from './mfa/webauthn.js'
import MFA from './mfa/MFA'

export default {
  data: () => ({
    // Login Form
    mode: 0,
    username: '',
    password: '',
    mfa: null,
    remember: false,
    loading: false,
    showInstall: false,

    // Password Dialog
    passwordDialog: false,
    passwordItem: { current: '', new: '', repeat: ''},

    // MFA Dialog
    mfaDialog: false,
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
  props: ['url'],
  components: { MFA },
  beforeRouteEnter(to, from, next) {
    next((vm) => {
      vm.prevRoute = from['path']
      vm.from = from
    })
  },
  created() {
    this.checkInstall()
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
  watch: {
    passwordDialog: function(val) {
      if (val) {
        this.passwordItem = { current: '', new: '', repeat: ''}
        requestAnimationFrame(() => {
          if (typeof this.$refs.passwordForm !== 'undefined') this.$refs.passwordForm.resetValidation()
          if (typeof this.$refs.passwordCurrent !== 'undefined') this.$refs.passwordCurrent.focus()
        })
      }
    },
    mfa: function (val) {
      if (val == '2fa') {
        this.$nextTick(() => { 
          this.$refs['2fa'].focus()
          this.$refs.form.resetValidation()
        })
      }
    }
  },
  methods: {
    async login() {
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'warning')
        return
      }
      this.loading = true
      this.webauthn = { status: 'init' }
      var payload = {
        username: this.username,
        password: this.password,
        remember: this.remember,
      }
      if (this.twoFactor['value'].length > 0) payload['mfa'] = this.twoFactor['value']
      if (this.twoFactor['hash'] != null) payload['2fa_hash'] = this.twoFactor['hash']
      try {
        let response = await this.$store.dispatch('app/login', payload)
        this.loading = false
        if (response.status == 200) this.login_success()
        else if (response.status == 202) {
          if (response.data.code == 'password_setup') this.passwordDialog = true
          else if (response.data.code == 'mfa_setup') this.mfaDialog = true
          else {
            this.mfa = response.data.code
            if (this.mfa == 'webauthn') {
              try {
                let mfa = await webauthnLogin(response.data.data)
                this.loading = true
                this.webauthn = { status: 'validating' }
                await this.$store.dispatch('app/login', { ...payload, mfa, host: window.location.host })
                this.login_success()
              }
              catch (error) {
                this.loading = true
                this.webauthn = { status: 'ko' }
                this.notification('response' in error ? error.response.data.message : error.message, '#EF5354')
                setTimeout(() => { this.loading = false; this.mfa = null }, 1000)
              }
            }
          }
        }
      }
      catch (error) {
        this.loading = false
        if (error.response === undefined) this.notification("No internet connection", '#EF5354')
        else if (error.response.status == 401) this.notification(error.response.data.message, '#EF5354')
        else if (this.mfa == null) this.notification("Can't establish a connection to the server", '#EF5354')
      }
    },
    checkInstall() {
      axios.get('/setup')
        .then((response) => {
          this.showInstall = response.data.available
        })
        .catch(() => {
          this.notification("Can't establish a connection to the server", '#EF5354')
        })
    },
    install() {
      this.$router.push('/install')
    },
    login_success() {
      if (this.$route.query.url !== undefined) this.$router.push({ path: this.$route.query.url })
      else if (['', '/install'].includes(this.prevRoute)) this.$router.push('/')
      else this.$router.push(this.prevRoute)
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  }
}
</script>