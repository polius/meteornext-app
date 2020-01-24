<template>
  <div>
    <v-container fluid grid-list-lg>
      <v-layout row wrap>
        <v-flex xs12>
          <div class="title font-weight-regular" style="margin-left:10px; margin-top:5px;">PRO</div>
          <v-form ref="form" style="padding:10px;">
            <v-text-field v-model="name" label="Name" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>
            <v-select :loading="loading_rel" v-model="release" :items="release_items" label="Release" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-select>
            <v-select :loading="loading_env" v-model="environment" :items="environment_items" label="Environment" :rules="[v => !!v || '']" required style="padding-top:0px;" hide-details></v-select>

            <!-- CODE -->
            <div class="subtitle-1 font-weight-regular" style="margin-top:20px; margin-bottom:10px;">
              CODE
              <v-tooltip right>
                <template v-slot:activator="{ on }">
                  <v-icon small style="margin-left:5px; margin-bottom:2px;" v-on="on">fas fa-question-circle</v-icon>
                </template>
                <span>Press ESC when cursor is in the editor to toggle full screen editing</span>
              </v-tooltip>
            </div>
            <v-progress-linear v-if="loading_code" height="1px" color="warning" indeterminate></v-progress-linear>
            <codemirror v-model="code" :options="cmOptions"></codemirror>

            <!-- PARAMETERS -->
            <div class="subtitle-1 font-weight-regular" style="margin-top:20px;">
              METHOD
              <v-tooltip right>
                <template v-slot:activator="{ on }">
                  <v-icon small style="margin-left:5px; margin-bottom:2px;" v-on="on">fas fa-question-circle</v-icon>
                </template>
                <span>
                  <b class="success--text">VALIDATE</b> Tests all server connections
                  <br>
                  <b class="orange--text">TEST</b> Executes only SELECT queries
                  <br>
                  <b class="red--text">DEPLOY</b> Executes ALL queries
                </span>
              </v-tooltip>
            </div>

            <v-radio-group v-model="method" style="margin-top:10px;">
              <v-radio value="validate" color="success">
                <template v-slot:label>
                  <div class="success--text">VALIDATE</div>
                </template>
              </v-radio>
              <v-radio value="test" color="orange">
                <template v-slot:label>
                  <div class="orange--text">TEST</div>
                </template>
              </v-radio>
              <v-radio value="deploy" color="red">
                <template v-slot:label>
                  <div class="red--text">DEPLOY</div>
                </template>
              </v-radio>
            </v-radio-group>

            <v-switch :disabled="loading_env || loading_code" v-model="schedule_enabled" @change="schedule_change()" label="Sheduled" color="info" hide-details style="margin-top:-10px;"></v-switch>
            <v-text-field v-if="schedule_enabled" solo v-model="schedule_datetime" @click="schedule_change()" title="Click to edit the schedule datetime" hide-details readonly style="margin-top:10px; margin-bottom:10px;"></v-text-field>

            <v-checkbox v-else v-model="start_execution" label="Start execution" color="primary" hide-details style="margin-top:15px; margin-bottom:20px;"></v-checkbox>
            <v-divider></v-divider>

            <div style="margin-top:20px;">
              <v-btn :loading="loading_env || loading_code" color="success" @click="submitDeploy()">CREATE DEPLOY</v-btn>
              <router-link to="/deployments"><v-btn :disabled="loading_env || loading_code" color="error" style="margin-left:10px;">CANCEL</v-btn></router-link>
            </div>
          </v-form>
        </v-flex>
      </v-layout>
    </v-container>

    <v-dialog v-model="scheduleDialog" persistent width="290px">
      <v-date-picker v-if="schedule_mode=='date'" v-model="schedule_date" color="info" scrollable>
        <v-btn text color="info" @click="schedule_now()">Now</v-btn>
        <v-spacer></v-spacer>
        <v-btn text color="error" @click="schedule_close()">Cancel</v-btn>
        <v-btn text color="success" @click="schedule_submit()">Confirm</v-btn>
      </v-date-picker>
      <v-time-picker v-else-if="schedule_mode=='time'" v-model="schedule_time" color="info" format="24hr" scrollable>
        <v-btn text color="info" @click="schedule_now()">Now</v-btn>
        <v-spacer></v-spacer>
        <v-btn text color="error" @click="schedule_close()">Cancel</v-btn>
        <v-btn text color="success" @click="schedule_submit()">Confirm</v-btn>
      </v-time-picker>
    </v-dialog>

    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn color="white" text @click="snackbar = false">Close</v-btn>
    </v-snackbar>
  </div>
</template>

<style>
.CodeMirror {
  min-height:450px;
  font-size: 14px;
}
</style>

<script>
import axios from 'axios'
import moment from 'moment'

// CODE-MIRROR
import { codemirror } from 'vue-codemirror'
import 'codemirror/lib/codemirror.css'

// language
import 'codemirror/mode/python/python.js'
// theme css
import 'codemirror/theme/monokai.css'

