<template>
  <div>
    <v-container fluid grid-list-lg>
      <v-layout row wrap>
        <v-flex xs12>
          <v-form ref="form" style="padding:5px">
            <v-text-field ref="name" v-model="name" label="Name" :rules="[v => !!v || '']" required style="padding-top:10px;"></v-text-field>
            <v-select :loading="loading_rel" v-model="release" :items="release_items" label="Release" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-select>
            <v-autocomplete :loading="loading_env" v-model="environment" :items="environment_items" item-value="id" item-text="name" label="Environment" :rules="[v => !!v || '']" required style="padding-top:0px;" hide-details>
              <template v-slot:item="{ item }" >
                <v-row align="center" no-gutters>
                  <v-col class="flex-grow-1 flex-shrink-1">
                    {{ item.name }}
                  </v-col>
                  <v-col cols="auto" class="flex-grow-0 flex-shrink-0">
                    <v-chip label><v-icon small :color="item.shared ? '#EF5354' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>{{ item.shared ? 'Shared' : 'Personal' }}</v-chip>
                  </v-col>
                </v-row>
              </template>
            </v-autocomplete>

            <!-- CODE -->
            <div style="margin-top:20px; margin-bottom:10px;">
              <v-tooltip right>
                <template v-slot:activator="{ on }">
                  <span v-on="on" class="subtitle-1 font-weight-regular white--text">
                    CODE
                    <v-icon small style="margin-left:5px; margin-bottom:4px;">fas fa-question-circle</v-icon>
                  </span>
                </template>
                <span>Press <span class="font-weight-medium" style="color:rgb(250, 130, 49)">ESC</span> when cursor is in the editor to toggle full screen editing</span>
              </v-tooltip>
            </div>
            <v-progress-linear v-if="loading_code" height="1px" color="info" indeterminate></v-progress-linear>
            <codemirror v-model="code" :options="cmOptions"></codemirror>

            <!-- PARAMETERS -->
            <div style="margin-top:20px">
              <v-tooltip right>
                <template v-slot:activator="{ on }">
                  <span v-on="on" class="subtitle-1 font-weight-regular white--text">
                    METHOD
                    <v-icon small style="margin-left:5px; margin-bottom:4px;" v-on="on">fas fa-question-circle</v-icon>
                  </span>
                </template>
                <span>
                  <b style="color:#00b16a">VALIDATE</b> Tests all server connections
                  <br>
                  <b class="orange--text">TEST</b> A simulation is performed (only SELECTs & SHOWs are executed)
                  <br>
                  <b style="color:#EF5354">DEPLOY</b> Executes ALL queries
                </span>
              </v-tooltip>
            </div>

            <v-radio-group v-model="method" style="margin-top:10px;">
              <v-radio value="validate" color="#00b16a">
                <template v-slot:label>
                  <div style="color:#00b16a;">VALIDATE</div>
                </template>
              </v-radio>
              <v-radio value="test" color="orange">
                <template v-slot:label>
                  <div class="orange--text">TEST</div>
                </template>
              </v-radio>
              <v-radio value="deploy" color="#EF5354">
                <template v-slot:label>
                  <div style="color:#EF5354">DEPLOY</div>
                </template>
              </v-radio>
            </v-radio-group>

            <v-switch :disabled="loading_env || loading_code" v-model="schedule_enabled" @change="schedule_change()" label="Scheduled" color="info" hide-details style="margin-top:-10px;"></v-switch>
            <v-text-field v-if="schedule_enabled && schedule_datetime != ''" solo v-model="schedule_datetime" @click="schedule_change()" title="Click to edit the schedule datetime" hide-details readonly style="margin-top:10px; margin-bottom:10px;"></v-text-field>

            <v-checkbox v-else v-model="start_execution" label="Start execution" color="primary" hide-details style="margin-top:15px; margin-bottom:20px;"></v-checkbox>
            <v-divider></v-divider>

            <div style="margin-top:20px;">
              <v-btn :loading="loading_env || loading_code" color="#00b16a" @click="submitDeploy()">CREATE DEPLOY</v-btn>
              <router-link to="/deployments"><v-btn :disabled="loading_env || loading_code" color="#EF5354" style="margin-left:5px">CANCEL</v-btn></router-link>
            </div>
          </v-form>
        </v-flex>
      </v-layout>
    </v-container>

    <v-dialog v-model="scheduleDialog" persistent width="290px">
      <v-date-picker v-if="schedule_mode=='date'" v-model="schedule_date" color="info" scrollable>
        <v-btn text color="#00b16a" @click="schedule_submit()">Confirm</v-btn>
        <v-btn text color="#EF5354" @click="schedule_close()">Cancel</v-btn>
        <v-spacer></v-spacer>
        <v-btn text color="info" @click="schedule_now()">Now</v-btn>
      </v-date-picker>
      <v-time-picker v-else-if="schedule_mode=='time'" v-model="schedule_time" color="info" format="24hr" scrollable>
        <v-btn text color="#00b16a" @click="schedule_submit()">Confirm</v-btn>
        <v-btn text color="#EF5354" @click="schedule_close()">Cancel</v-btn>
        <v-spacer></v-spacer>
        <v-btn text color="info" @click="schedule_now()">Now</v-btn>
      </v-time-picker>
    </v-dialog>

    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<style>
