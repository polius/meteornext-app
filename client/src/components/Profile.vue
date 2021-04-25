<template>
  <v-slide-y-transition mode="out-in">
    <v-container fluid>
      <v-main>
        <v-card>
          <v-toolbar flat dense color="primary">
            <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:3px">fas fa-user</v-icon>PROFILE</v-toolbar-title>
          </v-toolbar>
          <v-card-text style="padding: 20px 20px 20px;">
            <v-container fluid grid-list-lg style="padding:0px">
              <v-layout row wrap>
                <v-flex xs12>
                  <v-text-field readonly v-model="profile.username" :loading="loading" :disabled="loading" label="Username" style="padding-top:5px"></v-text-field>
                  <v-text-field readonly v-model="profile.group" :loading="loading" :disabled="loading" label="Group" style="padding-top:0px"></v-text-field>
                  <v-text-field readonly v-model="profile.email" :loading="loading" :disabled="loading" label="Email" type="email" style="padding-top:0px"></v-text-field>
                  <v-btn :disabled="loading" @click="passwordDialog = true">Change Password</v-btn>
                  <v-btn :disabled="loading" @click="mfaDialog = true" style="margin-left:5px">Manage MFA</v-btn>
                </v-flex>
              </v-layout>
            </v-container>
          </v-card-text>
        </v-card>
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
                      <v-btn :disabled="loadingDialog" color="error" @click="passwordDialog = false" style="margin-left:5px">CANCEL</v-btn>
                    </v-row>
                  </v-flex>
                </v-layout>
              </v-container>
            </v-card-text>
          </v-card>
        </v-dialog>
        <v-dialog v-model="mfaDialog" max-width="512px">
          <v-card>
            <v-toolbar dense flat color="primary">
              <v-toolbar-title class="white--text subtitle-1">MANAGE MFA</v-toolbar-title>
              <v-spacer></v-spacer>
              <v-btn @click="mfaDialog = false" icon><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
            </v-toolbar>
            <v-card-text style="padding:20px">
              <v-container style="padding:0px">
                <v-layout wrap>
                  <v-flex xs12>
                    <v-form ref="mfaForm" @submit.prevent style="margin-bottom:15px">
                      <div v-if="profile.mfa == 0">
                        <div class="text-body-1">Choose the type of MFA device to assign:</div>
                        <v-radio-group v-model="mfaMode">
                          <v-radio value="2fa">
                            <template v-slot:label>
                              <div>
                                <div>Virtual MFA device</div>
                                <div class="font-weight-regular caption" style="font-size:0.85rem !important">Authenticator app installed on your mobile device or computer</div>
                              </div>
                            </template>
                          </v-radio>
                          <v-radio disabled value="webauthn" style="margin-top:5px">
                            <template v-slot:label>
                              <div>
                                <div>Security Key</div>
                                <div class="font-weight-regular caption" style="font-size:0.85rem !important">YubiKey or any other compliant device</div>
                              </div>
                            </template>
                          </v-radio>
                        </v-radio-group>
                        <v-card>
                          <v-card-text>
                            <v-progress-circular v-if="mfa['uri'] == null" indeterminate style="margin-left:auto; margin-right:auto; display:table;"></v-progress-circular>
                            <qrcode-vue v-else :value="mfa['uri']" size="200" level="H" background="#ffffff" foreground="#000000" style="text-align:center"></qrcode-vue>
                            <v-btn @click="mfaCodeDialog = true" text block hide-details>CAN'T SCAN THE QR?</v-btn>
                            <v-text-field ref="mfaCode" outlined v-model="mfa['value']" v-on:keyup.enter="submitMFA" label="MFA Code" maxlength="6" :rules="[v => v == parseInt(v) && v >= 0 || '']" required hide-details style="margin-top:10px">
                              <template v-slot:append><v-icon small style="margin-top:3px; margin-right:4px">fas fa-key</v-icon></template>
                            </v-text-field>
                          </v-card-text>
                        </v-card>
                      </div>
                      <div v-else>
                        <v-card>
                          <v-row no-gutters>
                            <v-col cols="auto" style="display:flex; margin:15px">
                              <v-icon color="#00b16a">fas fa-check-circle</v-icon>
                            </v-col>
                            <v-col style="padding-top:5px">
                              <div class="text-body-1" style="color:#00b16a">The MFA is currently enabled.</div>
                              <div class="text-body-2">Active since: {{ dateFormat(profile.mfa_created) }}</div>
                            </v-col>
                          </v-row>
                        </v-card>
                      </div>
                    </v-form>
                    <v-divider></v-divider>
                    <v-row no-gutters style="margin-top:20px;">
                      <v-btn :loading="loadingDialog" color="#00b16a" @click="submitMFA">{{ profile.mfa ? 'DISABLE MFA' : 'CONFIRM' }}</v-btn>
                      <v-btn :disabled="loadingDialog" color="error" @click="mfaDialog = false" style="margin-left:5px">CANCEL</v-btn>
                    </v-row>
                  </v-flex>
                </v-layout>
              </v-container>
            </v-card-text>
          </v-card>
        </v-dialog>
        <v-dialog v-model="mfaCodeDialog" max-width="512px">
          <v-card>
            <v-toolbar dense flat color="primary">
              <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:3px">fas fa-qrcode</v-icon>QR CODE</v-toolbar-title>
            </v-toolbar>
            <v-card-text style="padding:0px">
              <v-container>
                <v-layout wrap>
                  <v-flex xs12>
                    <div class="white--text" style="font-size:18px; letter-spacing:0.08em; text-align:center;">{{ mfa['hash'] }}</div>
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
      </v-main>
    </v-container>
  </v-slide-y-transition>
