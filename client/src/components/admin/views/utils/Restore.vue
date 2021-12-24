<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="body-2 white--text font-weight-medium" style="font-size:0.9rem!important"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-database</v-icon>RESTORE</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items>
          <v-btn :disabled="selected.length != 1" text @click="infoRestore()"><v-icon small style="margin-right:10px">fas fa-bookmark</v-icon>DETAILS</v-btn>
          <v-btn :disabled="selected.length == 0" text @click="manageRestore()"><v-icon small style="margin-right:10px;">fas fa-mouse-pointer</v-icon>MANAGE</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn text @click="openFilter" :style="{ backgroundColor : filterApplied ? '#4ba2f1' : '' }"><v-icon small style="margin-right:10px">fas fa-sliders-h</v-icon>FILTER</v-btn>
          <v-btn @click="getRestore" text><v-icon small style="margin-right:10px">fas fa-sync-alt</v-icon>REFRESH</v-btn>
        </v-toolbar-items>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-text-field @input="onSearch" v-model="search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
        <v-divider class="mx-3" inset vertical style="margin-right:4px!important"></v-divider>
        <v-btn @click="openColumnsDialog" icon title="Show/Hide columns" style="margin-right:-10px; width:40px; height:40px;"><v-icon small>fas fa-cog</v-icon></v-btn>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="computedHeaders" :items="items" :options.sync="options" :server-items-length="total" :loading="loading" loading-text="Loading... Please wait" item-key="id" show-select class="elevation-1" style="padding-top:5px;" mobile-breakpoint="0">
        <template v-ripple v-slot:[`header.data-table-select`]="{}">
          <v-simple-checkbox
            :value="items.length == 0 ? false : selected.length == items.length"
            :indeterminate="selected.length > 0 && selected.length != items.length"
            @click="selected.length == items.length ? selected = [] : selected = [...items]">
          </v-simple-checkbox>
        </template>
        <template v-slot:[`item.mode`]="{ item }">
          <div v-if="item.mode == 'file'">
            <v-icon :title="`${item.source} (${formatBytes(item.size)})`" small color="#23cba7" style="margin-right:5px; margin-bottom:3px">fas fa-file</v-icon>
            File
          </div>
          <div v-else-if="item.mode == 'url'">
            <v-icon :title="`${item.source} (${formatBytes(item.size)})`" small color="#e47911" style="margin-right:5px; margin-bottom:2px">fas fa-link</v-icon>
            URL
          </div>
          <div v-else-if="item.mode == 'cloud'">
            <v-icon :title="`${item.source} (${formatBytes(item.size)})`" color="#19b5fe" style="font-size:18px; margin-right:5px; margin-bottom:3px">fas fa-cloud</v-icon>
            Cloud Key
          </div>
        </template>
        <template v-slot:[`item.size`]="{ item }">
          {{ formatBytes(item.size) }}
        </template>
        <template v-slot:[`item.status`]="{ item }">
          <v-icon v-if="item.status == 'IN PROGRESS'" title="In Progress" small style="color: #ff9800; margin-left:8px;">fas fa-spinner</v-icon>
          <v-icon v-else-if="item.status == 'SUCCESS'" title="Success" small style="color: #4caf50; margin-left:9px;">fas fa-check</v-icon>
          <v-icon v-else-if="item.status == 'FAILED'" title="Failed" small style="color: #EF5354; margin-left:11px;">fas fa-times</v-icon>
          <v-icon v-else-if="item.status == 'STOPPED'" title="Stopped" small style="color: #EF5354; margin-left:8px;">fas fa-ban</v-icon>
        </template>
        <template v-slot:[`item.deleted`]="{ item }">
          <div :style="`margin-left:${item.deleted ? '8px' : '10px'}; font-weight:500; color: ${item.deleted ? '#EF5354' : '#00b16a'}`">{{ item.deleted ? 'YES' : 'NO'}}</div>
        </template>
      </v-data-table>
    </v-card>
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
                <div class="subtitle-1" style="margin-bottom:10px">Choose the action to perform for the selected restore(s).</div>
                <v-radio-group v-model="manageOption" hide-details style="margin-top:0px; margin-bottom:20px">
                  <v-radio value="recover" color="#4caf50">
                    <template v-slot:label>
                      <div style="margin-left:5px">
                        <div class="body-1 white--text">Recover</div>
                        <div class="font-weight-regular caption" style="font-size:0.85rem !important">Recover the restore making it visible.</div>
                      </div>
                    </template>
                  </v-radio>
                  <v-radio value="delete" color="#ff9800">
                    <template v-slot:label>
                      <div style="margin-left:5px">
                        <div class="body-1 white--text">Delete</div>
                        <div class="font-weight-regular caption" style="font-size:0.85rem !important">Delete the restore making it not visible.</div>
                      </div>
                    </template>
                  </v-radio>
                  <v-radio value="permanently" color="#EF5354">
                    <template v-slot:label>
                      <div style="margin-left:5px">
                        <div class="body-1 white--text">Delete Permanently</div>
                        <div class="font-weight-regular caption" style="font-size:0.85rem !important">Delete the restore permanently. This action cannot be undone.</div>
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
                      <v-autocomplete v-model="filter.mode" :items="restoreMode" multiple label="Mode" style="padding-top:0px;" hide-details>
                        <template v-slot:item="{ item }">
                          <div v-if="item == 'file'"><v-icon small color="#23cba7" style="margin-left:6px; margin-right:18px">fas fa-file</v-icon>File</div>
                          <div v-else-if="item == 'url'"><v-icon small color="#e47911" style="margin-left:3px; margin-right:14px">fas fa-link</v-icon>URL</div>
                          <div v-else-if="item == 'cloud'"><v-icon size="18" color="#19b5fe" style="margin-right:10px">fas fa-cloud</v-icon>Cloud Key</div>
                        </template>
                        <template v-slot:selection="{ item }">
                          <v-chip v-if="item == 'file'" label>
                            <v-icon small color="#23cba7" style="margin-right:10px">fas fa-file</v-icon>
                            File
                          </v-chip>
                          <v-chip v-else-if="item == 'url'" label>
                            <v-icon small color="#e47911" style="margin-right:10px">fas fa-link</v-icon>
                            URL
                          </v-chip>
                          <v-chip v-else-if="item == 'cloud'" label>
                            <v-icon size="18" color="#19b5fe" style="margin-top:2px; margin-left:2px; margin-right:12px">fas fa-cloud</v-icon>
                            Cloud Key
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
                    <v-col>
                      <v-autocomplete v-model="filter.status" :items="restoreStatus" multiple label="Status" style="padding-top:0px;" hide-details>
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
                      <v-checkbox v-model="filter.deleted" label="Include Deleted Restores" style="margin-top:0px" hide-details></v-checkbox>
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
                  <v-checkbox v-model="columnsRaw" label="User" value="username" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Mode" value="mode" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Source" value="source" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Size" value="size" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Server" value="server" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Database" value="database" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Status" value="status" hide-details style="margin-top:5px"></v-checkbox>
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
    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script>
