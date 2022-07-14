<template>
  <div>
    <v-container fluid grid-list-lg style="padding:15px">
      <v-layout row wrap>
        <v-flex xs12>
          <v-form ref="form">
            <v-text-field ref="name" v-model="name" label="Name" :rules="[v => !!v || '']" required style="padding-top:10px;"></v-text-field>
            <v-select :loading="loading" v-model="release" :items="release_items" label="Release" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-select>
            <v-autocomplete :loading="loading" v-model="environment" :items="environment_items" item-value="id" item-text="name" label="Environment" :rules="[v => !!v || '']" required style="padding-top:0px;">
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
            <v-text-field v-model="databases" label="Databases" hint="Separated by commas. Wildcards allowed: % _" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>
            <!-- QUERIES -->
            <v-card style="margin-bottom:20px;">
              <v-toolbar flat dense color="#2e3131" style="margin-top:5px;">
                <v-toolbar-title class="white--text subtitle-1">QUERIES</v-toolbar-title>
                <v-divider class="mx-3" inset vertical></v-divider>
                <v-toolbar-items style="padding-left:0px;">
                  <v-btn text @click='newQuery()'><v-icon small style="margin-right:10px">fas fa-plus</v-icon>NEW</v-btn>
                  <v-btn :disabled="query_selected.length != 1" text @click="cloneQuery()"><v-icon small style="margin-right:10px">fas fa-clone</v-icon>CLONE</v-btn>
                  <v-btn :disabled="query_selected.length != 1" text @click="editQuery()"><v-icon small style="margin-right:10px">fas fa-feather-alt</v-icon>EDIT</v-btn>
                  <v-btn :disabled="query_selected.length == 0" text @click='deleteQuery()'><v-icon small style="margin-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
                  <v-divider class="mx-3" inset vertical></v-divider>
                  <v-btn :disabled="query_items.length < 2 || query_selected.length != 1" text title="Move query to the top" @click="moveTopQuery()"><v-icon small style="margin-right:10px">fas fa-level-up-alt</v-icon>TOP</v-btn>
                  <v-btn :disabled="query_items.length < 2 || query_selected.length != 1" text title="Move query up" @click="moveUpQuery()"><v-icon small style="margin-right:10px">fas fa-arrow-up</v-icon>UP</v-btn>
                  <v-btn :disabled="query_items.length < 2 || query_selected.length != 1" text title="Move query down" @click="moveDownQuery()"><v-icon small style="margin-right:10px">fas fa-arrow-down</v-icon>DOWN</v-btn>
                  <v-btn :disabled="query_items.length < 2 || query_selected.length != 1" text title="Move query to the bottom" @click="moveBottomQuery()"><v-icon small style="margin-right:10px">fas fa-level-down-alt</v-icon>BOTTOM</v-btn>
                </v-toolbar-items>
              </v-toolbar>
              <v-divider></v-divider>
              <v-data-table v-model="query_selected" :headers="query_headers" :items="query_items" item-key="id" show-select :hide-default-header="query_items.length == 0" :hide-default-footer="query_items.length < 11" class="elevation-1" mobile-breakpoint="0">
                <template v-ripple v-slot:[`header.data-table-select`]="{}">
                  <v-simple-checkbox
                    :value="query_items.length == 0 ? false : query_selected.length == query_items.length"
                    :indeterminate="query_selected.length > 0 && query_selected.length != query_items.length"
                    @click="query_selected.length == query_items.length ? query_selected = [] : query_selected = [...query_items]">
                  </v-simple-checkbox>
                </template>
                <template v-slot:[`item.query`]="{ item }">
                  <td style="padding-top:5px; padding-bottom:5px">{{ item.query }}</td>
                </template>
              </v-data-table>
            </v-card>
            <!-- METHOD -->
            <div>
              <v-tooltip right>
                <template v-slot:activator="{ on }">
                  <span v-on="on" class="subtitle-1 font-weight-regular white--text">
                    METHOD
                    <v-icon small style="margin-left:5px; margin-bottom:4px;" v-on="on">fas fa-question-circle</v-icon>
                  </span>
                </template>
                <span>
                  <b style="color:#00b16a">VALIDATE</b> Tests all server connections.
                  <br>
                  <b class="orange--text">TEST</b> A simulation is performed (only SELECTs & SHOWs are executed).
                  <br>
                  <b style="color:#EF5354">DEPLOY</b> Executes ALL queries.
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
            <div style="margin-top:15px">
              <v-tooltip right>
                <template v-slot:activator="{ on }">
                  <span v-on="on" class="subtitle-1 font-weight-regular white--text">
                    SCHEDULE
                    <v-icon small style="margin-left:5px; margin-bottom:4px;" v-on="on">fas fa-question-circle</v-icon>
                  </span>
                </template>
                <span>Enable this option to decide when the deployment should be executed.</span>
              </v-tooltip>
            </div>
            <v-switch v-model="schedule_enabled" label="Schedule execution" color="info" hide-details style="margin-top:15px; margin-bottom:15px; padding:0px"></v-switch>
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
                <v-text-field ref="schedule_datetime" filled readonly v-model="schedule_datetime" label="Execution time" hide-details style="margin-top:15px; margin-bottom:15px"></v-text-field>
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
                <v-select filled v-model="schedule_month_day" label="Day" :items="[{id: 'first', val: 'First day of the month'}, {id: 'last', val: 'Last day of the month'}]" item-value="id" item-text="val" hide-details style="margin-top:10px; margin-bottom:15px"></v-select>
              </div>
              <div v-show="nextExecution != null" style="margin-bottom:10px">
                <div class="body-1 font-weight-light white--text">The execution will start at:</div>
                <v-text-field solo readonly v-model="nextExecution" hide-details style="margin-top:5px; margin-bottom:15px"></v-text-field>
              </div>
            </div>
            <!-- START EXECUTION -->
            <div v-show="!schedule_enabled" style="margin-top:15px">
              <v-tooltip right>
                <template v-slot:activator="{ on }">
                  <span v-on="on" class="subtitle-1 font-weight-regular white--text">
                    START
                    <v-icon small style="margin-left:5px; margin-bottom:4px;" v-on="on">fas fa-question-circle</v-icon>
                  </span>
                </template>
                <span>Enable this option to start the execution right away after being created.</span>
              </v-tooltip>
            </div>
            <v-checkbox v-show="!schedule_enabled" v-model="start_execution" label="Start execution" color="primary" hide-details style="margin-top:15px; margin-bottom:20px; padding:0px"></v-checkbox>
            <v-divider></v-divider>
            <div style="margin-top:20px;">
              <v-btn :loading="loading" color="#00b16a" @click="submitDeploy()">CREATE DEPLOY</v-btn>
              <router-link to="/deployments"><v-btn :disabled="loading" color="#EF5354" style="margin-left:5px">CANCEL</v-btn></router-link>
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

    <v-dialog v-model="queryDialog" eager persistent max-width="896px">
      <v-toolbar flat dense color="primary">
        <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:1px">{{query_mode == 'new' ? 'fas fa-plus' : query_mode == 'edit' ? 'fas fa-feather-alt' : 'fas fa-minus'}}</v-icon>{{ queryDialogTitle }}</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn icon @click="queryDialog = false" style="width:40px; height:40px"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
      </v-toolbar>
      <v-card>
        <v-card-text style="padding: 0px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <div v-if="query_mode == 'delete'" class="subtitle-1" style="margin:15px">{{ queryDialogText }}</div>
                <div v-else>
                  <codemirror ref="codemirror" v-model="code" :options="cmOptions"></codemirror>
                </div>
                <v-divider style="margin:15px"></v-divider>
                <div style="padding:0px 15px 15px 15px">
                  <v-btn color="#00b16a" @click="actionConfirm()">Confirm</v-btn>
                  <v-btn color="#EF5354" @click="queryDialog=false" style="margin-left:5px">Cancel</v-btn>
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

