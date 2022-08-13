<template>
  <div>
    <v-card>
      <v-data-table v-model="selected" :headers="computedHeaders" :items="items" :options.sync="options" :server-items-length="total" :sort-by.sync="sortBy" :sort-desc.sync="sortDesc" :loading="loading" loading-text="Loading... Please wait" item-key="id" show-select class="elevation-1" style="padding-top:5px;" mobile-breakpoint="0">
        <template v-ripple v-slot:[`header.data-table-select`]="{}">
          <v-simple-checkbox
            :value="items.length == 0 ? false : selected.length == items.length"
            :indeterminate="selected.length > 0 && selected.length != items.length"
            @click="selected.length == items.length ? selected = [] : selected = [...items]">
          </v-simple-checkbox>
        </template>
        <template v-slot:[`item.mode`]="{ item }">
          <div v-if="item.mode == 'full'">
            <v-icon small color="#EF5354" style="margin-right:5px; margin-bottom:4px">fas fa-star</v-icon>
            Full
          </div>
          <div v-else-if="item.mode == 'partial'">
            <v-icon small color="#ff9800" style="margin-right:5px; margin-bottom:4px">fas fa-star-half</v-icon>
            Partial
          </div>
        </template>
        <template v-slot:[`item.server_id`]="{ item }">
          <v-btn @click="getServer(item.server_id)" text class="text-body-2" style="text-transform:inherit; padding:0 5px; margin-left:-5px">
            <v-icon small :title="item.server_shared ? item.server_secured ? 'Shared (Secured)' : 'Shared' : item.server_secured ? 'Personal (Secured)' : 'Personal'" :color="item.server_shared ? '#EB5F5D' : 'warning'" :style="`margin-bottom:2px; ${!item.server_secured ? 'padding-right:8px' : ''}`">{{ item.server_shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
            <v-icon v-if="item.server_secured" :title="item.server_shared ? 'Shared (Secured)' : 'Personal (Secured)'" :color="item.server_shared ? '#EB5F5D' : 'warning'" style="font-size:12px; padding-left:2px; padding-top:2px; padding-right:8px">fas fa-lock</v-icon>
            {{ item.server_name }}
          </v-btn>
        </template>
        <template v-slot:[`item.size`]="{ item }">
          {{ formatBytes(item.size) }}
        </template>
        <template v-slot:[`item.status`]="{ item }">
          <v-icon v-if="item.status == 'QUEUED'" :title="`Queued: ${item.queue}`" small style="color: #3498db; margin-left:8px;">fas fa-clock</v-icon>
          <v-icon v-else-if="item.status == 'STARTING'" title="Starting" small style="color: #3498db; margin-left:8px;">fas fa-spinner</v-icon>
          <v-icon v-else-if="item.status == 'IN PROGRESS'" title="In Progress" small style="color: #ff9800; margin-left:8px;">fas fa-spinner</v-icon>
          <v-icon v-else-if="item.status == 'SUCCESS'" title="Success" small style="color: #4caf50; margin-left:9px;">fas fa-check</v-icon>
          <v-icon v-else-if="item.status == 'FAILED'" title="Failed" small style="color: #EF5354; margin-left:11px;">fas fa-times</v-icon>
          <v-icon v-else-if="item.status == 'STOPPING'" title="Stopping" small style="color: #ff9800; margin-left:8px;">fas fa-ban</v-icon>
          <v-icon v-else-if="item.status == 'STOPPED'" title="Stopped" small style="color: #EF5354; margin-left:8px;">fas fa-ban</v-icon>
        </template>
        <template v-slot:[`item.deleted`]="{ item }">
          <div :style="`margin-left:${item.deleted ? '8px' : '10px'}; font-weight:500; color: ${item.deleted ? '#EF5354' : '#00b16a'}`">{{ item.deleted ? 'YES' : 'NO'}}</div>
        </template>
      </v-data-table>
    </v-card>
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
                  <v-checkbox v-model="columnsRaw" label="Mode" value="mode" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Server" value="server_id" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Database" value="database" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Size" value="size" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Status" value="status" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Created" value="created" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Started" value="started" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Ended" value="ended" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Overall" value="overall" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Deleted" value="deleted" hide-details style="margin-top:5px"></v-checkbox>
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
    <!------------------->
    <!-- MANAGE DIALOG -->
    <!------------------->
    <v-dialog v-model="manageDialog" max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-mouse-pointer</v-icon>MANAGE</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" icon @click="manageDialog = false"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <div class="subtitle-1" style="margin-bottom:10px">Choose the action to perform for the selected exports.</div>
                <v-radio-group v-model="manageOption" hide-details style="margin-top:0px; margin-bottom:20px">
                  <v-radio value="recover" color="#4caf50">
                    <template v-slot:label>
                      <div style="margin-left:5px">
                        <div class="body-1 white--text">Recover</div>
                        <div class="font-weight-regular caption" style="font-size:0.85rem !important">Recover the export making it visible.</div>
                      </div>
                    </template>
                  </v-radio>
                  <v-radio value="delete" color="#ff9800">
                    <template v-slot:label>
                      <div style="margin-left:5px">
                        <div class="body-1 white--text">Delete</div>
                        <div class="font-weight-regular caption" style="font-size:0.85rem !important">Delete the export making it not visible.</div>
                      </div>
                    </template>
                  </v-radio>
                  <v-radio value="permanently" color="#EF5354">
                    <template v-slot:label>
                      <div style="margin-left:5px">
                        <div class="body-1 white--text">Delete Permanently</div>
                        <div class="font-weight-regular caption" style="font-size:0.85rem !important">Delete the export permanently. This action cannot be undone.</div>
                      </div>
                    </template>
                  </v-radio>
                </v-radio-group>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :disabled="loading" color="#00b16a" @click="manageSubmit()">Confirm</v-btn>
                  <v-btn :disabled="loading" color="#EF5354" @click="manageDialog = false" style="margin-left:5px;">Cancel</v-btn>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <!--------------------->
    <!-- DATETIME DIALOG -->
    <!--------------------->
    <v-dialog v-model="dateTimeDialog" persistent width="290px">
      <v-date-picker v-if="dateTimeMode == 'date'" v-model="dateTimeValue.date" color="info" scrollable>
        <v-btn text color="#00b16a" @click="dateTimeSubmit">Confirm</v-btn>
        <v-btn text color="#EF5354" @click="dateTimeDialog = false">Cancel</v-btn>
        <v-spacer></v-spacer>
        <v-btn text color="info" @click="dateTimeNow">Now</v-btn>
      </v-date-picker>
      <v-time-picker v-else-if="dateTimeMode == 'time'" v-model="dateTimeValue.time" color="info" format="24hr" scrollable>
        <v-btn text color="#00b16a" @click="dateTimeSubmit">Confirm</v-btn>
        <v-btn text color="#EF5354" @click="dateTimeDialog = false">Cancel</v-btn>
        <v-spacer></v-spacer>
        <v-btn text color="info" @click="dateTimeNow">Now</v-btn>
      </v-time-picker>
    </v-dialog>
    <!------------------->
    <!-- FILTER DIALOG -->
    <!------------------->
    <v-dialog v-model="filterDialog" persistent max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text text-subtitle-1"><v-icon small style="padding-right:10px; padding-bottom:1px">fas fa-sliders-h</v-icon>FILTER</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="filterDialog = false" style="width:40px; height:40px"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
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
                      <v-autocomplete v-model="filter.mode" :items="exportMode" multiple label="Mode" style="padding-top:0px;" hide-details>
                        <template v-slot:item="{ item }">
                          <div v-if="item == 'full'"><v-icon small color="#EF5354" style="margin-left:5px; margin-right:18px">fas fa-star</v-icon>Full</div>
                          <div v-else-if="item == 'partial'"><v-icon small color="#ff9800" style="margin-left:5px; margin-right:18px">fas fa-star-half</v-icon>Partial</div>
                        </template>
                        <template v-slot:selection="{ item }">
                          <v-chip v-if="item == 'full'" label>
                            <v-icon small color="#EF5354" style="margin-right:10px">fas fa-star</v-icon>
                            Full
                          </v-chip>
                          <v-chip v-else-if="item == 'partial'" label>
                            <v-icon small color="#ff9800" style="margin-right:10px">fas fa-star-half</v-icon>
                            Partial
                          </v-chip>
                        </template>
                      </v-autocomplete>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col>
                      <v-autocomplete v-model="filter.status" :items="exportStatus" multiple label="Status" style="padding-top:0px;" hide-details>
                        <template v-slot:item="{ item }">
                          <v-icon small :style="`color:${getStatusColor(item)}; margin-left:${getStatusIcon(item).margin}; margin-right:${getStatusIcon(item).margin}`">{{ getStatusIcon(item).name }}</v-icon>
                          <span :style="`margin-left:10px; color:${getStatusColor(item)}`">{{ item }}</span>
                        </template>
                        <template v-slot:selection="{ item }">
                          <v-chip label>
                            <v-icon small :style="`color:${getStatusColor(item)}`">{{ getStatusIcon(item).name }}</v-icon>
                            <span :style="`margin-left:10px; color:${getStatusColor(item)}`">{{ item }}</span>
                          </v-chip>
                        </template>
                      </v-autocomplete>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="8" style="padding-right:5px;">
                      <v-text-field v-model="filter.server" label="Server" style="padding-top:0px" hide-details></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-left:5px;">
                      <v-select text v-model="filter.serverFilter" label="Filter" :items="filters" item-value="id" item-text="name" :rules="[v => ((filter.name === undefined || filter.name.length == 0) || (filter.name.length > 0 && !!v)) || '']" clearable style="padding-top:0px" hide-details></v-select>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="8" style="padding-right:5px;">
                      <v-text-field v-model="filter.database" label="Database" style="padding-top:0px" hide-details></v-text-field>
                    </v-col>
                    <v-col cols="4" style="padding-left:5px;">
                      <v-select text v-model="filter.databaseFilter" label="Filter" :items="filters" item-value="id" item-text="name" :rules="[v => ((filter.name === undefined || filter.name.length == 0) || (filter.name.length > 0 && !!v)) || '']" clearable style="padding-top:0px" hide-details></v-select>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="6" style="padding-right:8px;">
                      <v-text-field v-model="filter.createdFrom" label="Created - From" style="padding-top:0px" hide-details>
                        <template v-slot:append><v-icon @click="dateTimeDialogOpen('createdFrom')" small style="margin-top:4px; margin-right:4px">fas fa-calendar-alt</v-icon></template>
                      </v-text-field>
                    </v-col>
                    <v-col cols="6" style="padding-left:8px;">
                      <v-text-field v-model="filter.createdTo" label="Created - To" style="padding-top:0px" hide-details>
                        <template v-slot:append><v-icon @click="dateTimeDialogOpen('createdTo')" small style="margin-top:4px; margin-right:4px">fas fa-calendar-alt</v-icon></template>
                      </v-text-field>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="6" style="padding-right:8px;">
                      <v-text-field v-model="filter.startedFrom" label="Started - From" style="padding-top:0px" hide-details>
                        <template v-slot:append><v-icon @click="dateTimeDialogOpen('startedFrom')" small style="margin-top:4px; margin-right:4px">fas fa-calendar-alt</v-icon></template>
                      </v-text-field>
                    </v-col>
                    <v-col cols="6" style="padding-left:8px;">
                      <v-text-field v-model="filter.startedTo" label="Started - To" style="padding-top:0px" hide-details>
                        <template v-slot:append><v-icon @click="dateTimeDialogOpen('startedTo')" small style="margin-top:4px; margin-right:4px">fas fa-calendar-alt</v-icon></template>
                      </v-text-field>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="6" style="padding-right:8px;">
                      <v-text-field v-model="filter.endedFrom" label="Ended - From" style="padding-top:0px" hide-details>
                        <template v-slot:append><v-icon @click="dateTimeDialogOpen('endedFrom')" small style="margin-top:4px; margin-right:4px">fas fa-calendar-alt</v-icon></template>
                      </v-text-field>
                    </v-col>
                    <v-col cols="6" style="padding-left:8px;">
                      <v-text-field v-model="filter.endedTo" label="Ended - To" style="padding-top:0px" hide-details>
                        <template v-slot:append><v-icon @click="dateTimeDialogOpen('endedTo')" small style="margin-top:4px; margin-right:4px">fas fa-calendar-alt</v-icon></template>
                      </v-text-field>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col>
                      <v-checkbox v-model="filter.deleted" label="Include Deleted Exports" style="margin-top:0px" hide-details></v-checkbox>
                    </v-col>
                  </v-row>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:20px;">
                  <v-btn :loading="loading" color="#00b16a" @click="submitFilter">Confirm</v-btn>
                  <v-btn :disabled="loading" color="#EF5354" @click="filterDialog = false" style="margin-left:5px;">Cancel</v-btn>
                  <v-btn v-if="filterApplied" :disabled="loading" color="info" @click="clearFilter" style="float:right;">Remove Filter</v-btn>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import axios from 'axios';
import moment from 'moment';
import pretty from 'pretty-bytes';
import EventBus from '../../js/event-bus'

export default {
  data: () => ({
    headers: [
      { text: 'User', align: 'left', value: 'username' },
      { text: 'Mode', align: 'left', value: 'mode' },
      { text: 'Server', align: 'left', value: 'server_id' },
      { text: 'Database', align: 'left', value: 'database' },
      { text: 'Size', align: 'left', value: 'size' },
      { text: 'Status', align:'left', value: 'status' },
      { text: 'Created', align: 'left', value: 'created' },
      { text: 'Started', align: 'left', value: 'started' },
      { text: 'Ended', align: 'left', value: 'ended' },
      { text: 'Overall', align: 'left', value: 'overall' },
      { text: 'Deleted', align: 'left', value: 'deleted' },
    ],
    origin: [],
    items: [],
    total: 0,
    selected: [],
    options: null,
    firstLoad: true,
    sortBy: null,
    sortDesc: null,
    loading: false,

    // Manage Dialog
    manageDialog: false,
    manageOption: 'recover',

    // Filter Dialog
    filterDialog: false,
    filters: [
      {id: 'equal', name: 'Equal'},
      {id: 'not_equal', name: 'Not equal'},
      {id: 'starts', name: 'Starts'},
      {id: 'not_starts', name: 'Not starts'},
      {id: 'contains', name: 'Contains'},
      {id: 'not_contains', name: 'Not contains'},
    ],
    filterOrigin: {},
    filter: {},
    filterApplied: false,
    filterUsers: [],
    exportMode: ['full','partial'],
    exportStatus: ['IN PROGRESS','SUCCESS','FAILED','STOPPED'],

    // Date / Time Picker
    dateTimeDialog: false,
    dateTimeField: '',
    dateTimeMode: 'date',
    dateTimeValue: { date: null, time: null },

    // Filter Columns Dialog
    columnsDialog: false,
    columns: ['username','mode','server_id','database','status','created','started','ended','overall'],
    columnsRaw: [],
  }),
  props: ['active','search'],
  watch: {
    options: {
      handler (newValue, oldValue) {
        if (oldValue == null || (!this.firstLoad && oldValue.page == newValue.page && oldValue.itemsPerPage == newValue.itemsPerPage)) {
          this.getExport()
        }
        else this.onSearch()
      },
      deep: true,
    },
    search: function() {
      if (this.active) this.onSearch()
    },
    selected(val) { 
      EventBus.$emit('utils-select-row', { from: 'export', value: val.length })
    }
  },
  computed: {
    computedHeaders() { return this.headers.filter(x => this.columns.includes(x.value)) },
  },
  mounted() {
    EventBus.$on('info-utils-export', this.infoExport)
    EventBus.$on('manage-utils-export', this.manageExport)
    EventBus.$on('filter-utils-export', () => { this.filterDialog = true })
    EventBus.$on('refresh-utils-export', this.getExport)
    EventBus.$on('columns-utils-export', this.openColumnsDialog)
  },
  destroyed() {
    EventBus.$off()
  },
  methods: {
    getExport() {
      var payload = {}
      // Build Filter
      let filterKeys = Object.keys(this.$route.query).filter(x => !(['sortBy','sortDesc'].includes(x)))
      if (!this.filterApplied && filterKeys.length != 0) {
        this.filter = filterKeys.reduce((acc, val) => {
          if (['mode','status'].includes(val) && typeof this.$route.query[val] == 'string') acc[val] = [this.$route.query[val]]
          else acc[val] = this.$route.query[val]
          return acc
        },{})
        this.filterApplied = true
      }
      if (this.filterApplied) {
        this.filterOrigin = JSON.parse(JSON.stringify(this.filter))
        payload['filter'] = Object.keys(this.filter).reduce((acc, val) => {
          if (['createdFrom','createdTo','startedFrom','startedTo','endedFrom','endedTo'].includes(val)) acc[val] = moment(this.filter[val]).utc().format("YYYY-MM-DD HH:mm:ss")
          else acc[val] = this.filter[val]
          return acc
        },{})
      }
      // Build Sort
      const { sortBy, sortDesc } = this.options
      if (sortBy.length > 0) {
        payload['sort'] = { column: sortBy[0], desc: sortDesc[0] === undefined ? false : sortDesc[0] }
      }
      else if (this.firstLoad && 'sortBy' in this.$route.query && 'sortDesc' in this.$route.query) {
        this.sortBy = this.$route.query['sortBy']
        this.sortDesc = this.$route.query['sortDesc'] == 'true'
        payload['sort'] = { column: this.sortBy, desc: this.sortDesc }
      }
      // Build URL Params
      let query = {}
      if ('filter' in payload) query = {...payload['filter']}
      if ('sort' in payload) query = {...query, sortBy: payload['sort']['column'], sortDesc: payload['sort']['desc']}
      let routeQuery = ('sortDesc' in this.$route.query) ? {...this.$route.query, "sortDesc": this.$route.query['sortDesc'] == 'true'} : this.$route.query
      if (JSON.stringify(routeQuery) != JSON.stringify(query)) this.$router.replace({query: query})
      // Get Exports
      this.loading = true
      axios.get('/admin/utils/exports', { params: payload })
        .then((response) => {
          this.origin = response.data.exports.map(x => ({...x, created: this.dateFormat(x.created), started: this.dateFormat(x.started), ended: this.dateFormat(x.ended)}))
          this.filterUsers = response.data.users_list
          this.onSearch()
          this.firstLoad = false
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    manageExport() {
      this.manageOption = 'recover'
      this.manageDialog = true
    },
    manageSubmit() {
      // Check export status
      if (['delete','permanently'].includes(this.manageOption) && this.selected.some(x => x.status == 'IN PROGRESS')) {
        EventBus.$emit('send-notification', "Can't delete exports that are in progress", '#EF5354')
        this.deleteDialog = false
        return
      }
      // Delete Exports
      this.loading = true
      const payload = { 
        action: this.manageOption,
        items: this.selected.map(x => x.id)
      }
      axios.post('/admin/utils/exports/action', payload)
        .then((response) => {
          EventBus.$emit('send-notification', response.data.message, '#00b16a')
          this.selected = []
          this.manageDialog = false
          this.getExport()
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
    formatBytes(size) {
      if (size == null) return null
      return pretty(size, {binary: true}).replace('i','')
    },
    infoExport() {
      this.$router.push({ name:'utils.exports.info', params: { uri: this.selected[0]['uri'] }})
    },
    getServer(server_id) {
      EventBus.$emit('utils-get-server', server_id)
    },
    openColumnsDialog() {
      this.columnsRaw = [...this.columns]
      this.columnsDialog = true
    },
    selectAllColumns() {
      this.columnsRaw = ['username','mode','source','size','server_id','database','status','created','started','ended','overall','deleted']
    },
    deselectAllColumns() {
      this.columnsRaw = []
    },
    filterColumns() {
      this.columns = [...this.columnsRaw]
      this.columnsDialog = false
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
          (x.username != null && x.username.toLowerCase().includes(this.search.toLowerCase())) ||
          (x.mode != null && x.mode.toLowerCase().includes(this.search.toLowerCase())) ||
          (x.server_name != null && x.server_name.toLowerCase().includes(this.search.toLowerCase())) ||
          (x.database != null && x.database.toLowerCase().includes(this.search.toLowerCase())) ||
          (x.status != null && x.status.toLowerCase().includes(this.search.toLowerCase())) ||
          (x.created != null && x.created.toLowerCase().includes(this.search.toLowerCase())) ||
          (x.started != null && x.started.toLowerCase().includes(this.search.toLowerCase())) ||
          (x.ended != null && x.ended.toLowerCase().includes(this.search.toLowerCase())) ||
          (x.overall != null && x.overall.toLowerCase().includes(this.search.toLowerCase()))
        )
        this.total = items.length
        this.items = items.slice(itemStart, itemEnd)
      }
    },
    openFilter() {
      this.filter = this.filterApplied ? JSON.parse(JSON.stringify(this.filterOrigin)) : {}
      this.filterDialog = true
    },
    submitFilter() {
      // Check if all necessary fields are filled
      if (!this.$refs.form.validate()) {
        EventBus.$emit('send-notification', 'Please make sure all required fields are filled out correctly', '#EF5354')
        return
      }
      // Check if some filter was applied
      if (Object.keys(this.filter).length == 1 && 'deleted' in this.filter && !this.filter['deleted']) {
        EventBus.$emit('send-notification', 'Enter at least one filter.', '#EF5354')
        return
      }
      if (!Object.keys(this.filter).some(x => this.filter[x] != null && this.filter[x].length != 0)) {
        EventBus.$emit('send-notification', 'Enter at least one filter.', '#EF5354')
        return
      }
      this.filterDialog = false
      EventBus.$emit('utils-toggle-filter', { from: 'export', value: true })
      this.filterApplied = true
      this.getExport()
    },
    clearFilter() {
      this.filterDialog = false
      this.filter = {}
      EventBus.$emit('utils-toggle-filter', { from: 'export', value: false })
      this.filterApplied = false
      this.firstLoad = true
      this.sortBy = null
      this.sortDesc = null
      this.$router.replace({query: {}})
      this.$nextTick(() => this.getExport())
    },
    dateTimeDialogOpen(field) {
      this.dateTimeField = field
      this.dateTimeMode = 'date'
      this.dateTimeValue = { date: moment().format("YYYY-MM-DD"), time: moment().format("HH:mm") }
      if (this.filter[field] !== undefined && this.filter[field].length > 0) {
        let isValid = moment(this.filter[field], 'YYYY-MM-DD HH:mm', true).isValid()
        if (!isValid) {
          EventBus.$emit('send-notification', "Enter a valid date", '#EF5354')
          return
        }
        this.dateTimeValue = { date: moment(this.filter[field]).format("YYYY-MM-DD"), time: moment(this.filter[field]).format("HH:mm") }
      }
      this.dateTimeDialog = true
    },
    dateTimeSubmit() {
      if (this.dateTimeMode == 'date') this.dateTimeMode = 'time'
      else {
        this.filter[this.dateTimeField] = this.dateTimeValue.date + ' ' + this.dateTimeValue.time
        this.dateTimeDialog = false
      }
    },
    dateTimeNow() {
      this.dateTimeValue = { date: moment().format("YYYY-MM-DD"), time: moment().format("HH:mm") }
    },
    getStatusColor (status) {
      if (['IN PROGRESS'].includes(status)) return '#ff9800'
      if (['SUCCESS'].includes(status)) return '#4caf50'
      if (['FAILED','STOPPED'].includes(status)) return '#EF5354'
    },
    getStatusIcon (status) {
      if (['SUCCESS'].includes(status)) return { name: 'fas fa-check', margin: '0px' }
      if (['IN PROGRESS'].includes(status)) return { name: 'fas fa-spinner', margin: '0x' }
      if (['FAILED'].includes(status)) return { name: 'fas fa-times', margin: '4px' }
      if (['STOPPED'].includes(status)) return { name: 'fas fa-ban', margin: '0px' }
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color
      this.snackbar = true
    }
  }
}
</script>