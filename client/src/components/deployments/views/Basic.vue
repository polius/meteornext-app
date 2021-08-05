<template>
  <div>
    <v-container fluid grid-list-lg>
      <v-layout row wrap>
        <v-flex xs12>
          <v-form ref="form" style="padding:5px">
            <v-text-field ref="name" v-model="name" label="Name" :rules="[v => !!v || '']" required style="padding-top:10px;"></v-text-field>
            <v-select :loading="loading" v-model="release" :items="release_items" label="Release" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-select>
            
            <!-- EXECUTION -->
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

            <v-card style="margin-bottom:20px;">
              <v-toolbar flat dense color="#2e3131" style="margin-top:5px;">
                <v-toolbar-title class="white--text subtitle-1">QUERIES</v-toolbar-title>
                <v-divider class="mx-3" inset vertical></v-divider>
                <v-toolbar-items class="hidden-sm-and-down" style="padding-left:0px;">
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
              <v-data-table v-model="query_selected" :headers="query_headers" :items="query_items" item-key="id" show-select :hide-default-header="query_items.length == 0" :hide-default-footer="query_items.length < 11" class="elevation-1">
                <template v-ripple v-slot:[`header.data-table-select`]="{}">
                  <v-simple-checkbox
                    :value="query_items.length == 0 ? false : query_selected.length == query_items.length"
                    :indeterminate="query_selected.length > 0 && query_selected.length != query_items.length"
                    @click="query_selected.length == query_items.length ? query_selected = [] : query_selected = [...query_items]">
                  </v-simple-checkbox>
                </template>
              </v-data-table>
            </v-card>

            <!-- PARAMETERS -->
            <div>
              <v-tooltip right>
                <template v-slot:activator="{ on }">
                  <span v-on="on" class="subtitle-1 font-weight-regular white--text">
                    METHOD
                    <v-icon small style="margin-left:5px; margin-bottom:2px;" v-on="on">fas fa-question-circle</v-icon>
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

            <v-switch :disabled="loading" v-model="schedule_enabled" @change="schedule_change()" label="Scheduled" color="info" hide-details style="margin-top:-10px;"></v-switch>
            <v-text-field v-if="schedule_enabled && schedule_datetime != ''" solo v-model="schedule_datetime" @click="schedule_change()" title="Click to edit the schedule datetime" hide-details readonly style="margin-top:10px; margin-bottom:10px;"></v-text-field>

            <v-checkbox v-else v-model="start_execution" label="Start execution" color="primary" hide-details style="margin-top:15px; margin-bottom:20px;"></v-checkbox>
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
      name: '',
      databases: '',

      // Query
      query_headers: [{ text: 'Query', value: 'query' }],
      query_items: [],
      query_selected: [],
      query_mode: '', // new, edit, delete

      // Parameters
      release: '',
      release_items: [],
      environment: '',
      environment_items: [],
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
        mode: 'sql',
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
  components: { codemirror },
  created() {
    this.getReleases()
    this.getEnvironments()
  },
  mounted() {
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
      this.notification('Queries added successfully', '#00b16a')
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
      this.notification('Query edited successfully', '#00b16a')
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
      this.notification('Selected queries removed successfully', '#00b16a')
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
      this.loading = true
      // Build parameters
      var payload = {
        mode: 'BASIC',
        name: this.name,
        release: this.release,
        environment: this.environment,
        databases: this.databases,
        queries: JSON.stringify(this.query_items),
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
          // Refresh user coins
          this.$store.dispatch('app/coins', data['coins'])
          // Redirect page
          this.$router.push({ name:'deployment', params: { id: data['id'], admin: false, msg: response.data.message, color: '#00b16a' }})
        })
        .catch((error) => {
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
    }
  },
  watch: {
    queryDialog (val) {
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