<style scoped>
::v-deep .CodeMirror {
  min-height: min(60vh, 416px);
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
import 'codemirror/mode/sql/sql.js'
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
      // Query
      query_headers: [{ text: 'Query', value: 'query' }],
      // query_items: [],
      query_selected: [],
      query_mode: '', // new, edit, delete

      // Parameters
      release_items: [],
      environment_items: [],
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
      code: '',
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
        mode: 'text/x-mysql',
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
          },
        }
      },

      // Loading Fields
      loading: true,
      
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
  },
  mounted() {
    if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
    requestAnimationFrame(() => this.$refs.name.focus())
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
    databases: {
      get() { return this.fields.databases },
      set(val) { this.$emit('change', {"name": "databases", "value": val}) }
    },
    query_items: {
      get() { return this.fields.queries },
      set(val) { this.$emit('change', {"name": "queries", "value": val}) }
    },
    nextExecution() {
      const now = moment().seconds(0).milliseconds(0)
      if (this.schedule_time2.length == 0) return null
      if (this.schedule_type == 'one_time') {
        const schedule = moment(this.schedule_date2 + ' ' + this.schedule_time2, "YYYY-MM-DD HH:mm")
        if (this.schedule_date2.length == 0) return null
        return schedule.format("YYYY-MM-DD HH:mm Z (dddd)")
      }
      else if (this.schedule_type == 'daily') {
        const schedule = moment(now.format("YYYY-MM-DD") + ' ' + this.schedule_time2, "YYYY-MM-DD HH:mm")
        if (schedule >= now) return schedule.format("YYYY-MM-DD HH:mm Z (dddd)")
        else return schedule.add(1, 'days').format("YYYY-MM-DD HH:mm Z (dddd)")
      }
      else if (this.schedule_type == 'weekly') {
        if (this.schedule_week.length == 0) return null
        const schedule = moment(now.format("YYYY-MM-DD") + ' ' + this.schedule_time2, "YYYY-MM-DD HH:mm")
        const startDays = this.schedule_week.map(x => moment(schedule.isoWeekday(Number(x)))).sort((a,b) => moment(a).diff(b))
        const startDay = startDays.find(x => x >= now)
        if (startDay === undefined) return startDays[0].add(1, 'weeks').format("YYYY-MM-DD HH:mm Z (dddd)")
        else return startDay.format("YYYY-MM-DD HH:mm Z (dddd)")
      }
      else if (this.schedule_type == 'monthly') {
        if (this.schedule_month.length == 0) return null
        const schedule = moment(now.format("YYYY-MM-DD") + ' ' + this.schedule_time2, "YYYY-MM-DD HH:mm")
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
        .finally(() => this.loading = false)
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
        .finally(() => this.loading = false)
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
    newQuery() {
      this.query_mode = 'new'
      this.code = ''
      this.queryDialogTitle = 'NEW QUERIES'
      this.queryDialog = true
    },
    editQuery () {
      this.query_mode = 'edit'
      this.code = this.query_selected[0]['query']
      this.queryDialogTitle = 'EDIT QUERY'
      this.queryDialog = true
    },
    deleteQuery() {
      this.query_mode = 'delete'
      this.queryDialogTitle = 'DELETE QUERY'
      this.queryDialogText = 'Are you sure you want to delete the selected queries?'
      this.queryDialog = true
    },
    actionConfirm() {
      if (this.query_mode == 'new') this.newQueryConfirm()
      else if (this.query_mode == 'edit') this.editQueryConfirm()
      else if (this.query_mode == 'delete') this.deleteQueryConfirm()
    },
    newQueryConfirm() {
      // Check if all fields are filled
      if (this.code.trim().length == 0) {
        this.notification('Please enter a query', '#EF5354')
        return
      }

      // Parse Queries
      var queries = this.parseQueries()

      // Add queries into the data table
      for (var q = 0; q < queries.length; ++q) {
        if (queries[q]['query'] != ';') this.query_items.push(queries[q])
      }
      
      // Post-tasks
      this.query_selected = []
      this.queryDialog = false
      this.notification('Queries added', '#00b16a')
    },
    editQueryConfirm() {
      // Check if all fields are filled
      if (this.code.trim().length == 0) {
        this.notification('Please enter a query', '#EF5354')
        return
      }

      // Parse Queries
      if (this.parseQueries().length > 1) {
        this.notification('Multiple queries detected', '#EF5354')
        return
      }

      // Get Item Position
      for (var i = 0; i < this.query_items.length; ++i) {
        if (this.query_items[i]['id'] == this.query_selected[0]['id']) break
      }

      // Edit item in the data table
      this.query_items.splice(i, 1, {"id": this.query_items[i]['id'], "query": this.code})
      this.query_selected = []
      this.queryDialog = false
      this.notification('Query edited', '#00b16a')
    },
    deleteQueryConfirm() {
      while(this.query_selected.length > 0) {
        var s = this.query_selected.pop()
        for (var i = 0; i < this.query_items.length; ++i) {
          if (this.query_items[i]['id'] == s['id']) {
            // Delete Item
            this.query_items.splice(i, 1)
            break
          }
        }
      }
      this.notification('Selected queries removed', '#00b16a')
      this.queryDialog = false
    },
    parseQueries() {
      // Build multi-queries
      var id = (this.query_items.length == 0) ? 1: this.query_items.reduce((acc, val) => val.id > acc ? val.id : acc, 0)+1
      var queries = []
      var start = 0;
      var chars = []
      for (var i = 0; i < this.code.length; ++i) {
        if (this.code[i] == ';' && chars.length == 0) {
          queries.push({"id": id, "query": this.code.substring(start, i+1).trim()})
          id += 1
          start = i+1
        }
        else if (this.code[i] == '"' && (i == 0 || this.code[i-1] != '\\')) {
          if (chars.length == 0) chars.push('"')
          else if (chars[chars.length-1] == '"') chars.pop()
        }
        else if (this.code[i] == "'" && (i == 0 || this.code[i-1] != '\\')) {
          if (chars.length == 0) chars.push("'")
          else if (chars[chars.length-1] == "'") chars.pop()
        }
      }
      if (start < i) queries.push({"id": id, "query": this.code.substring(start, i).trim()})
      // Return parsed queries
      return queries
    },
    submitDeploy() {
      // Check if all fields are filled
      if (!this.$refs.form.validate()) {
        this.notification('Please fill the required fields', '#EF5354')
        return
      }
      if (this.query_items.length == 0) {
        this.notification('Please enter a query to deploy', '#EF5354')
        return
      }
      if (this.schedule_enabled && this.schedule_datetime.length == 0) {
        this.notification('Please enter a schedule time', '#EF5354')
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
      this.loading = true
      // Build parameters
      var payload = {
        mode: 'BASIC',
        name: this.name,
        release: this.release,
        environment: this.environment,
        databases: this.databases,
        queries: this.query_items.map(x => x.query),
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
          // Refresh user coins
          this.$store.dispatch('app/coins', data['coins'])
          // Redirect page
          this.$router.push({ name: 'deployments.execution', params: { uri: data['uri'], admin: false, msg: response.data.message, color: '#00b16a' }})
        })
        .catch((error) => {
          console.log(error)
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    cloneQuery() {
      let item = {id: this.query_items.reduce((acc, val) => val.id > acc ? val.id : acc, 0)+1, query: this.query_selected[0].query}
      this.query_items.push(item)
      this.query_selected = []
    },
    moveTopQuery() {
      let currentPos = this.query_items.findIndex(x => x.id == this.query_selected[0].id)
      this.arraymove(this.query_items, currentPos, 0)
    },
    moveUpQuery() {
      let currentPos = this.query_items.findIndex(x => x.id == this.query_selected[0].id)
      if (currentPos > 0) this.arraymove(this.query_items, currentPos, currentPos-1)
    },
    moveDownQuery() {
      let currentPos = this.query_items.findIndex(x => x.id == this.query_selected[0].id)
      if (currentPos < this.query_items.length-1) this.arraymove(this.query_items, currentPos, currentPos+1)
    },
    moveBottomQuery() {
      let currentPos = this.query_items.findIndex(x => x.id == this.query_selected[0].id)
      this.arraymove(this.query_items, currentPos, this.query_items.length-1)
    },
    arraymove(arr, fromIndex, toIndex) {
      let element = arr[fromIndex]
      arr.splice(fromIndex, 1)
      arr.splice(toIndex, 0, element)
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    },
  },
  watch: {
    schedule_type(val) {
      if (val == 'one_time') this.schedule_datetime = (this.schedule_date2.length == 0) ? '' : (this.schedule_date2 + ' ' + this.schedule_time2).trim()
      else this.schedule_datetime = this.schedule_time2
    },
    queryDialog(val) {
      if (!val) return
      this.cmOptions.readOnly = true
      this.$nextTick(() => {
        if (this.$refs.codemirror === undefined) return
        const codemirror = this.$refs.codemirror.codemirror
        setTimeout(() => { codemirror.refresh(); codemirror.focus(); this.cmOptions.readOnly = false }, 200)
      })
    },
  }
}
</script>