<template>
  <v-slide-y-transition mode="out-in">
    <v-container fluid>
      <v-main>
        <v-card>
          <v-toolbar flat dense color="primary">
            <v-toolbar-title class="white--text subtitle-1"><v-icon small style="padding-right:10px; padding-bottom:3px">fas fa-user</v-icon>PROFILE</v-toolbar-title>
          </v-toolbar>
          <v-card-text style="padding: 20px 20px 20px;">
            <v-container fluid grid-list-lg style="padding:0px">
              <v-layout row wrap>
                <v-flex xs12>
                  <div class="text-h6 font-weight-regular">Hello <span class="font-weight-medium">{{ this.username }}</span> <v-chip color="teal" label text-color="white" style="margin-left:10px; margin-bottom:2px; letter-spacing: 1px;">{{ this.group.toUpperCase() }}</v-chip></div>
                  <v-form ref="form" @submit.prevent style="margin-top:15px">
                    <v-text-field v-model="email" :loading="loading" :disabled="loading" label="Email" type="email" append-icon="email"></v-text-field>
                    <v-text-field v-model="newPassword" :loading="loading" :disabled="loading" label="Password" type="password" :placeholder="password" append-icon="lock" hide-details style="padding-top:0px;"></v-text-field>
                    <v-switch v-model="mfa['enabled']" @change="onMFAChange" :loading="loading" :disabled="loading" flat label="Multi-Factor Authentication (MFA)" style="margin-top:20px"></v-switch>
                    <v-card v-if="mfa['enabled'] && !mfa['origin']" style="width:232px; margin-bottom:20px;">
                      <v-card-text>
                        <v-progress-circular v-if="mfa['uri'] == null" indeterminate style="margin-left:auto; margin-right:auto; display:table;"></v-progress-circular>
                        <qrcode-vue v-else :value="mfa['uri']" size="200" level="H" background="#ffffff" foreground="#000000"></qrcode-vue>
                        <v-text-field outlined v-model="mfa['value']" v-on:keyup.enter="saveProfile()" label="MFA Code" append-icon="vpn_key" :rules="[v => v == parseInt(v) && v >= 0 || '']" required hide-details style="margin-top:10px"></v-text-field>
                      </v-card-text>
                    </v-card>
                  </v-form>
                  <v-btn color="primary" :loading="loading" @click="saveProfile()" style="margin-left:0px;">Save</v-btn>    
                </v-flex>
              </v-layout>
            </v-container>
          </v-card-text>
        </v-card>
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
import axios from 'axios';
import QrcodeVue from 'qrcode.vue'

export default {
  data: () => ({
    username: '',
    group: '...',
    email: '',
    password: '',
    newPassword: '',
    mfa: {
      enabled: false,
      origin: false,
      hash: null,
      uri: null,
      value: ''
    },
    loading: true,

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
  methods: {
    getProfile() {
      axios.get('/profile')
        .then((response) => {
          this.username = response.data.data['username']
          this.group = response.data.data['group']
          this.email = response.data.data['email']
          var hiddenPassword = ''
          for (var i = 0; i < response.data.data['password'].length; ++i) hiddenPassword += '·'
          this.password = hiddenPassword
          this.mfa['enabled'] = this.mfa['origin'] = response.data.data['mfa']
          this.loading = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    onMFAChange(val) {
      if (val && !this.mfa['origin'] && this.mfa['uri'] == null) this.getMFA()
    },
    getMFA() {
      axios.get('/profile/mfa')
        .then((response) => {
          this.mfa['hash'] = response.data['mfa_hash']
          this.mfa['uri'] = response.data['mfa_uri']
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    saveProfile() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please make sure all required fields are filled out correctly', 'error')
        return
      }
      // Disable the fields while updating fields to the DB
      this.loading = true
      // Edit item in the DB
      const payload = { 
        email: this.email,
        password: this.newPassword,
        mfa: this.mfa['enabled'],
        mfaHash: this.mfa['hash'],
        mfaValue: this.mfa['value']
      }
      axios.put('/profile', payload)
        .then((response) => {
          this.mfa['origin'] = this.mfa['enabled']
          this.mfa['hash'] = null
          this.mfa['uri'] = null
          this.mfa['value'] = ''
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
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