import axios from 'axios';
import moment from 'moment';
import pretty from 'pretty-bytes';

export default {
  data: () => ({
    headers: [
      { text: 'User', align: 'left', value: 'username' },
      { text: 'Mode', align: 'left', value: 'mode' },
      { text: 'Source', align: 'left', value: 'source' },
      { text: 'Size', align: 'left', value: 'size' },
      { text: 'Server', align: 'left', value: 'server' },
      { text: 'Database', align: 'left', value: 'database' },
      { text: 'Status', align:'left', value: 'status' },
      { text: 'Started', align: 'left', value: 'started' },
      { text: 'Ended', align: 'left', value: 'ended' },
      { text: 'Overall', align: 'left', value: 'overall' },
      { text: 'Deleted', align: 'left', value: 'deleted' },
    ],
    origin: [],
    items: [],
    total: 0,
    selected: [],
    search: '',
    options: null,
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
    restoreMode: ['file','url','cloud'],
    restoreStatus: ['IN PROGRESS','SUCCESS','FAILED','STOPPED'],

    // Date / Time Picker
    dateTimeDialog: false,
    dateTimeField: '',
    dateTimeMode: 'date',
    dateTimeValue: { date: null, time: null },

    // Filter Columns Dialog
    columnsDialog: false,
    columns: ['username','mode','server','database','status','started','ended','overall'],
    columnsRaw: [],

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(2000),
    snackbarText: '',
    snackbarColor: ''
  }),
  watch: {
    options: {
      handler (newValue, oldValue) {
        if (oldValue == null || (oldValue.page == newValue.page && oldValue.itemsPerPage == newValue.itemsPerPage)) {
          this.getRestore()
        }
        else this.onSearch()
      },
      deep: true,
    },
  },
  computed: {
    computedHeaders() { return this.headers.filter(x => this.columns.includes(x.value)) },
  },
  methods: {
    getRestore() {
      this.loading = true
      var payload = {}
      // Build Filter
      let filter = this.filterApplied ? JSON.parse(JSON.stringify(this.filter)) : null
      if (this.filterApplied) {
        this.filterOrigin = JSON.parse(JSON.stringify(this.filter))
        for (let i of ['startedFrom','startedTo','endedFrom','endedTo']) {
          if (i in filter) filter[i] = moment(this.filter[i]).utc().format("YYYY-MM-DD HH:mm:ss")
        }
      }
      if (filter != null) payload['filter'] = filter
      // Build Sort
      const { sortBy, sortDesc } = this.options
      if (sortBy.length > 0) payload['sort'] = { column: sortBy[0], desc: sortDesc[0] }
      // Get Restores
      axios.get('/admin/utils/restore', { params: payload })
        .then((response) => {
          this.origin = response.data.restore.map(x => ({...x, created: this.dateFormat(x.created), started: this.dateFormat(x.started), ended: this.dateFormat(x.ended)}))
          this.filterUsers = response.data.users_list
          this.onSearch()
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    manageRestore() {
      this.manageOption = 'recover'
      this.manageDialog = true
    },
    manageSubmit() {
      // Check restore status
      if (['delete','permanently'].includes(this.manageOption) && this.selected.some(x => x.status == 'IN PROGRESS')) {
        this.notification("Can't delete restores that are in progress", '#EF5354')
        this.deleteDialog = false
        return
      }
      // Delete Restores
      this.loading = true
      const payload = { 
        action: this.manageOption,
        items: this.selected.map(x => x.id)
      }
      axios.post('/admin/utils/restore/action', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          this.selected = []
          this.manageDialog = false
          this.getRestore()
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
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
    infoRestore() {
      this.$router.push({ name: 'utils.restore.info', params: { id: this.selected[0]['id'] }})
    },
    openColumnsDialog() {
      this.columnsRaw = [...this.columns]
      this.columnsDialog = true
    },
    selectAllColumns() {
      this.columnsRaw = ['username','mode','source','size','server','database','status','started','ended','overall','deleted']
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
          (x.server != null && x.server.toLowerCase().includes(this.search.toLowerCase())) ||
          (x.database != null && x.database.toLowerCase().includes(this.search.toLowerCase())) ||
          (x.status != null && x.status.toLowerCase().includes(this.search.toLowerCase())) ||
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
        this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
        return
      }
      // Check if some filter was applied
      if (Object.keys(this.filter).length == 1 && 'deleted' in this.filter && !this.filter['deleted']) {
        this.notification('Enter at least one filter.', '#EF5354')
        return
      }
      if (!Object.keys(this.filter).some(x => this.filter[x] != null && this.filter[x].length != 0)) {
        this.notification('Enter at least one filter.', '#EF5354')
        return
      }
      this.filterDialog = false
      this.filterApplied = true
      this.getRestore()
    },
    clearFilter() {
      this.filterDialog = false
      this.filter = {}
      this.filterApplied = false
      this.getRestore()
    },
    dateTimeDialogOpen(field) {
      this.dateTimeField = field
      this.dateTimeMode = 'date'
      this.dateTimeValue = { date: moment().format("YYYY-MM-DD"), time: moment().format("HH:mm") }
      if (this.filter[field] !== undefined && this.filter[field].length > 0) {
        let isValid = moment(this.filter[field], 'YYYY-MM-DD HH:mm', true).isValid()
        if (!isValid) {
          this.notification("Enter a valid date", '#EF5354')
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