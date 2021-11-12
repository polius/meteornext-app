<template>
  <div style="height:100%" v-if="available">
    <v-main :style="{ height:'100%', padding:'0px', backgroundImage: 'url(' + require('@/assets/bg.jpg') + ')', backgroundRepeat: 'no-repeat', backgroundSize: 'cover' }">
      <v-container grid-list-xl text-center style="height:100%; display:flex; justify-content:center; align-items:center">
        <v-layout row wrap align-center style="max-width:500px">
          <v-flex>
            <v-slide-y-transition mode="out-in">
              <v-card style="border-radius:5px">
                <v-card-text>
                  <v-avatar :size="110" style="margin-top:10px"><img :src="require('../assets/logo.png')" /></v-avatar>
                  <div class="display-2" style="color:rgba(255,255,255,.9); margin-top:10px"><span style="font-weight:500">Meteor</span> Next</div>
                  <div class="headline" style="color:rgba(255,255,255,.9); margin-top:10px; margin-bottom:20px">INSTALL</div>
                  <v-divider></v-divider>
                  <!-- LICENSE -->
                  <v-form ref="formLicense" v-show="installPart == 'license'">
                    <div class="text-h5" style="color:rgba(255,255,255,.9); font-size:1.2rem!important; margin-top:15px; margin-bottom:15px">LICENSE</div>
                    <v-text-field autofocus filled v-model="license.email" name="email" label="Email" required style="margin-bottom:20px" :rules="emailRules" hide-details v-on:keyup.enter="install" autocomplete="false"></v-text-field>
                    <v-text-field filled v-model="license.key" name="key" label="Key" required type="password" style="margin-bottom:20px" :rules="[v => !!v || '']" hide-details v-on:keyup.enter="install" autocomplete="new-password"></v-text-field>
                  </v-form>
                  <!-- SQL -->
                  <v-form ref="formSQL" v-show="installPart == 'sql'">
                    <div class="text-h5" style="color:rgba(255,255,255,.9); font-size:1.2rem!important; margin-top:15px; margin-bottom:15px">SERVER</div>
                    <v-row no-gutters style="margin-bottom:20px">
                      <v-col style="margin-right:5px">
                        <v-select filled v-model="sql.engine" :items="['MySQL','Aurora MySQL']" @change="sql.port == '' ? sql.port = '3306' : ''" name="engine" label="Engine" required  :rules="[v => !!v || '']" hide-details></v-select>
                      </v-col>
                      <v-col style="margin-left:5px">
                        <v-text-field filled v-model="sql.port" name="port" label="Port" required :rules="[v => !!v || '']" hide-details v-on:keyup.enter="install"></v-text-field>
                      </v-col>
                    </v-row>
                    <v-text-field autofocus filled v-model="sql.hostname" name="hostname" label="Hostname" style="margin-bottom:20px" :rules="[v => !!v || '']" hide-details v-on:keyup.enter="install"></v-text-field>
                    <v-text-field filled v-model="sql.username" name="username" label="Username" required style="margin-bottom:20px" :rules="[v => !!v || '']" hide-details v-on:keyup.enter="install" autocomplete="email"></v-text-field>
                    <v-text-field filled v-model="sql.password" name="password" label="Password" required :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'" :type="showPassword ? 'text' : 'password'" @click:append="showPassword = !showPassword" style="margin-bottom:20px" :rules="[v => !!v || '']" hide-details v-on:keyup.enter="install" autocomplete="new-password"></v-text-field>
                    <v-text-field filled v-model="sql.database" name="database" label="Database" required style="margin-bottom:20px" :rules="[v => !!v || '']" hide-details v-on:keyup.enter="install"></v-text-field>
                    <!-- <v-switch v-model="sql.ssl" flat label="SSL Connection" style="margin-top:20px"></v-switch> -->
                    <div v-if="sql.ssl" style="margin-bottom:20px">
                      <v-file-input v-model="sql.ssl_client_key" label="Client Key" prepend-icon="" hide-details style="padding-top:0px"></v-file-input>
                      <v-file-input v-model="sql.ssl_client_certificate" label="Client Certificate" prepend-icon="" hide-details style="margin-top:10px"></v-file-input>
                      <v-file-input v-model="sql.ssl_ca_certificate" label="CA Certificate" prepend-icon="" hide-details style="margin-top:10px"></v-file-input>
                      <v-checkbox v-model="sql.ssl_verify_ca" label="Verify server certificate against CA" hide-details></v-checkbox>
                    </div>
                  </v-form>
                  <!-- ACCOUNT -->
                  <v-form ref="formAccount" v-show="installPart == 'account'">
                    <div class="text-h5" style="color:rgba(255,255,255,.9); font-size:1.2rem!important; margin-top:15px; margin-bottom:15px">ADMIN ACCOUNT</div>
                    <v-text-field autofocus filled v-model="account.username" name="username" label="Username" required style="margin-bottom:20px" :rules="[v => !!v || '']" hide-details v-on:keyup.enter="install"></v-text-field>
                    <v-text-field filled v-model="account.password" name="password" label="Password" required type="password" style="margin-bottom:20px" :rules="[v => !!v || '']" hide-details v-on:keyup.enter="install"></v-text-field>
                  </v-form>
                  <!-- SUBMIT BUTTON -->
                  <v-row no-gutters>
                    <v-col :cols="installPart == 'license' ? 12 : 10">
                      <v-btn x-large type="submit" color="info" :loading="loading" block style="margin-top:0px" @click="install">{{ buttonText }}</v-btn>
                    </v-col>
                    <v-col v-if="installPart != 'license'" cols="2" style="padding-left:5px">
                      <v-btn x-large title="Go back" type="submit" color="info" :loading="loading" block style="margin-top:0px" @click="back"><v-icon style="font-size:1.1rem">fas fa-chevron-left</v-icon></v-btn>
                    </v-col>
                  </v-row>
                </v-card-text>
              </v-card>
            </v-slide-y-transition>
          </v-flex>
        </v-layout>
      </v-container>
    </v-main>

    <v-dialog v-model="installDialog" persistent max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-exclamation-triangle</v-icon>DATABASE ALREADY EXISTS</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="installDialog = false"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <div style="padding-bottom:5px" class="subtitle-1">A database named <span style="font-weight:500; color:white">{{ sql['database'] }}</span> already exists in this server.</div>
                <div style="padding-bottom:10px" class="subtitle-1">Which action do you want to perform?</div>
                <v-radio-group v-model="installOption" hide-details style="margin-top:0px; margin-bottom:20px">
                  <v-radio value="install" color="primary">
                    <template v-slot:label>
                      <div style="margin-left:5px">
                        <div class="body-1 white--text">Install Meteor Next</div>
                        <div class="font-weight-regular caption" style="font-size:0.85rem !important">Recreate the database with a fresh Meteor Next installation.</div>
                      </div>
                    </template>
                  </v-radio>
                  <v-radio value="use" color="primary">
                    <template v-slot:label>
                      <div style="margin-left:5px">
                        <div class="body-1 white--text">Update Meteor Next</div>
                        <div class="font-weight-regular caption" style="font-size:0.85rem !important">Use this option if the current database contains an existing Meteor Next installation.</div>
                      </div>
                    </template>
                  </v-radio>
                </v-radio-group>
                <v-divider></v-divider>
                <div style="margin-top:20px">
                  <v-btn :disabled="loading" color="#00b16a" @click="installDialogSubmit(installOption == 'install')">Confirm</v-btn>
                  <v-btn :disabled="loading" color="#EF5354" @click="installDialog = false" style="margin-left:5px;">Cancel</v-btn>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px">
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
      // Install Form
      license: { email: '', key: '' },
      sql: { engine: 'MySQL', port: '3306', hostname: '', username: '', password: '', database: 'meteor2', ssl: false, ssl_ca_certificate: null, ssl_client_key: null, ssl_client_certificate: null, ssl_verify_ca: false },
      account: { username: '', password: '' },
      installPart: 'license',
      buttonText: 'VERIFY',
      loading: false,
      showPassword: false,
      emailRules: [
        v => !!v || 'E-mail is required',
        v => /^(([^<>()[\]\\.,;:\s@']+(\.[^<>()\\[\]\\.,;:\s@']+)*)|('.+'))@((\[[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\])|(([a-zA-Z\-0-9]+\.)+[a-zA-Z]{2,}))$/.test(v) || 'E-mail must be valid',
      ],

      // Install Dialog
      installDialog: false,
      installOption: 'install',

      // Install Available
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
        vm.installAvailable()
      })
    },
    mounted() {
      requestAnimationFrame(() => {
        if (typeof this.$refs.email !== 'undefined') this.$refs.email.focus()
      })
    },
    methods: {
      installAvailable() {
        axios.get('/setup')
          .then((response) => {
            if (!response.data.available) this.$router.push('/login')
            else this.available = true
          })
          .catch(() => {
            this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          })
      },
      back() {
        if (this.installPart == 'sql') this.installPart = 'license'
        else if (this.installPart == 'account') this.installPart = 'sql'
      },
      install() {
        if (this.installPart == 'license') this.installLicense()
        else if (this.installPart == 'sql') this.installSQL()
        else if (this.installPart == 'account') this.installAccount()
      },
      installLicense() {
        if (!this.$refs.formLicense.validate()) {
          this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
          return
        }
        this.loading = true
        const payload = this.license
        axios.post('/setup/license', payload)
          .then((response) => {
            this.notification(response.data.message, '#00b16a')
            this.installPart = 'sql'
            this.buttonText = 'CHECK CONNECTION'
          })
          .catch((error) => {
            this.notification(error.response.data.message, '#EF5354')
          })
          .finally(() => this.loading = false)
      },
      async installSQL() {
        if (!this.$refs.formSQL.validate()) {
          this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
          return
        }
        // Get SSL Imported Files
        let ssl_ca_certificate = await this.readFileAsync(this.sql.ssl_ca_certificate)
        let ssl_client_key = await this.readFileAsync(this.sql.ssl_client_key)
        let ssl_client_certificate = await this.readFileAsync(this.sql.ssl_client_certificate)
        if (this.sql.ssl && ssl_ca_certificate == null && ssl_client_key == null && ssl_client_certificate == null) {
          this.notification('Import at least one SSL certificate/key', '#EF5354')
          return
        }
        // Test SQL Connection
        this.loading = true
        const payload = {...this.sql, ssl_ca_certificate, ssl_client_key, ssl_client_certificate}
        axios.post('/setup/sql', payload)
          .then((response) => {
            this.notification('Connection successful', '#00b16a')
            if (response.data.exists) this.installDialog = true
            else this.installDialogSubmit(true)
          })
          .catch((error) => {
            this.notification(error.response.data.message, '#EF5354')
          })
          .finally(() => this.loading = false)
      },
      readFileAsync(file) {
        if (file == null) return file
        return new Promise((resolve, reject) => {
          let reader = new FileReader()
          reader.onload = () => { resolve(reader.result)}
          reader.onerror = reject
          reader.readAsText(file, 'utf-8')
        })
      },
      installDialogSubmit(status) {
        this.sql['recreate'] = status
        this.installDialog = false
        this.buttonText = 'CONFIRM'
        if (status) this.installPart = 'account'
        else this.installSubmit()
      },
      installAccount() {
        if (!this.$refs.formAccount.validate()) {
          this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
          return
        }
        this.installSubmit()
      },
      async installSubmit() {
        this.loading = true
        // Get SSL Imported Files
        let ssl_ca_certificate = await this.readFileAsync(this.sql.ssl_ca_certificate)
        let ssl_client_key = await this.readFileAsync(this.sql.ssl_client_key)
        let ssl_client_certificate = await this.readFileAsync(this.sql.ssl_client_certificate)
        const payload = {
          license: this.license,
          sql: {...this.sql, ssl_ca_certificate, ssl_client_key, ssl_client_certificate},
          account: this.account
        }
        axios.post('/setup', payload)
          .then((response) => {
            this.notification(response.data.message, '#00b16a')
            setTimeout(() => this.$router.push('/login'), 1000)
          })
          .catch((error) => {
            this.loading = false
            this.notification(error.response.data.message, '#EF5354')
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