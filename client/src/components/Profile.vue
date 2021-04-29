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
        <MFA :enabled="mfaDialog" @update="mfaDialog = $event" mode="profile"/>
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
import axios from 'axios'
import MFA from './mfa/MFA'

export default {
  data: () => ({
    profile: { username: '', group: '', email: '' },

    // Loading
    loading: true,
    loadingDialog: false,

    // Password Dialog
    mfaDialog: false,
    passwordDialog: false,
    passwordItem: { current: '', new: '', repeat: ''},

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarColor: '',
    snackbarText: ''
  }),
  components: { MFA },
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
    }
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
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    },
  }
}
</script>