.CodeMirror {
  min-height: 450px;
  font-size: 14px;
}
.CodeMirror-scrollbar-filler {
  background-color: rgb(55, 53, 64);
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
import 'codemirror/theme/one-dark.css' // monokai.css

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
        theme: 'one-dark',
        keyMap: 'sublime',
        extraKeys: {
          Tab: function(cm) {
            if (cm.somethingSelected()) cm.indentSelection("add")
            else cm.replaceSelection("    " , "end")
          },
          "Esc": function(cm) {
            cm.setOption("fullScreen", !cm.getOption("fullScreen"))
          },
          "Ctrl-S": function(cm) {
            var textFileAsBlob = new Blob([cm.getValue()], { type: "text/plain;charset=utf-8" })
            var downloadLink = document.createElement("a")
            downloadLink.download = "meteor.py"
            downloadLink.style.display = "none"
            if (window.webkitURL != null) downloadLink.href = window.webkitURL.createObjectURL(textFileAsBlob)
            else downloadLink.href = window.URL.createObjectURL(textFileAsBlob)
            document.body.appendChild(downloadLink)
            downloadLink.click()
            document.body.removeChild(downloadLink)
          },
          "Cmd-S": function(cm) {
            var textFileAsBlob = new Blob([cm.getValue()], { type: "text/plain;charset=utf-8" })
            var downloadLink = document.createElement("a")
            downloadLink.download = "meteor.py"
            downloadLink.style.display = "none"
            if (window.webkitURL != null) downloadLink.href = window.webkitURL.createObjectURL(textFileAsBlob)
            else downloadLink.href = window.URL.createObjectURL(textFileAsBlob)
            document.body.appendChild(downloadLink)
            downloadLink.click()
            document.body.removeChild(downloadLink)
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
  mounted() {
    if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
    requestAnimationFrame(() => this.$refs.name.focus())
  },
  methods: {
    getReleases() {
      axios.get('/deployments/releases/active')
        .then((response) => {
          for (var i = 0; i < response.data.data.length; ++i) this.release_items.push(response.data.data[i]['name'])
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading_rel = false)
    },
    getEnvironments() {
      axios.get('/inventory/environments/list')
        .then((response) => {
          this.environment_items = response.data.data.map(x => ({id: x.id, name: x.name, shared: x.shared }))        
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading_env = false)
    },
    getCode() {
      this.loading_code = true
      axios.get('/deployments/blueprint')
        .then((response) => {
          this.code = response.data.data
          this.cmOptions.readOnly = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading_code = false)
    },
    schedule_close() {
      this.scheduleDialog = false
      this.schedule_enabled = this.schedule_datetime != ''
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
          const date = moment()
          this.schedule_date = date.format("YYYY-MM-DD")
          this.schedule_time = date.format("HH:mm")
        }
        this.scheduleDialog = true
      }
      else this.scheduleDialog = false
    },
    schedule_submit() {
      if (this.schedule_mode == 'date') {
        this.schedule_mode = 'time'
      }
      else if (this.schedule_mode == 'time') {
        this.schedule_datetime = this.schedule_date + ' ' + this.schedule_time
        this.schedule_mode = 'date'
        this.scheduleDialog = false
      }
    },
    submitDeploy() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please fill the required fields', '#EF5354')
        return
      }
      this.loading_code = true
      // Build parameters
      const payload = {
        mode: 'PRO',
        name: this.name,
        release: this.release,
        environment: this.environment,
        code: this.code,
        method: this.method.toUpperCase(),
        scheduled: null,
        start_execution: false,
        url: window.location.protocol + '//' + window.location.host
      }
      if (this.schedule_enabled) payload['scheduled'] = moment(this.schedule_datetime).utc().format("YYYY-MM-DD HH:mm") + ':00'
      else payload['start_execution'] = this.start_execution

      // Add deployment to the DB
      axios.post('/deployments', payload)
        .then((response) => {
          const data = response.data.data
          this.notification(response.data.message, '#00b16a')
          // Refresh user coins
          this.$store.dispatch('app/coins', data['coins'])
          // Redirect page
          this.$router.push({ name:'deployment', params: { id: data['id'], admin: false, msg: response.data.message, color: '#00b16a' }})
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading_code = false)
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