// require active-line.js
import 'codemirror/addon/selection/active-line.js'
// closebrackets
import 'codemirror/addon/edit/closebrackets.js'
// keyMap
import 'codemirror/mode/clike/clike.js'
import 'codemirror/addon/edit/matchbrackets.js'
import 'codemirror/addon/comment/comment.js'
import 'codemirror/addon/dialog/dialog.js'
import 'codemirror/addon/dialog/dialog.css'
import 'codemirror/addon/selection/mark-selection.js'
import 'codemirror/addon/search/searchcursor.js'
import 'codemirror/addon/search/search.js'
import 'codemirror/keymap/sublime.js'
import 'codemirror/addon/selection/active-line.js'
import 'codemirror/addon/display/fullscreen.js'
import 'codemirror/addon/display/fullscreen.css'

export default {
  data() {
    return {
      // Metadata
      name: '',

      // Execution
      environment: '',
      environment_items: [],

      // Code
      code: '',

      // Init Code Parameters
      cmOptions: {
        readOnly: true,
        autoCloseBrackets: true,
        styleActiveLine: true,
        lineNumbers: true,
        tabSize: 4,
        indentUnit: 4,
        line: true,
        foldGutter: true,
        matchBrackets: true,
        showCursorWhenSelecting: true,
        mode: 'python',
        theme: 'monokai',
        keyMap: 'sublime',
        extraKeys: {
          Tab: function(cm) {
            if (cm.somethingSelected()) cm.indentSelection("add")
            else cm.replaceSelection("    " , "end")
          },
          "Esc": function(cm) {
            cm.setOption("fullScreen", !cm.getOption("fullScreen"))
          }
        }
      },

      // Parameters
      release: '',
      release_items: [],
      method: 'validate',
      start_execution: false,

      // Schedule
      scheduleDialog: false,
      schedule_enabled: false,
      schedule_mode: 'date',
      schedule_date: '',
      schedule_time: '',
      schedule_datetime: '',

      // Query Dialog
      queryDialog: false,
      queryDialogTitle: '',
      
      // Loading Fields
      loading_code: true,
      loading_env: true,
      loading_rel: true,

      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(5000),
      snackbarColor: '',
      snackbarText: ''
    }
  },
  components: {
    codemirror
  },
  created() {
    this.getReleases()
    this.getEnvironments()
    this.getCode()
  },
  methods: {
    getReleases() {
      axios.get('/deployments/releases/active')
        .then((response) => {
          for (var i = 0; i < response.data.data.length; ++i) this.release_items.push(response.data.data[i]['name'])
          this.loading_rel = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    getEnvironments() {
      axios.get('/deployments/environments')
        .then((response) => {
          for (var i = 0; i < response.data.data.length; ++i) this.environment_items.push(response.data.data[i]['name'])
          this.loading_env = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    getCode() {
      this.loading_code = true
      axios.get('/deployments/pro/code')
        .then((response) => {
          this.code = response.data.data
          this.cmOptions.readOnly = false
          this.loading_code = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    schedule_close() {
      this.scheduleDialog = false
      if (this.schedule_mode == 'date') this.schedule_date = this.schedule_datetime.substring(0,10)
      else if (this.schedule_mode == 'time') this.schedule_time = this.schedule_datetime.substring(11,16)
      this.schedule_mode = 'date'
    },
    schedule_now() {
      const date = moment()
      if (this.schedule_mode == 'date') this.schedule_date = date.format("YYYY-MM-DD")
      else if (this.schedule_mode == 'time') this.schedule_time = date.format("HH:mm")
    },
    schedule_change() {
      if (this.schedule_enabled) {
        if (this.schedule_datetime == '') {
          const date = moment().add(30, 'minutes')
          this.schedule_date = date.format("YYYY-MM-DD")
          this.schedule_time = date.format("HH:mm")
          this.schedule_datetime = date.format("YYYY-MM-DD HH:mm")
        }
        this.scheduleDialog = true
      }
      else this.scheduleDialog = false
    },
    schedule_submit() {
      this.schedule_datetime = this.schedule_date + ' ' + this.schedule_time

      if (this.schedule_mode == 'date') {
        this.schedule_mode = 'time'
      }
      else if (this.schedule_mode == 'time') {
        this.scheduleDialog = false
        this.schedule_mode = 'date'
      }
    },
    submitDeploy() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please fill the required fields', 'error')
        return
      }
      this.loading_code = true
      // Build parameters
      const payload = {
        name: this.name,
        release: this.release,
        environment: this.environment,
        code: this.code,
        method: this.method.toUpperCase(),
        scheduled: '',
        start_execution: false
      }
      if (this.schedule_enabled) payload['scheduled'] = moment(this.schedule_datetime).utc().format("YYYY-MM-DD HH:mm")
      else payload['start_execution'] = this.start_execution

      // Add deployment to the DB
      axios.post('/deployments/pro', payload)
        .then((response) => {
          const data = response.data.data
          this.notification(response.data.message, 'success')
          // Refresh user coins
          this.$store.dispatch('coins', data['coins'])
          // Redirect page
          this.$router.push({ name:'deployment', params: { id: 'P' + data['execution_id'], admin: false }})
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading_code = false
        })
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  },
  watch: {
    queryDialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.field !== 'undefined') this.$refs.field.focus()
      })
    }
  }
}
</script>