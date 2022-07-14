<template>
  <div>
    <v-data-table :headers="computedHeaders" :items="items" :options.sync="options" :server-items-length="total" :loading="loading" :expanded.sync="expanded" single-expand item-key="id" show-expand class="elevation-1" mobile-breakpoint="0">
      <template v-slot:[`item.start_date`]="{ item }">
        <span style="display:block; min-width:130px">{{ item.start_date }}</span>
      </template>
      <template v-slot:[`item.end_date`]="{ item }">
        <span style="display:block; min-width:130px">{{ item.end_date }}</span>
      </template>
      <template v-slot:[`item.user`]="{ item }">
        <span style="display:block; min-width:44px">{{ item.user }}</span>
      </template>
      <template v-slot:[`item.server`]="{ item }">
        <v-btn @click="getServer(item.server_id)" text class="body-2" style="text-transform:inherit; padding:0 5px; margin-left:-5px">
          <v-icon small :title="item.shared ? item.secured ? 'Shared (Secured)' : 'Shared' : item.secured ? 'Personal (Secured)' : 'Personal'" :color="item.shared ? '#EB5F5D' : 'warning'" :style="`margin-bottom:2px; ${!item.secured ? 'padding-right:8px' : ''}`">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
          <v-icon v-if="item.secured" :title="item.shared ? 'Shared (Secured)' : 'Personal (Secured)'" :color="item.shared ? '#EB5F5D' : 'warning'" style="font-size:12px; padding-left:2px; padding-top:2px; padding-right:8px">fas fa-lock</v-icon>
          {{ item.server }}
        </v-btn>
      </template>
      <template v-slot:[`item.database`]="{ item }">
        <span style="display:block; min-width:70px">{{ item.database }}</span>
      </template>
      <template v-slot:[`item.status`]="{ item }">
        <span :style="`display:block; min-width:78px; color:${item.status == 'SUCCESS' ? '#00b16a' : item.status == 'RUNNING' ? '#fa8131' : '#EF5354' };`">
          <v-icon small :title="item.status.charAt(0).toUpperCase() + item.status.slice(1).toLowerCase()" :style="`color:${item.status == 'SUCCESS' ? '#00b16a' : item.status == 'RUNNING' ? '#fa8131' : '#EF5354' }; margin-right:5px; margin-bottom:2px`">{{ item.status == 'SUCCESS' ? 'fas fa-check-circle' : item.status == 'FAILED' ? 'fas fa-times-circle' : item.status == 'STOPPED' ? 'fas fa-exclamation-circle' : 'fas fa-spinner' }}</v-icon>
          {{ item.status.charAt(0).toUpperCase() + item.status.slice(1).toLowerCase() }}
        </span>
      </template>
      <template v-slot:[`item.query`]="{ item }">
        <span style="white-space:nowrap">{{ item.query }}</span>
      </template>
      <template v-slot:expanded-item="{ headers, item }">
        <td :colspan="headers.length">
          <div v-if="item.records != null && item.error == null" style="margin-top:10px">
            Records:
            <span style="margin-left:6px">{{ item.records }}</span>
          </div>
          <div v-if="item.elapsed != null && item.error == null" style="margin-top:2px">
            Elapsed:
            <span style="margin-left:8px">{{ item.elapsed + 's' }}</span>
          </div>
          <div v-if="item.error != null" style="margin-top:10px">
            Error:
            <span style="margin-left:5px">{{ item.error }}</span>
          </div>
          <div id="editor" style="width:calc(100vw - 70px); margin-top:10px; margin-bottom:15px"></div>
        </td>
      </template>
    </v-data-table>
    <!------------------->
    <!-- FILTER DIALOG -->
    <!------------------->
    <v-dialog v-model="filterDialog" max-width="50%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:3px">fas fa-sliders-h</v-icon>FILTER</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="filterDialog = false" style="width:40px; height:40px"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:10px; margin-bottom:20px;">
                  <v-row>
                    <v-col>
                      <v-autocomplete :loading="loading" text v-model="filter.user" :items="filterUsers" item-value="user" item-text="user" label="User" clearable style="padding-top:0px" hide-details>
                        <template v-slot:item="{ item }" >
                          <v-row no-gutters align="center">
                            <v-col class="flex-grow-1 flex-shrink-1">
                              {{ item.user }}
                            </v-col>
                            <v-col cols="auto" class="flex-grow-0 flex-shrink-0">
                              <v-chip label>{{ item.group }}</v-chip>
                            </v-col>
                          </v-row>
                        </template>
                      </v-autocomplete>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col>
                      <v-autocomplete :loading="loading" text v-model="filter.server" :items="filterServers" label="Server" clearable style="padding-top:0px" hide-details></v-autocomplete>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="8" style="padding-right:5px;">
                      <v-text-field text v-model="filter.database" label="Database" required style="padding-top:0px" hide-details></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-left:5px;">
                      <v-select text v-model="filter.databaseFilter" label="Filter" :items="filters" item-value="id" item-text="name" :rules="[v => ((filter.database === undefined || filter.database.length == 0) || (filter.database.length > 0 && !!v)) || '']" clearable style="padding-top:0px" hide-details></v-select>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="8" style="padding-right:5px;">
                      <v-text-field text v-model="filter.query" label="Query" required style="padding-top:0px" hide-details></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-left:5px;">
                      <v-select text v-model="filter.queryFilter" label="Filter" :items="filters" item-value="id" item-text="name" :rules="[v => ((filter.query === undefined || filter.query.length == 0) || (filter.query.length > 0 && !!v)) || '']" clearable style="padding-top:0px" hide-details></v-select>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col>
                      <v-select v-model="filter.status" :items="[{id: 1, name: 'Success'}, {id: 0, name: 'Failed'}]" item-value="id" item-text="name" label="Status" clearable required style="padding-top:0px" hide-details></v-select>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="6" style="padding-right:8px;">
                      <v-text-field v-model="filter.startDateFrom" label="Start Date - From" style="padding-top:0px" hide-details>
                        <template v-slot:append><v-icon @click="dateTimeDialogOpen('startDateFrom')" small style="margin-top:4px; margin-right:4px">fas fa-calendar-alt</v-icon></template>
                      </v-text-field>
                    </v-col>
                    <v-col cols="6" style="padding-left:8px;">
                      <v-text-field v-model="filter.startDateTo" label="Start Date - To" style="padding-top:0px" hide-details>
                        <template v-slot:append><v-icon @click="dateTimeDialogOpen('startDateTo')" small style="margin-top:4px; margin-right:4px">fas fa-calendar-alt</v-icon></template>
                      </v-text-field>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="6" style="padding-right:8px;">
                      <v-text-field v-model="filter.endDateFrom" label="End Date - From" style="padding-top:0px" hide-details>
                        <template v-slot:append><v-icon @click="dateTimeDialogOpen('endDateFrom')" small style="margin-top:4px; margin-right:4px">fas fa-calendar-alt</v-icon></template>
                      </v-text-field>
                    </v-col>
                    <v-col cols="6" style="padding-left:8px;">
                      <v-text-field v-model="filter.endDateTo" label="End Date - To" style="padding-top:0px" hide-details>
                        <template v-slot:append><v-icon @click="dateTimeDialogOpen('endDateTo')" small style="margin-top:4px; margin-right:4px">fas fa-calendar-alt</v-icon></template>
                      </v-text-field>
                    </v-col>
                  </v-row>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :loading="loading" color="#00b16a" @click="submitFilter">CONFIRM</v-btn>
                  <v-btn :disabled="loading" color="#EF5354" @click="filterDialog = false" style="margin-left:5px;">CANCEL</v-btn>
                  <v-btn v-show="filterApplied" :disabled="loading" color="info" @click="clearFilter" style="float:right;">Remove Filter</v-btn>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!-------------------->
    <!-- COLUMNS DIALOG -->
    <!-------------------->
    <v-dialog v-model="columnsDialog" max-width="600px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="text-subtitle-1 white--text">FILTER COLUMNS</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn @click="selectAllColumns" text title="Select all columns" style="height:100%"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-check-square</v-icon>Select all</v-btn>
          <v-btn @click="deselectAllColumns" text title="Deselect all columns" style="height:100%"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-square</v-icon>Deselect all</v-btn>
          <v-spacer></v-spacer>
          <v-btn icon @click="columnsDialog = false" style="width:40px; height:40px"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 0px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:15px; margin-bottom:20px;">
                  <div class="text-body-1" style="margin-bottom:10px">Select the columns to display:</div>
                  <v-checkbox v-model="columnsRaw" label="Start Date" value="start_date" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="End Date" value="end_date" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="User" value="user" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Server" value="server" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Database" value="database" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Status" value="status" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Elapsed" value="elapsed" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Records" value="records" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Query" value="query" hide-details style="margin-top:5px"></v-checkbox>
                  <v-divider style="margin-top:15px;"></v-divider>
                  <div style="margin-top:20px;">
                    <v-btn @click="filterColumns" :loading="loading" color="#00b16a">Confirm</v-btn>
                    <v-btn :disabled="loading" color="#EF5354" @click="columnsDialog = false" style="margin-left:5px;">Cancel</v-btn>
                  </div>
                </v-form>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="dateTimeDialog" persistent width="290px">
      <v-date-picker v-if="dateTimeMode == 'date'" v-model="dateTimeValue.date" color="info" scrollable>
        <v-btn text color="#00b16a" @click="dateTimeSubmit">Confirm</v-btn>
        <v-btn text color="#EF5354" @click="dateTimeDialog = false">Cancel</v-btn>
        <v-spacer></v-spacer>
        <v-btn text color="info" @click="dateTimeNow">Now</v-btn>
      </v-date-picker>
      <v-time-picker v-else-if="dateTimeMode == 'time'" v-model="dateTimeValue.time" color="info" format="24hr" use-seconds scrollable>
        <v-btn text color="#00b16a" @click="dateTimeSubmit">Confirm</v-btn>
        <v-btn text color="#EF5354" @click="dateTimeDialog = false">Cancel</v-btn>
        <v-spacer></v-spacer>
        <v-btn text color="info" @click="dateTimeNow">Now</v-btn>
      </v-time-picker>
    </v-dialog>

    <!-- Preload -->
    <div v-show="false" id="editor" style="height:50vh; width:100%"></div>
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
import EventBus from '../../js/event-bus'

