<template>
  <div style="height:100%" v-if="available">
    <v-content style="height:100%; padding-top:10px;" :style="{ backgroundImage: 'url(' + require('@/assets/bg.jpg') + ')', backgroundRepeat: 'no-repeat', backgroundSize: 'cover' }">
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
                  <v-form ref="form1" v-show="setup_part == 1">
                    <div class="title font-weight-medium" style="margin-top:15px; margin-bottom:10px;">MySQL Server</div>
                    <v-text-field filled v-model="sql.hostname" name="hostname" label="Hostname" required append-icon="cloud" style="margin-bottom:20px;" :rules="[v => !!v || '']" hide-details v-on:keyup.enter="setup1()"></v-text-field>
                    <v-text-field filled v-model="sql.username" name="username" label="Username" required append-icon="person" style="margin-bottom:20px;" :rules="[v => !!v || '']" hide-details v-on:keyup.enter="setup1()"></v-text-field>
                    <v-text-field filled v-model="sql.password" name="password" label="Password" required append-icon="lock" type="password" style="margin-bottom:20px;" :rules="[v => !!v || '']" hide-details v-on:keyup.enter="setup1()"></v-text-field>
                    <v-text-field filled v-model="sql.port" name="port" label="Port" required append-icon="directions_boat" style="margin-bottom:20px;" :rules="[v => !!v || '']" hide-details v-on:keyup.enter="setup1()"></v-text-field>
                    <v-text-field filled v-model="sql.database" name="database" label="Database" required append-icon="storage" style="margin-bottom:20px;" :rules="[v => !!v || '']" hide-details v-on:keyup.enter="setup1()"></v-text-field>
                  </v-form>
                  <v-form ref="form2" v-show="setup_part == 2">
                    <div class="title font-weight-medium" style="margin-top:10px; margin-bottom:10px;">Create Admin Account</div>
                    <v-text-field filled v-model="account.username" name="username" label="Username" required append-icon="person" style="margin-bottom:20px;" :rules="[v => !!v || '']" hide-details v-on:keyup.enter="setup2()"></v-text-field>
                    <v-text-field filled v-model="account.password" name="password" label="Password" required append-icon="lock" type="password" style="margin-bottom:20px;" :rules="[v => !!v || '']" hide-details v-on:keyup.enter="setup2()"></v-text-field>
                  </v-form>
                  <v-btn v-if="setup_part != 3" x-large type="submit" color="info" :loading="loading" block style="margin-top:0px;" @click="setupSubmit()">{{ formButton }}</v-btn>
                  <v-btn v-else x-large type="submit" color="info" :loading="loading" block style="margin-top:0px;" @click="login()"><b>LOGIN</b></v-btn>
                </v-card-text>
              </v-card>
            </v-slide-y-transition>
          </v-flex>
        </v-layout>
      </v-container>
    </v-content>

    <v-dialog v-model="dialog" persistent max-width="768px">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">Database Already Exists</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="dialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 20px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <div style="padding-top:10px; padding-bottom:5px;" class="subtitle-1">A database named <b>{{ sql['database'] }}</b> has been detected in <b>{{ sql['hostname'] }}</b></div>
                <div style="padding-bottom:10px" class="subtitle-1">Are you sure you want to recreate this database?</div>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :loading="loading" color="success" @click="submitDialog(true)">YES, recreate it</v-btn>
                  <v-btn :disabled="loading" color="error" @click="dialog=false" style="margin-left:10px">Do NOT recreate it</v-btn>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn hover text color="white" @click="snackbar = false">Close</v-btn>
    </v-snackbar>
  </div>
</template>

<script>
  import axios from 'axios'

  export default {
    data: () => ({
      // Setup Form
      sql: { hostname: '', username: '', password: '', port: '3306', database: 'meteor' },
      account: { username: '', password: '' },
      setup_part: 1,
      formButton: 'CHECK CONNECTION',
      loading: false,

      // Setup Dialog
      dialog: false,

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
          .catch((error) => {
            if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          })
      },
      setupSubmit() {
        if (this.account['username'] == '' && this.account['password'] == '') this.setup1()
        else this.setup2()
      },
      setup1() {
        if (!this.$refs.form1.validate()) {
          this.notification('Please fill all fields', 'error')
          return
        }
        this.loading = true
        const payload = JSON.stringify(this.sql)
        axios.post('/setup/1', payload)
          .then((response) => {
            this.notification('Connection successful', 'success')
              if (response.data.exists) this.dialog = true
              else this.submitDialog(false)
          })
          .catch((error) => {
            console.log(error)
            console.log(error.response)
            this.notification("Can't connect to MySQL server", 'error')
          })
          .finally(() => {
            this.loading = false
          })
      },
      setup2() {
        if (!this.$refs.form2.validate()) {
          this.notification('Please fill all fields', 'error')
          return
        }
        this.notification('Setting up Meteor Next...', 'info')
        this.loading = true
        const payload = {
          sql: this.sql,
          account: this.account
        }
        axios.post('/setup/2', JSON.stringify(payload))
          .then((response) => {
            this.notification(response.data.message, 'success')
            this.setup_part += 1
          })
          .catch((error) => {
            this.notification(error.response.data.message, 'error')
          })
          .finally(() => {
            this.loading = false
          })
      },
      login() {
        this.$router.push('/login')
      },
      submitDialog() {
        this.dialog = false
        this.setup_part += 1
        this.$refs.form2.reset()
        this.formButton = 'CONFIRM'
      },
      notification(message, color) {
        this.snackbarText = message
        this.snackbarColor = color 
        this.snackbar = true
      }
    }
  }
</script>