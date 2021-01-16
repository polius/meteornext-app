<template>
  <div style="height:100%" v-if="available">
    <v-main style="height:100%; padding-top:10px;" :style="{ backgroundImage: 'url(' + require('@/assets/bg.jpg') + ')', backgroundRepeat: 'no-repeat', backgroundSize: 'cover' }">
      <v-container grid-list-xl text-center style="padding-top:0px;">
        <v-layout row wrap align-center style="max-width:500px; margin: 0 auto;">
          <v-flex>
            <v-slide-y-transition mode="out-in">
              <v-card style="border-radius:5px;">
                <v-card-text>
                  <v-avatar :size="150" style="margin-top:10px;"><img :src="require('../assets/logo.png')" /></v-avatar>
                  <div class="display-2" style="margin-top:10px;"><b>Meteor</b> Next</div>
                  <div class="headline" style="margin-top:10px; margin-bottom:20px;">SETUP</div>
                  <v-divider></v-divider>
                  <!-- LICENSE -->
                  <v-form ref="formLicense" v-show="setup_part == 'license'">
                    <div class="title font-weight-medium" style="margin-top:15px; margin-bottom:10px;">License</div>
                    <v-text-field filled v-model="license.email" name="email" label="Email" required append-icon="account_circle" style="margin-bottom:20px;" :rules="[v => !!v || '']" hide-details v-on:keyup.enter="setup()"></v-text-field>
                    <v-text-field filled v-model="license.key" name="key" label="Key" required append-icon="vpn_key" type="password" style="margin-bottom:20px;" :rules="[v => !!v || '']" hide-details v-on:keyup.enter="setup()"></v-text-field>
                  </v-form>
                  <!-- SQL -->
                  <v-form ref="formSQL" v-show="setup_part == 'sql'">
                    <div class="title font-weight-medium" style="margin-top:15px; margin-bottom:10px;">Server</div>
                    <v-text-field filled v-model="sql.hostname" name="hostname" label="Hostname" style="margin-bottom:20px;" :rules="[v => !!v || '']" hide-details v-on:keyup.enter="setup()"></v-text-field>
                    <v-row no-gutters style="margin-bottom:20px;">
                      <v-col style="margin-right:5px">
                        <v-select filled v-model="sql.engine" :items="['MySQL','Aurora MySQL']" @change="sql.port == '' ? sql.port = '3306' : ''" name="engine" label="Engine" required  :rules="[v => !!v || '']" hide-details></v-select>
                      </v-col>
                      <v-col style="margin-left:5px">
                        <v-text-field filled v-model="sql.port" name="port" label="Port" required :rules="[v => !!v || '']" hide-details v-on:keyup.enter="setup()"></v-text-field>
                      </v-col>
                    </v-row>
                    <v-text-field filled v-model="sql.username" name="username" label="Username" required style="margin-bottom:20px;" :rules="[v => !!v || '']" hide-details v-on:keyup.enter="setup()"></v-text-field>
                    <v-text-field filled v-model="sql.password" name="password" label="Password" required type="password" style="margin-bottom:20px;" :rules="[v => !!v || '']" hide-details v-on:keyup.enter="setup()"></v-text-field>
                    <v-text-field filled v-model="sql.database" name="database" label="Database" required style="margin-bottom:20px;" :rules="[v => !!v || '']" hide-details v-on:keyup.enter="setup()"></v-text-field>
                  </v-form>
                  <!-- ACCOUNT -->
                  <v-form ref="formAccount" v-show="setup_part == 'account'">
                    <div class="title font-weight-medium" style="margin-top:10px; margin-bottom:10px;">Admin Account</div>
                    <v-text-field filled v-model="account.username" name="username" label="Username" required append-icon="person" style="margin-bottom:20px;" :rules="[v => !!v || '']" hide-details v-on:keyup.enter="setup()"></v-text-field>
                    <v-text-field filled v-model="account.password" name="password" label="Password" required append-icon="lock" type="password" style="margin-bottom:20px;" :rules="[v => !!v || '']" hide-details v-on:keyup.enter="setup()"></v-text-field>
                  </v-form>
                  <!-- OVERVIEW -->
                  <div v-show="setup_part == 'overview'">
                  <div class="title font-weight-medium" style="margin-top:10px; margin-bottom:10px;">OVERVIEW</div>
                    <div class="subtitle-1 font-weight-medium" style="margin-top:10px; margin-bottom:10px;">License</div>
                    <v-text-field readonly dense filled v-model="license.email" name="email" label="Email" required append-icon="account_circle" style="margin-bottom:20px;" :rules="[v => !!v || '']" hide-details></v-text-field>
                    <v-text-field readonly dense filled v-model="license.key" name="key" label="Key" required append-icon="vpn_key" type="password" style="margin-bottom:20px;" :rules="[v => !!v || '']" hide-details></v-text-field>
                    <div class="subtitle-1 font-weight-medium" style="margin-top:15px; margin-bottom:10px;">Server</div>
                    <v-text-field readonly dense filled v-model="sql.hostname" name="hostname" label="Hostname" required style="margin-bottom:20px;" :rules="[v => !!v || '']" hide-details></v-text-field>
                    <v-text-field readonly dense filled v-model="sql.port" name="port" label="Port" required style="margin-bottom:20px;" :rules="[v => !!v || '']" hide-details></v-text-field>
                    <v-text-field readonly dense filled v-model="sql.username" name="username" label="Username" required style="margin-bottom:20px;" :rules="[v => !!v || '']" hide-details></v-text-field>
                    <v-text-field readonly dense filled v-model="sql.password" name="password" label="Password" required type="password" style="margin-bottom:20px;" :rules="[v => !!v || '']" hide-details></v-text-field>
                    <v-text-field readonly dense filled v-model="sql.database" name="database" label="Database" required style="margin-bottom:20px;" :rules="[v => !!v || '']" hide-details></v-text-field>
                    <div v-if="sql['recreate']" class="subtitle-1 font-weight-medium" style="margin-top:10px; margin-bottom:10px;">Admin Account</div>
                    <v-text-field v-if="sql['recreate']" readonly dense filled v-model="account.username" name="username" label="Username" required append-icon="person" style="margin-bottom:20px;" :rules="[v => !!v || '']" hide-details></v-text-field>
                    <v-text-field v-if="sql['recreate']" readonly dense filled v-model="account.password" name="password" label="Password" required append-icon="lock" type="password" style="margin-bottom:20px;" :rules="[v => !!v || '']" hide-details></v-text-field>
                  </div>
                  <!-- SUBMIT BUTTON -->
                  <v-btn x-large type="submit" color="info" :loading="loading" block style="margin-top:0px;" @click="setup()">{{ buttonText }}</v-btn>
                </v-card-text>
              </v-card>
            </v-slide-y-transition>
          </v-flex>
        </v-layout>
      </v-container>
    </v-main>

    <v-dialog v-model="setupDialog" persistent max-width="768px">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">Database Already Exists</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="setupDialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 20px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <div style="padding-top:10px; padding-bottom:5px;" class="subtitle-1">A database named <b>{{ sql['database'] }}</b> has been detected in <b>{{ sql['hostname'] }}</b></div>
                <div style="padding-bottom:10px" class="subtitle-1">Are you sure you want to recreate this database?</div>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :loading="loading" color="#00b16a" @click="setupDialogSubmit(true)">YES, recreate it</v-btn>
                  <v-btn :disabled="loading" color="error" @click="setupDialogSubmit(false)" style="margin-left:10px">Do NOT recreate it</v-btn>
                </div>
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

  export default {
    data: () => ({
      // Setup Form
      license: { email: '', key: '' },
      sql: { hostname: '', engine: '', port: '', username: '', password: '', database: 'meteor2' },
      account: { username: '', password: '' },
      setup_part: 'license',
      buttonText: 'VERIFY',
      loading: false,

      // Setup Dialog
      setupDialog: false,

      // Setup Available
      available: false,

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
        vm.setupAvailable()
      })
    },
    methods: {
      setupAvailable() {
        axios.get('/setup')
          .then(() => {
            this.available = true
          })
          .catch(() => {
            this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          })
      },
      setup() {
        if (this.setup_part == 'license') this.setupLicense()
        else if (this.setup_part == 'sql') this.setupSQL()
        else if (this.setup_part == 'account') this.setupAccount()
        else if (this.setup_part == 'overview') this.setupOverview()
        else if (this.setup_part == 'login') this.login()
      },
      setupLicense() {
        if (!this.$refs.formLicense.validate()) {
          this.notification('Please fill all fields', 'warning')
          return
        }
        this.loading = true
        const payload = this.license
        axios.post('/setup/license', payload)
          .then((response) => {
            this.notification(response.data.message, '#00b16a')
            this.setup_part = 'sql'
            this.buttonText = 'CHECK CONNECTION'
          })
          .catch((error) => {
            this.notification(error.response.data.message, 'error')
          })
          .finally(() => this.loading = false)
      },
      setupSQL() {
        if (!this.$refs.formSQL.validate()) {
          this.notification('Please fill all fields', 'warning')
          return
        }
        this.loading = true
        const payload = this.sql
        axios.post('/setup/sql', payload)
          .then((response) => {
            this.notification('Connection successful', '#00b16a')
            if (response.data.exists) this.setupDialog = true
            else this.setupDialogSubmit(true)
          })
          .catch((error) => {
            this.notification(error.response.data.message, 'error')
          })
          .finally(() => this.loading = false)
      },
      setupDialogSubmit(status) {
        this.sql['recreate'] = status
        this.setupDialog = false
        this.setup_part = (status) ? 'account' : 'overview'
        this.buttonText = (status) ? 'CONFIRM' : 'SETUP'
      },
      setupAccount() {
        if (!this.$refs.formAccount.validate()) {
          this.notification('Please fill all fields', 'warning')
          return
        }
        this.setup_part = 'overview'
        this.buttonText = 'SETUP'
      },
      setupOverview() {
        this.notification('Setting up Meteor Next...', 'info')
        this.loading = true
        const payload = {
          license: this.license,
          sql: this.sql,
          account: this.account
        }
        axios.post('/setup', payload)
          .then((response) => {
            this.notification(response.data.message, '#00b16a')
            this.setup_part = 'login'
            this.buttonText = 'LOGIN'
          })
          .catch((error) => {
            this.notification(error.response.data.message, 'error')
          })
          .finally(() => this.loading = false)
      },
      login() {
        this.$router.push('/login')
      },
      notification(message, color) {
        this.snackbarText = message
        this.snackbarColor = color 
        this.snackbar = true
      }
    }
  }
</script>