export default {
  data() {
    return {
      loading: true,
      origin: [],
      items: [],
      headers: [
        { text: 'Start Date', align: 'left', value: 'start_date' },
        { text: 'End Date', align: 'left', value: 'end_date' },
        { text: 'User', align: 'left', value: 'user' },
        { text: 'Server', align: 'left', value: 'server' },
        { text: 'Database', align: 'left', value: 'database' },
        { text: 'Status', align: 'left', value: 'status' },
        { text: 'Elapsed', align: 'left', value: 'elapsed' },
        { text: 'Records', align: 'left', value: 'records' },
        { text: 'Query', align: 'left', value: 'query', sortable: false },
      ],
      options: null,
      total: 0,
      editor: null,
      expanded: [],
      // Filter Dialog
      filterDialog: false,
      filters: [
        {id: 'equal', name: 'Equal'},
        {id: 'not_equal', name: 'Not equal'},
        {id: 'starts', name: 'Starts'},
        {id: 'not_starts', name: 'Not starts'},
        {id: 'contains', name: 'Contains'},
        {id: 'not_contains', name: 'Not contains'}
      ],
      filter: {},
      filterUsers: [],
      filterServers: [],
      filterApplied: false,
      dateTimeDialog: false,
      dateTimeField: '',
      dateTimeMode: 'date',
      dateTimeValue: { date: null, time: null },
      // Filter Columns Dialog
      columnsDialog: false,
      columns: ['start_date','user','server','database','status','query'],
      columnsRaw: [],
    }
  },
  props: ['active','search'],
  mounted() {
    EventBus.$on('filter-client-queries', () => { this.filterDialog = true })
    EventBus.$on('filter-client-columns', this.filterQueriesColumns)
    EventBus.$on('refresh-client-queries', this.getQueries)
    this.editor = ace.edit("editor", {
      mode: "ace/mode/mysql",
      theme: "ace/theme/monokai",
      keyboardHandler: "ace/keyboard/vscode",
    })
  },
  computed: {
    computedHeaders() { return this.headers.filter(x => this.columns.includes(x.value)) },
  },
  watch: {
    options: {
      handler (newValue, oldValue) {
        if (oldValue == null || (oldValue.page == newValue.page && oldValue.itemsPerPage == newValue.itemsPerPage)) {
          this.getQueries()
        }
        else this.onSearch()
      },
      deep: true,
    },
    active: function(newVal) {
      if (newVal) this.onSearch()
    },
    search: function() {
      if (this.active) this.onSearch()
    },
    expanded: function(val) {
      if (val.length == 0) return
      this.$nextTick(() => {
        // Init ACE Editor
        this.editor = ace.edit("editor", {
          mode: "ace/mode/mysql",
          theme: "ace/theme/monokai",
          keyboardHandler: "ace/keyboard/vscode",
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
    getQueries() {
      this.loading = true
      var payload = {}
      // Build Filter
      let filter = this.filterApplied ? JSON.parse(JSON.stringify(this.filter)) : null
      if (this.filterApplied && 'startDateFrom' in filter) filter.startDateFrom = moment(this.filter.startDateFrom).utc().format("YYYY-MM-DD HH:mm:ss")
      if (this.filterApplied && 'startDateTo' in filter) filter.startDateTo = moment(this.filter.startDateTo).utc().format("YYYY-MM-DD HH:mm:ss")
      if (this.filterApplied && 'endDateFrom' in filter) filter.endDateFrom = moment(this.filter.endDateFrom).utc().format("YYYY-MM-DD HH:mm:ss")
      if (this.filterApplied && 'endDateTo' in filter) filter.endDateTo = moment(this.filter.endDateTo).utc().format("YYYY-MM-DD HH:mm:ss")
      if (filter != null) payload['filter'] = filter
      // Build Sort
      const { sortBy, sortDesc } = this.options
      if (sortBy.length > 0) payload['sort'] = { column: sortBy[0], desc: sortDesc[0] }
      // Get Client queries
      axios.get('/admin/client/queries', { params: payload })
        .then((response) => {
          this.origin = response.data.queries.map(x => ({...x, start_date: this.dateFormat(x.start_date), end_date: this.dateFormat(x.end_date)}))
          this.filterUsers = response.data.users_list
          this.filterServers = response.data.servers_list
          this.onSearch()
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    getServer(server_id) {
      EventBus.$emit('client-get-server', server_id)
    },
    onSearch() {
      const { page, itemsPerPage } = this.options
      const itemStart = (page-1) * itemsPerPage
      const itemEnd = (page-1) * itemsPerPage + itemsPerPage
      if (this.search.length == 0) {
        this.items = this.origin.slice(itemStart, itemEnd)
        this.total = this.origin.length
      }
      else {
        const items = this.origin.filter(x =>
          x.start_date.includes(this.search) ||
          x.end_date.includes(this.search) ||
          x.user.toLowerCase().includes(this.search.toLowerCase()) ||
          x.server.toLowerCase().includes(this.search.toLowerCase()) ||
          (x.database != null && x.database.toLowerCase().includes(this.search.toLowerCase())) ||
          x.query.toLowerCase().includes(this.search.toLowerCase())
        )
        this.total = items.length
        this.items = items.slice(itemStart, itemEnd)
      }
    },
    dateTimeDialogOpen(field) {
      this.dateTimeField = field
      this.dateTimeMode = 'date'
      this.dateTimeValue = { date: moment().format("YYYY-MM-DD"), time: moment().format("HH:mm") }
      if (this.dateTimeField == 'startDateFrom' && this.filter.startDateFrom !== undefined && this.filter.startDateFrom.length > 0) {
        let isValid = moment(this.filter.startDateFrom, 'YYYY-MM-DD HH:mm', true).isValid()
        if (!isValid) {
          this.notification("Enter a valid date", '#EF5354')
          return
        }
        this.dateTimeValue = { date: moment(this.filter.startDateFrom).format("YYYY-MM-DD"), time: moment(this.filter.startDateFrom).format("HH:mm") }
      }
      else if (this.dateTimeField == 'startDateTo' && this.filter.startDateTo !== undefined && this.filter.startDateTo.length > 0) {
        let isValid = moment(this.filter.startDateTo, 'YYYY-MM-DD HH:mm', true).isValid()
        if (!isValid) {
          this.notification("Enter a valid date", '#EF5354')
          return
        }
        this.dateTimeValue = { date: moment(this.filter.startDateTo).format("YYYY-MM-DD"), time: moment(this.filter.startDateTo).format("HH:mm") }
      }
      else if (this.dateTimeField == 'endDateFrom' && this.filter.endDateFrom !== undefined && this.filter.endDateFrom.length > 0) {
        let isValid = moment(this.filter.endDateFrom, 'YYYY-MM-DD HH:mm', true).isValid()
        if (!isValid) {
          this.notification("Enter a valid date", '#EF5354')
          return
        }
        this.dateTimeValue = { date: moment(this.filter.endDateFrom).format("YYYY-MM-DD"), time: moment(this.filter.endDateFrom).format("HH:mm") }
      }
      else if (this.dateTimeField == 'endDateTo' && this.filter.endDateTo !== undefined && this.filter.endDateTo.length > 0) {
        let isValid = moment(this.filter.endDateTo, 'YYYY-MM-DD HH:mm', true).isValid()
        if (!isValid) {
          this.notification("Enter a valid date", '#EF5354')
          return
        }
        this.dateTimeValue = { date: moment(this.filter.endDateTo).format("YYYY-MM-DD"), time: moment(this.filter.endDateTo).format("HH:mm") }
      }
      this.dateTimeDialog = true
    },
    dateTimeSubmit() {
      console.log(this.dateTimeField)
      if (this.dateTimeMode == 'date') this.dateTimeMode = 'time'
      else {
        if (this.dateTimeField == 'startDateFrom') this.filter.startDateFrom = this.dateTimeValue.date + ' ' + this.dateTimeValue.time
        else if (this.dateTimeField == 'startDateTo') this.filter.startDateTo = this.dateTimeValue.date + ' ' + this.dateTimeValue.time
        else if (this.dateTimeField == 'endDateFrom') this.filter.endDateFrom = this.dateTimeValue.date + ' ' + this.dateTimeValue.time
        else if (this.dateTimeField == 'endDateTo') this.filter.endDateTo = this.dateTimeValue.date + ' ' + this.dateTimeValue.time
        this.dateTimeDialog = false
      }
    },
    dateTimeNow() {
      this.dateTimeValue = { date: moment().format("YYYY-MM-DD"), time: moment().format("HH:mm") }
    },
    submitFilter() {
      // Check if all necessary fields are filled
      if (!this.$refs.form.validate()) {
        EventBus.$emit('send-notification', 'Please make sure all required fields are filled out correctly', '#EF5354')
        return
      }
      // Check if some filter was applied
      if (!Object.keys(this.filter).some(x => this.filter[x] != null && this.filter[x].length != 0)) {
        EventBus.$emit('send-notification', 'Enter at least one filter.', '#EF5354')
        return
      }
      this.filterDialog = false
      EventBus.$emit('client-toggle-filter', { from: 'queries', value: true })
      this.filterApplied = true
      this.getQueries()
    },
    clearFilter() {
      this.filterDialog = false
      this.filter = {}
      EventBus.$emit('client-toggle-filter', { from: 'queries', value: false })
      this.filterApplied = false
      this.getQueries()
    },
    filterQueriesColumns() {
      this.columnsRaw = [...this.columns]
      this.columnsDialog = true
    },
    selectAllColumns() {
      this.columnsRaw = ['start_date','end_date','user','server','database','status','elapsed','records','query']
    },
    deselectAllColumns() {
      this.columnsRaw = []
    },
    filterColumns() {
      this.columns = [...this.columnsRaw]
      this.columnsDialog = false
    },
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
  }
}
</script>