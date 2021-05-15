<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="body-2 white--text font-weight-medium"><v-icon small style="margin-right:10px">fas fa-bolt</v-icon>CLIENT</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text class="body-2"><v-icon small style="padding-right:10px">fas fa-database</v-icon>SERVERS</v-btn>
          <v-btn @click="filterDialog = true" text class="body-2" :style="{ backgroundColor : filterApplied ? '#4ba1f1' : '' }"><v-icon small style="padding-right:10px">fas fa-sliders-h</v-icon>FILTER</v-btn>
          <v-btn @click="refresh" text class="body-2"><v-icon small style="margin-right:10px">fas fa-sync-alt</v-icon>REFRESH</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
        </v-toolbar-items>
        <v-text-field v-model="search" append-icon="search" label="Search" @input="onSearch" color="white" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table :headers="headers" :items="items" :options.sync="options" :server-items-length="total" :hide-default-footer="total < 11" :loading="loading" :expanded.sync="expanded" single-expand item-key="id" show-expand class="elevation-1">
        <template v-slot:[`item.date`]="{ item }">
          <span style="display:block; min-width:130px">{{ item.date }}</span>
        </template>
        <template v-slot:[`item.user`]="{ item }">
          <span style="display:block; min-width:44px">{{ item.user }}</span>
        </template>
        <template v-slot:[`item.server`]="{ item }">
          <span style="display:block; min-width:55px">{{ item.server }}</span>
        </template>
        <template v-slot:[`item.database`]="{ item }">
          <span style="display:block; min-width:70px">{{ item.database }}</span>
        </template>
        <template v-slot:[`item.status`]="{ item }">
          <span style="display:block; min-width:78px">
            <v-icon small :title="item.status ? 'Success' : 'Failed'" :style="`color:${item.status ? '#00b16a' : '#e74d3c'}; margin-right:5px; margin-bottom:2px`">{{ item.status ? 'fas fa-check-circle' : 'fas fa-times-circle' }}</v-icon>
            {{ item.status ? 'Success' : 'Failed' }}
          </span>
        </template>
        <template v-slot:[`item.query`]="{ item }">
          <span style="white-space:nowrap">{{ item.query }}</span>
        </template>
        <template v-slot:expanded-item="{ headers, item }">
          <td :colspan="headers.length">
            <div v-if="item.records != null" style="margin-top:10px">
              Records:
              <span style="margin-left:6px">{{ item.records }}</span>
            </div>
            <div v-if="item.elapsed != null" style="margin-top:2px">
              Elapsed:
              <span style="margin-left:8px">{{ item.elapsed + 's' }}</span>
            </div>
            <div v-if="item.error != null" style="margin-top:10px">
              Error:
              <span style="margin-left:5px">{{ item.error }}</span>
            </div>
            <div id="editor" style="width:calc(100vw - 51px); margin-top:10px; margin-bottom:15px"></div>
          </td>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="filterDialog" max-width="50%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:3px">fas fa-sliders-h</v-icon>FILTER</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="filterDialog = false" style="width:40px; height:40px"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 10px 15px 15px 15px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:10px; margin-bottom:20px;">
                  <v-row>
                    <v-col>
                      <v-autocomplete :loading="loading" text v-model="filter.user" :items="filterUsers" label="User" clearable style="padding-top:0px" hide-details></v-autocomplete>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col>
                      <v-text-field text v-model="filter.server" label="Server" style="padding-top:0px" hide-details></v-text-field>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="8" style="padding-right:5px;">
                      <v-text-field text v-model="filter.database" label="Database" required style="padding-top:0px" hide-details></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-left:5px;">
                      <v-select text v-model="filter.databaseFilter" label="Filter" :items="filters" item-value="id" item-text="name" :rules="[v => ((filter.database === undefined || filter.database.length == 0) || (filter.database.length > 0 && !!v)) || '']" style="padding-top:0px" hide-details></v-select>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="8" style="padding-right:5px;">
                      <v-text-field text v-model="filter.query" label="Query" required style="padding-top:0px" hide-details></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-left:5px;">
                      <v-select text v-model="filter.queryFilter" label="Filter" :items="filters" item-value="id" item-text="name" :rules="[v => ((filter.query === undefined || filter.query.length == 0) || (filter.query.length > 0 && !!v)) || '']" style="padding-top:0px" hide-details></v-select>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col>
                      <v-select v-model="filter.status" :items="[{id: 1, name: 'Success'}, {id: 0, name: 'Failed'}]" item-value="id" item-text="name" label="Status" clearable required style="padding-top:0px" hide-details></v-select>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="6" style="padding-right:8px;">
                      <v-text-field v-model="filter.dateFrom" label="Date From" style="padding-top:0px" hide-details>
                        <template v-slot:append><v-icon @click="dateTimeDialogOpen('from')" small style="margin-top:4px; margin-right:4px">fas fa-calendar-alt</v-icon></template>
                      </v-text-field>
                    </v-col>
                    <v-col cols="6" style="padding-left:8px;">
                      <v-text-field v-model="filter.dateTo" label="Date To" style="padding-top:0px" hide-details>
                        <template v-slot:append><v-icon @click="dateTimeDialogOpen('to')" small style="margin-top:4px; margin-right:4px">fas fa-calendar-alt</v-icon></template>
                      </v-text-field>
                    </v-col>
                  </v-row>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :loading="loading" color="#00b16a" @click="submitFilter">CONFIRM</v-btn>
                  <v-btn :disabled="loading" color="error" @click="filterDialog = false" style="margin-left:5px;">CANCEL</v-btn>
                  <v-btn v-show="filterApplied" :disabled="loading" color="info" @click="clearFilter" style="float:right;">Remove Filter</v-btn>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="dateTimeDialog" persistent width="290px">
      <v-date-picker v-if="dateTimeMode == 'date'" v-model="dateTimeValue.date" color="info" scrollable>
        <v-btn text color="#00b16a" @click="dateTimeSubmit">Confirm</v-btn>
        <v-btn text color="error" @click="dateTimeDialog = false">Cancel</v-btn>
        <v-spacer></v-spacer>
        <v-btn text color="info" @click="dateTimeNow">Now</v-btn>
      </v-date-picker>
      <v-time-picker v-else-if="dateTimeMode == 'time'" v-model="dateTimeValue.time" color="info" format="24hr" use-seconds scrollable>
        <v-btn text color="#00b16a" @click="dateTimeSubmit">Confirm</v-btn>
        <v-btn text color="error" @click="dateTimeDialog = false">Cancel</v-btn>
        <v-spacer></v-spacer>
        <v-btn text color="info" @click="dateTimeNow">Now</v-btn>
      </v-time-picker>
    </v-dialog>

    <!-- Preload -->
    <div v-show="false" id="editor" style="height:50vh; width:100%"></div>

    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<style scoped>