</template>

<script>
// import base64js from 'base64-js'
import axios from 'axios'
import moment from 'moment'
import QrcodeVue from 'qrcode.vue'

export default {
  data: () => ({
    profile: { username: '', group: '', email: '', mfa: 0, mfa_created: null},

    // Loading
    loading: true,
    loadingDialog: false,

    // Password Dialog
    passwordDialog: false,
    passwordItem: { current: '', new: '', repeat: ''},

    // MFA Dialog
    mfaDialog: false,
    mfaCodeDialog: false,
    mfaMode: '2fa',
    mfa: {
      enabled: false,
      hash: null,
      uri: null,
      value: ''
    },

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarColor: '',
    snackbarText: ''
  }),
  components: { QrcodeVue },
  created() {
    this.getProfile()
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
    mfaDialog: function(val) {
      if (val) {
        if (this.mfa['uri'] == null) this.getMFA()
        this.mfa.value = ''
        requestAnimationFrame(() => {
          if (typeof this.$refs.mfaForm !== 'undefined') this.$refs.mfaForm.resetValidation()
          if (typeof this.$refs.mfaCode !== 'undefined') this.$refs.mfaCode.focus()
        })
      }
    },
    mfaCodeDialog: function(val) {
      if (val) {
        requestAnimationFrame(() => {
          if (typeof this.$refs.mfaForm !== 'undefined') this.$refs.mfaForm.resetValidation()
        })
      }
      if (!val) {
        requestAnimationFrame(() => {
          if (typeof this.$refs.mfaForm !== 'undefined') this.$refs.mfaForm.resetValidation()
          if (typeof this.$refs.mfaCode !== 'undefined') this.$refs.mfaCode.focus()
        })
      }
    },
    mfaMode: function(val) {
      if (val == 'webauthn') {
        if (this.u2fChallenge == null) {
          console.log("register")
          const payload = { host: window.location.host }
          axios.post('/mfa/webauthn/register', payload)
            .then((response) => {
              // Convert certain members of the PublicKeyCredentialCreateOptions into byte arrays as expected by the spec.
              const publicKeyCredentialCreateOptions = this.transformCredentialCreateOptions(response.data)
              // Request the authenticator(s) to create a new credential keypair.
              navigator.credentials.create({ publicKey: publicKeyCredentialCreateOptions })
              .then((resp) => {
                const newAssertionForServer = this.transformNewAssertionForServer(resp)
                console.log(newAssertionForServer)
              })
              .catch ((err) => { return console.error("Error creating credential:", err) })
            })
            .catch((error) => {
              console.log(error)
              if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
              else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
            })
        }
        else {
          console.log("sign2")
        }
      }
    },
  },
  methods: {
    getProfile() {
      axios.get('/profile')
        .then((response) => {
          this.profile = response.data.data
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
    },
    onMFAChange(val) {
      if (val && this.mfa['uri'] == null) this.getMFA()
    },
    getMFA() {
      axios.get('/mfa/2fa')
        .then((response) => {
          this.mfa['hash'] = response.data['mfa_hash']
          this.mfa['uri'] = response.data['mfa_uri']
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
    },
    submitPassword() {
      // Check if all fields are filled
      if (!this.$refs.passwordForm.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        return
      }
      this.loadingDialog = true
      const payload = this.passwordItem
      axios.put('/profile/password', payload)
        .then((response) => {
          this.passwordDialog = false
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loadingDialog = false)
    },
    submitMFA() {
      // Check if all fields are filled
      if (!this.$refs.mfaForm.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        return
      }
      this.loadingDialog = true
      const payload = this.profile.mfa ? {'enabled': 0} : {'enabled': 1, 'hash': this.mfa.hash, 'value': this.mfa.value}
      axios.post('/mfa/2fa', payload)
        .then((response) => {
          this.mfaDialog = false
          this.getProfile()
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loadingDialog = false)
    },
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    },
    // WEBAUTHN
    // Convert certain members of the PublicKeyCredentialCreateOptions into byte arrays as expected by the spec
    transformCredentialCreateOptions(credentialCreateOptionsFromServer) {
      let {challenge, user} = credentialCreateOptionsFromServer
      user.id = Uint8Array.from (
        atob(credentialCreateOptionsFromServer.user.id.replace(/_/g, "/").replace(/-/g, "+")), 
        c => c.charCodeAt(0)
      )
      challenge = Uint8Array.from (
        atob(credentialCreateOptionsFromServer.challenge.replace(/_/g, "/").replace(/-/g, "+")),
        c => c.charCodeAt(0)
      )
      const transformedCredentialCreateOptions = Object.assign(
        {}, credentialCreateOptionsFromServer, {challenge, user}
      )
      return transformedCredentialCreateOptions
    },
    // Transforms the binary data in the credential into base64 strings
    transformNewAssertionForServer(newAssertion) {
      const attObj = new Uint8Array(newAssertion.response.attestationObject)
      const clientDataJSON = new Uint8Array(newAssertion.response.clientDataJSON)
      const rawId = new Uint8Array(newAssertion.rawId)
      const registrationClientExtensions = newAssertion.getClientExtensionResults()
      return {
          id: newAssertion.id,
          rawId: this.b64enc(rawId),
          type: newAssertion.type,
          attObj: this.b64enc(attObj),
          clientData: this.b64enc(clientDataJSON),
          registrationClientExtensions: JSON.stringify(registrationClientExtensions)
      }
    },
    b64enc(buf) {
      var base64js = require('base64-js')
      return base64js.fromByteArray(buf).replace(/\+/g, "-").replace(/\//g, "_").replace(/=/g, "")
    }
  }
}
</script>