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
            <!-- METHOD -->
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
            <v-radio-group v-model="method" style="margin-top:10px" hide-details>
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
            <!-- SCHEDULE -->
            <v-switch v-model="schedule_enabled" label="Scheduled" color="info" hide-details style="margin-top:15px; margin-bottom:15px"></v-switch>
            <div v-show="schedule_enabled">
              <span class="body-1 font-weight-light white--text">Select the schedule type.</span>
              <v-radio-group row v-model="schedule_type" style="margin-top:10px; margin-bottom:15px" hide-details>
                <v-radio value="one_time">
                  <template v-slot:label>
                    <div class="white--text">One time</div>
                  </template>
                </v-radio>
                <v-radio value="daily">
                  <template v-slot:label>
                    <div class="white--text">Daily</div>
                  </template>
                </v-radio>
                <v-radio value="weekly">
                  <template v-slot:label>
                    <div class="white--text">Weekly</div>
                  </template>
                </v-radio>
                <v-radio value="monthly">
                  <template v-slot:label>
                    <div class="white--text">Monthly</div>
                  </template>
                </v-radio>
              </v-radio-group>
              <span class="body-1 font-weight-light white--text">Select the execution time.</span>
              <div @click="schedule_change">
                <v-text-field ref="schedule_datetime" filled readonly v-model="schedule_datetime" label="Execution time" :rules="[v => !!v || '']" required hide-details style="margin-top:15px; margin-bottom:15px"></v-text-field>
              </div>
              <div v-show="schedule_type == 'weekly'">
                <span class="body-1 font-weight-light white--text">Select what days of the week the schedule should execute.</span>
                <v-row no-gutters>
                  <v-col cols="auto" style="width:150px">
                    <v-checkbox v-model="schedule_week" label="Monday" value="1" hide-details style="padding-top:0px"></v-checkbox>
                  </v-col>
                  <v-col cols="auto" style="width:150px">
                    <v-checkbox v-model="schedule_week" label="Tuesday" value="2" hide-details style="padding-top:0px"></v-checkbox>
                  </v-col>
                  <v-col cols="auto" style="width:150px">
                    <v-checkbox v-model="schedule_week" label="Wednesday" value="3" hide-details style="padding-top:0px"></v-checkbox>
                  </v-col>
                </v-row>
                <v-row no-gutters>
                  <v-col cols="auto" style="width:150px">
                    <v-checkbox v-model="schedule_week" label="Thursday" value="4" hide-details style="padding-top:0px"></v-checkbox>
                  </v-col>
                  <v-col cols="auto" style="width:150px">
                    <v-checkbox v-model="schedule_week" label="Friday" value="5" hide-details style="padding-top:0px"></v-checkbox>
                  </v-col>
                  <v-col cols="auto" style="width:150px">
                    <v-checkbox v-model="schedule_week" label="Saturday" value="6" hide-details style="padding-top:0px"></v-checkbox>
                  </v-col>
                </v-row>
                <v-row no-gutters style="margin-bottom:15px">
                  <v-col cols="auto" style="width:150px">
                    <v-checkbox v-model="schedule_week" label="Sunday" value="7" hide-details style="padding-top:0px"></v-checkbox>
                  </v-col>
                </v-row>
              </div>
              <div v-show="schedule_type == 'monthly'">
                <span class="body-1 font-weight-light white--text">Select what months the schedule should execute.</span>
                <v-row no-gutters>
                  <v-col cols="auto" style="width:150px">
                    <v-checkbox v-model="schedule_month" label="January" value="1" hide-details style="padding-top:0px"></v-checkbox>
                  </v-col>
                  <v-col cols="auto" style="width:150px">
                    <v-checkbox v-model="schedule_month" label="February" value="2" hide-details style="padding-top:0px"></v-checkbox>
                  </v-col>
                  <v-col cols="auto" style="width:150px">
                    <v-checkbox v-model="schedule_month" label="March" value="3" hide-details style="padding-top:0px"></v-checkbox>
                  </v-col>
                  <v-col cols="auto" style="width:150px">
                    <v-checkbox v-model="schedule_month" label="April" value="4" hide-details style="padding-top:0px"></v-checkbox>
                  </v-col>
                </v-row>
                <v-row no-gutters>
                  <v-col cols="auto" style="width:150px">
                    <v-checkbox v-model="schedule_month" label="May" value="5" hide-details style="padding-top:0px"></v-checkbox>
                  </v-col>
                  <v-col cols="auto" style="width:150px">
                    <v-checkbox v-model="schedule_month" label="June" value="6" hide-details style="padding-top:0px"></v-checkbox>
                  </v-col>
                  <v-col cols="auto" style="width:150px">
                    <v-checkbox v-model="schedule_month" label="July" value="7" hide-details style="padding-top:0px"></v-checkbox>
                  </v-col>
                  <v-col cols="auto" style="width:150px">
                    <v-checkbox v-model="schedule_month" label="August" value="8" hide-details style="padding-top:0px"></v-checkbox>
                  </v-col>
                </v-row>
                <v-row no-gutters style="margin-bottom:15px">
                  <v-col cols="auto" style="width:150px">
                    <v-checkbox v-model="schedule_month" label="September" value="9" hide-details style="padding-top:0px"></v-checkbox>
                  </v-col>
                  <v-col cols="auto" style="width:150px">
                    <v-checkbox v-model="schedule_month" label="October" value="10" hide-details style="padding-top:0px"></v-checkbox>
                  </v-col>
                  <v-col cols="auto" style="width:150px">
                    <v-checkbox v-model="schedule_month" label="November" value="11" hide-details style="padding-top:0px"></v-checkbox>
                  </v-col>
                  <v-col cols="auto" style="width:150px">
                    <v-checkbox v-model="schedule_month" label="December" value="12" hide-details style="padding-top:0px"></v-checkbox>
                  </v-col>
                </v-row>
                <span class="body-1 font-weight-light white--text">Select the day to be executed.</span>
                <v-select filled v-model="schedule_month_day" label="Day" :items="[{id: 'first', val: 'First day of the month'}, {id: 'last', val: 'Last day of the month'}]" item-value="id" item-text="val" :rules="[v => !!v || '']" required hide-details style="margin-top:10px; margin-bottom:15px"></v-select>
              </div>
              <div v-show="nextExecution != null" style="margin-bottom:10px">
                <div class="body-1 font-weight-light white--text">The execution will start at:</div>
                <v-text-field solo readonly v-model="nextExecution" hide-details style="margin-top:5px; margin-bottom:15px"></v-text-field>
              </div>
            </div>
            <!-- START EXECUTION -->
            <v-checkbox v-show="!schedule_enabled" v-model="start_execution" label="Start execution" color="primary" hide-details style="margin-top:10px; margin-bottom:20px;"></v-checkbox>
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
        <v-btn text color="info" @click="schedule_now">Now</v-btn>
        <v-spacer></v-spacer>
        <v-btn text color="#EF5354" @click="schedule_close">Cancel</v-btn>
        <v-btn text color="#00b16a" @click="schedule_submit">Confirm</v-btn>
      </v-date-picker>
      <v-time-picker v-else-if="schedule_mode=='time'" v-model="schedule_time" color="info" format="24hr" scrollable>
        <v-btn text color="info" @click="schedule_now">Now</v-btn>
        <v-spacer></v-spacer>
        <v-btn text color="#EF5354" @click="schedule_close">Cancel</v-btn>
        <v-btn text color="#00b16a" @click="schedule_submit">Confirm</v-btn>
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
      // Execution
      environment_items: [],

      // Init Code Parameters
      cmOptions: {
        readOnly: false,
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
      release_items: [],
      method: 'validate',
      start_execution: false,

      // Schedule
      scheduleDialog: false,
      schedule_enabled: false,
      schedule_type: 'one_time',
      schedule_week: [],
      schedule_month: [],
      schedule_month_day: 'first',
      schedule_mode: 'date',
      schedule_date: '',
      schedule_time: '',
      schedule_date2: '',
      schedule_time2: '',
      schedule_datetime: '',

      // Query Dialog
      queryDialog: false,
      queryDialogTitle: '',
      
      // Loading Fields
      loading_code: false,
      loading_env: true,
      loading_rel: true,

      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarColor: '',
      snackbarText: ''
    }
  },
  props: ['fields'],
  components: { codemirror },
  created() {
    this.getReleases()
    this.getEnvironments()
    if (this.$route.params.uri == undefined) this.getCode()
  },
  computed: {
    name: {
      get() { return this.fields.name },
      set(val) { this.$emit('change', {"name": "name", "value": val}) }
    },
    release: {
      get() { return this.fields.release },
      set(val) { this.$emit('change', {"name": "release", "value": val}) }
    },
    environment: {
      get() { return this.fields.environment },
      set(val) { this.$emit('change', {"name": "environment", "value": val}) }
    },
    code: {
      get() { return this.fields.code },
      set(val) { this.$emit('change', {"name": "code", "value": val}) }
    },
    nextExecution() {
      if (this.schedule_time2.length == 0) return null
      const schedule = moment(this.schedule_date + ' ' + this.schedule_time2, "YYYY-MM-DD HH:mm")
      const now = moment().seconds(0).milliseconds(0)
      if (this.schedule_type == 'one_time') {
        if (this.schedule_date2.length == 0) return null
        return schedule.format("YYYY-MM-DD HH:mm Z (dddd)")
      }
      else if (this.schedule_type == 'daily') {
        if (schedule >= now) return schedule.format("YYYY-MM-DD HH:mm Z (dddd)")
        else return schedule.add(1, 'days').format("YYYY-MM-DD HH:mm Z (dddd)")
      }
      else if (this.schedule_type == 'weekly') {
        if (this.schedule_week.length == 0) return null
        const startDays = this.schedule_week.map(x => moment(schedule.isoWeekday(Number(x)))).sort((a,b) => moment(a).diff(b))
        const startDay = startDays.find(x => x >= now)
        if (startDay === undefined) return startDays[0].add(1, 'weeks').format("YYYY-MM-DD HH:mm Z (dddd)")
        else return startDay.format("YYYY-MM-DD HH:mm Z (dddd)")
      }
      else if (this.schedule_type == 'monthly') {
        if (this.schedule_month.length == 0) return null
        const startDays = this.schedule_month.map(x => {
          let date = moment(schedule.year() + '-' + ('0' + x).slice(-2) + '-01', "YYYY-MM-DD")
          if (this.schedule_month_day == 'last') date = moment(schedule.year() + '-' + ('0' + x).slice(-2) + '-' + date.endOf('month').format("DD"), "YYYY-MM-DD")
          return date
        }).sort((a,b) => moment(a).diff(b))
        const startDay = startDays.find(x => x >= now)
        if (startDay === undefined) return startDays[0].add(1, 'year').format("YYYY-MM-DD HH:mm Z (dddd)")
        else return startDay.format("YYYY-MM-DD HH:mm Z (dddd)")
      }
      return null
    }
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
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading_code = false)
    },
    schedule_close() {
      this.scheduleDialog = false
    },
    schedule_now() {
      const date = moment()
      if (this.schedule_mode == 'date') this.schedule_date = date.format("YYYY-MM-DD")
      else if (this.schedule_mode == 'time') this.schedule_time = date.format("HH:mm")
    },
    schedule_change() {
      const date = moment()
      if (this.schedule_datetime.length == 0) {
        this.schedule_date = date.format("YYYY-MM-DD")
        this.schedule_time = date.format("HH:mm")
      }
      this.schedule_mode = (this.schedule_type == 'one_time') ? 'date' : 'time'
      this.scheduleDialog = true
    },
    schedule_submit() {
      if (this.schedule_mode == 'date') {
        this.schedule_mode = 'time'
      }
      else if (this.schedule_mode == 'time') {
        this.schedule_time2 = this.schedule_time
        if (this.schedule_type == 'one_time') {
          this.schedule_date2 = this.schedule_date
          this.schedule_datetime = this.schedule_date + ' ' + this.schedule_time
        }
        else this.schedule_datetime = this.schedule_time
        this.scheduleDialog = false
      }
    },
    submitDeploy() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please fill the required fields', '#EF5354')
        return
      }
      if (this.schedule_enabled && this.schedule_type == 'weekly' && this.schedule_week.length == 0) {
        this.notification('Please select at least one day of week', '#EF5354')
        return
      }
      if (this.schedule_enabled && this.schedule_type == 'monthly' && this.schedule_month.length == 0) {
        this.notification('Please select at least one month', '#EF5354')
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
        url: window.location.protocol + '//' + window.location.host
      }
      if (this.schedule_enabled) {
        payload['schedule_type'] = this.schedule_type
        if (this.schedule_type == 'one_time') {
          payload['schedule_value'] = moment(this.schedule_datetime).utc().format("YYYY-MM-DD HH:mm")
        }
        else if (this.schedule_type == 'daily') {
          payload['schedule_value'] = moment(this.schedule_datetime, "HH:mm").utc().format("HH:mm")
        }
        else if (this.schedule_type == 'weekly') {
          payload['schedule_value'] = moment(this.schedule_datetime, "HH:mm").utc().format("HH:mm")
          payload['schedule_rules'] = {"rules": this.schedule_week.map(Number).sort((a, b) => a - b)}
        }
        else if (this.schedule_type == 'monthly') {
          payload['schedule_value'] = moment(this.schedule_datetime, "HH:mm").utc().format("HH:mm")
          payload['schedule_rules'] = {"rules": this.schedule_month.map(Number).sort((a, b) => a - b), "day": this.schedule_month_day}
        }
      }
      else payload['start_execution'] = this.start_execution

      // Add deployment to the DB
      axios.post('/deployments', payload)
        .then((response) => {
          const data = response.data.data
          this.notification(response.data.message, '#00b16a')
          // Refresh user coins
          this.$store.dispatch('app/coins', data['coins'])
          // Redirect page
          this.$router.push({ name: 'deployments.execution', params: { uri: data['uri'], admin: false, msg: response.data.message, color: '#00b16a' }})
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
    schedule_type(val) {
      if (val == 'one_time') this.schedule_datetime = (this.schedule_date2.length == 0) ? '' : (this.schedule_date2 + ' ' + this.schedule_time2).trim()
      else this.schedule_datetime = this.schedule_time2
    },
    queryDialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.field !== 'undefined') this.$refs.field.focus()
      })
    }
  }
}
</script>