.ace-monokai {
  background-color: #303030;
}
::deep .ace_scroller {
  padding: 13px!important;
}
::deep .ace_scrollbar.ace_scrollbar-v {
  display: none;
}
</style>

<script>
import axios from 'axios'
import moment from 'moment'
import ace from 'ace-builds'
import 'ace-builds/webpack-resolver'
import 'ace-builds/src-noconflict/ext-language_tools'
import sqlFormatter from '@sqltools/formatter'

export default {
  data() {
    return {
      loading: true,
      origin: [],
      items: [],
      headers: [
        { text: 'Date', align: 'left', value: 'date' },
        { text: 'User', align: 'left', value: 'user' },
        { text: 'Server', align: 'left', value: 'server' },
        { text: 'Database', align: 'left', value: 'database' },
        { text: 'Status', align: 'left', value: 'status' },
        { text: 'Query', align: 'left', value: 'query', sortable: false },
      ],
      options: {},
      total: 0,
      search: '',
      editor: null,
      expanded: [],
      // Filter Dialog
      filterDialog: false,
      filters: [
        {id: 'equal', name: 'Equal'},
        {id: 'not_equal', name: 'Not equal'},
        {id: 'starts', name: 'Starts'},
        {id: 'not_starts', name: 'Not starts'},
        {id: 'contains', name: 'Contains'}
      ],
      filter: {},
      filterUsers: [],
      filterApplied: false,
      dateTimeDialog: false,
      dateTimeField: '',
      dateTimeMode: 'date',
      dateTimeValue: { date: null, time: null },
      // Info Dialog
      infoDialog: false,
      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarText: '',
      snackbarColor: ''
    }
  },
  mounted() {
    this.editor = ace.edit("editor", {
      mode: "ace/mode/mysql",
      theme: "ace/theme/monokai",
    })
  },
  watch: {
    options: {
      handler () {
        this.getClient()
      },
      deep: true,
    },
    expanded: function(val) {
      if (val.length == 0) return
      this.$nextTick(() => {
        // Init ACE Editor
        this.editor = ace.edit("editor", {
          mode: "ace/mode/mysql",
          theme: "ace/theme/monokai",
          maxLines: 20,
          fontSize: 14,
          showPrintMargin: false,
          // wrap: false,
          readOnly: true,
          showGutter: false,
        })
        this.editor.commands.removeCommand('showSettingsMenu')
        this.editor.container.addEventListener("keydown", (e) => {
          // - Increase Font Size -
          if (e.key.toLowerCase() == "+" && (e.ctrlKey || e.metaKey)) {
            let size = parseInt(this.editor.getFontSize(), 10) || 12
            this.editor.setFontSize(size + 1)
            e.preventDefault()
          }
          // - Decrease Font Size -
          else if (e.key.toLowerCase() == "-" && (e.ctrlKey || e.metaKey)) {
            let size = parseInt(this.editor.getFontSize(), 10) || 12
            this.editor.setFontSize(Math.max(size - 1 || 1))
            e.preventDefault()
          }
        }, false)
        let sqlFormatted = sqlFormatter.format(this.expanded[0].query, { reservedWordCase: 'upper', linesBetweenQueries: 2 })
        this.editor.setValue(sqlFormatted, -1)
      })
    }
  },
  methods: {
    getClient() {
      this.loading = true
      var payload = {}
      // Build Filter
      let filter = this.filterApplied ? JSON.parse(JSON.stringify(this.filter)) : null
      if (this.filterApplied && 'dateFrom' in filter) filter.dateFrom = moment(this.filter.dateFrom).utc().format("YYYY-MM-DD HH:mm:ss")
      if (this.filterApplied && 'dateTo' in filter) filter.dateTo = moment(this.filter.dateTo).utc().format("YYYY-MM-DD HH:mm:ss")
      if (filter != null) payload['filter'] = filter
      // Build Sort
      const { sortBy, sortDesc } = this.options
      if (sortBy.length > 0) payload['sort'] = { column: sortBy[0], desc: sortDesc[0] }
      // Get Client queries
      axios.get('/admin/client/queries', { params: payload })
        .then((response) => {
          this.items = response.data.queries.map(x => ({...x, date: this.dateFormat(x.date)}))
          // this.items = response.data.queries.map(x => ({...x, query: x.query.length > 512 ? x.query.substring(0,512) + '...' : x.query, date: this.dateFormat(x.date)}))
          this.origin = JSON.parse(JSON.stringify(this.items))
          this.total = this.items.length
          this.filterUsers = response.data.users
          this.onSearch()
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
    },
    refresh() {
      this.getClient()
    },
    onSearch() {
      if (this.search.length == 0) this.items = JSON.parse(JSON.stringify(this.origin))
      else {
        this.items = this.origin.filter(x => {(
          x.date.includes(this.search) ||
          x.user.includes(this.search) ||
          x.server.includes(this.search) ||
          x.database.includes(this.search) ||
          x.query.includes(this.search)
        )})
      }
    },
    dateTimeDialogOpen(field) {
      this.dateTimeField = field
      this.dateTimeMode = 'date'
      this.dateTimeValue = { date: moment().format("YYYY-MM-DD"), time: moment().format("HH:mm") }
      this.dateTimeDialog = true
    },
    dateTimeSubmit() {
      if (this.dateTimeMode == 'date') this.dateTimeMode = 'time'
      else {
        if (this.dateTimeField == 'from') this.filter.dateFrom = this.dateTimeValue.date + ' ' + this.dateTimeValue.time
        else if (this.dateTimeField == 'to') this.filter.dateTo = this.dateTimeValue.date + ' ' + this.dateTimeValue.time
        this.dateTimeDialog = false
      }
    },
    dateTimeNow() {
      this.dateTimeValue = { date: moment().format("YYYY-MM-DD"), time: moment().format("HH:mm") }
    },
    submitFilter() {
      // Check if some filter was applied
      if (!Object.keys(this.filter).some(x => this.filter[x] != null && this.filter[x].length != 0)) {
        this.notification('Enter at least one filter', 'error')
        return
      }
      this.filterDialog = false
      this.filterApplied = true
      this.getClient()
    },
    clearFilter() {
      this.filterDialog = false
      this.filter = {}
      this.filterApplied = false
      this.getClient()
    },
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  }
}
</script>