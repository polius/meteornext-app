<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">DEPLOYMENTS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items>
          <v-btn :disabled="!deploymentsBasic && !deploymentsPro" text title="Create a new deployment" @click="newDeploy()"><v-icon small style="padding-right:10px;">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn title="Show a deployment's details" :disabled="selected.length != 1" text @click="infoDeploy()"><v-icon small style="padding-right:10px">fas fa-bookmark</v-icon>DETAILS</v-btn>
          <v-btn title="Create a deployment with the same config as the selected one" :disabled="selected.length != 1" @click="cloneDeploy()" text><v-icon small style="margin-right:10px">fas fa-clone</v-icon>CLONE</v-btn>
          <v-btn @click="pinDeployments()" :disabled="selected.length == 0" :title="`${pinMode.charAt(0).toUpperCase() + pinMode.slice(1)} a deployment`" text><v-icon small style="padding-right:10px">fas fa-thumbtack</v-icon>{{ pinMode.toUpperCase() }}</v-btn>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-btn text @click="openFilter" :style="{ backgroundColor : filterApplied ? '#4ba2f1' : '' }"><v-icon small style="padding-right:10px">fas fa-sliders-h</v-icon>FILTER</v-btn>
          <v-btn @click="getDeployments" text><v-icon small style="margin-right:10px">fas fa-sync-alt</v-icon>REFRESH</v-btn>
        </v-toolbar-items>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
        <v-divider class="mx-3" inset vertical style="margin-right:4px!important"></v-divider>
        <v-btn @click="openColumnsDialog" icon title="Show/Hide columns" style="margin-right:-10px; width:40px; height:40px;"><v-icon small>fas fa-cog</v-icon></v-btn>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="computedHeaders" :items="items" :search="search" @current-items="(items) => current = items" :loading="loading" loading-text="Loading... Please wait" item-key="execution_id" show-select class="elevation-1" style="padding-top:5px;" mobile-breakpoint="0">
        <template v-ripple v-slot:[`header.data-table-select`]="{}">
          <v-simple-checkbox
            :value="items.length == 0 ? false : selected.length == items.length"
            :indeterminate="selected.length > 0 && selected.length != items.length"
            @click="checkboxClick">
          </v-simple-checkbox>
        </template>
        <template v-slot:[`item.name`]="{ item }">
          <v-row no-gutters>
            <v-col v-if="item.is_pinned" cols="auto" style="margin-right:10px">
              <v-icon color="#ff9900" small>fas fa-thumbtack</v-icon>
            </v-col>
            <v-col>
              <v-edit-dialog :return-value.sync="item.name" lazy @open="openName(item)" @save="saveName(item)"> 
                {{ item.name }}
                <template v-slot:input>
                  <v-text-field v-model="inline_editing_name" label="Name" single-line hide-details style="margin-bottom:20px;"></v-text-field>
                </template>
              </v-edit-dialog>
            </v-col>
          </v-row>
        </template>
        <template v-slot:[`item.release`]="{ item }">
          <v-edit-dialog :return-value.sync="item.release" large @open="openRelease(item)" @save="saveRelease(item)"> 
            {{ item.release }}
            <template v-slot:input>
              <v-autocomplete v-model="inline_editing_release" :items="releaseItems" label="Releases" hide-details style="margin-top:15px; margin-bottom:5px;"></v-autocomplete>
            </template>
          </v-edit-dialog>
        </template>
        <template v-slot:[`item.environment`]="{ item }">
          <span :title="item.environment_shared ? (item.environment_secured ? 'Shared (Secured)' : 'Shared') : (item.environment_secured ? 'Personal (Secured)' : 'Personal')">{{ item.environment_name }}</span>
        </template>
        <template v-slot:[`item.mode`]="{ item }">
          <v-icon small :title="item.mode.charAt(0).toUpperCase() + item.mode.slice(1).toLowerCase()" :color="getModeColor(item.mode)" :style="`text-transform:capitalize; margin-left:${item.mode == 'BASIC' ? '8px' : '6px'}`">{{ item.mode == 'BASIC' ? 'fas fa-chess-knight' : 'fas fa-chess-queen' }}</v-icon>
        </template>
        <template v-slot:[`item.method`]="{ item }">
          <span :style="'color: ' + getMethodColor(item.method)">{{ item.method }}</span>
        </template>
        <template v-slot:[`item.status`]="{ item }">
          <v-icon v-if="item.status == 'CREATED'" title="Created" small style="color: #3498db; margin-left:9px;">fas fa-check</v-icon>
          <v-icon v-else-if="item.status == 'SCHEDULED'" :title="parseSchedule(item.schedule_type, item.scheduled)" small style="color: #ff9800; margin-left:8px;">fas fa-clock</v-icon>
          <v-icon v-else-if="item.status == 'QUEUED'" :title="`Queued: ${item.queue}`" small style="color: #3498db; margin-left:8px;">fas fa-clock</v-icon>
          <v-icon v-else-if="item.status == 'STARTING'" title="Starting" small style="color: #3498db; margin-left:8px;">fas fa-spinner</v-icon>
          <v-icon v-else-if="item.status == 'IN PROGRESS'" title="In Progress" small style="color: #ff9800; margin-left:8px;">fas fa-spinner</v-icon>
          <v-icon v-else-if="item.status == 'SUCCESS'" title="Success" small style="color: #4caf50; margin-left:9px;">fas fa-check</v-icon>
          <v-icon v-else-if="item.status == 'WARNING'" title="Some queries failed" small style="color: #ff9800; margin-left:9px;">fas fa-check</v-icon>
          <v-icon v-else-if="item.status == 'FAILED'" title="Failed" small style="color: #EF5354; margin-left:11px;">fas fa-times</v-icon>
          <v-icon v-else-if="item.status == 'STOPPING'" title="Stopping" small style="color: #ff9800; margin-left:8px;">fas fa-ban</v-icon>
          <v-icon v-else-if="item.status == 'STOPPED'" title="Stopped" small style="color: #EF5354; margin-left:8px;">fas fa-ban</v-icon>
        </template>
        <template v-slot:[`item.scheduled`]="{ item }">
          <span>{{ item.scheduled === null ? '' : item.scheduled.slice(0,-3) }}</span>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="filterDialog" persistent max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text text-subtitle-1"><v-icon small style="padding-right:10px; padding-bottom:1px">fas fa-sliders-h</v-icon>FILTER DEPLOYMENTS</v-toolbar-title>
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
                      <v-autocomplete v-model="filter.name" :items="deploymentsItems" label="Name" style="padding-top:0px;" hide-details></v-autocomplete>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="6" style="padding-right:8px;">
                      <v-autocomplete v-model="filter.release" :items="releaseItems" label="Release" style="padding-top:0px;" hide-details></v-autocomplete>
                    </v-col>
                    <v-col cols="6" style="padding-left:8px;">
                      <v-autocomplete v-model="filter.mode" :items="deploymentMode" multiple label="Mode" style="padding-top:0px;" hide-details>
                        <template v-slot:item="{ item }">
                          <v-icon small :color="getModeColor(item)" :style="`text-transform:capitalize; margin-left:5px; margin-right:${item == 'BASIC' ? '17px' : '15px'}`">{{ item == 'BASIC' ? 'fas fa-chess-knight' : 'fas fa-chess-queen' }}</v-icon>
                          <span :style="`color:${getModeColor(item)};`">{{ item }}</span>
                        </template>
                        <template v-slot:selection="{ item }">
                          <v-chip label>
                            <v-icon small :color="getModeColor(item)" style="text-transform:capitalize; margin-right:10px">{{ item == 'BASIC' ? 'fas fa-chess-knight' : 'fas fa-chess-queen' }}</v-icon>
                            <span :style="`color:${getModeColor(item)};`">{{ item }}</span>
                          </v-chip>
                        </template>
                      </v-autocomplete>
                    </v-col>
                  </v-row>
                  <v-row style="margin-top:10px">
                    <v-col cols="6" style="padding-right:8px;">
                      <v-autocomplete v-model="filter.method" :items="deploymentMethod" multiple label="Method" style="padding-top:0px;" hide-details>
                        <template v-slot:item="{ item }">
                          <span :style="`color:${ item == 'VALIDATE' ? '#00b16a' : item == 'TEST' ? '#ff9800' : '#EF5354'}`">{{ item }}</span>
                        </template>
                        <template v-slot:selection="{ item }">
                          <v-chip label>
                            <span :style="`color:${ item == 'VALIDATE' ? '#00b16a' : item == 'TEST' ? '#ff9800' : '#EF5354'}`">{{ item }}</span>
                          </v-chip>
                        </template>
                      </v-autocomplete>
                    </v-col>
                    <v-col cols="6" style="padding-left:8px;">
                      <v-autocomplete v-model="filter.status" :items="deploymentStatus" multiple label="Status" style="padding-top:0px;" hide-details>
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
                      <v-checkbox v-model="filter.allExecutions" label="Filter all deployment executions" style="margin-top:0px" hide-details></v-checkbox>
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
                  <v-checkbox v-model="columnsRaw" label="Name" value="name" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Release" value="release" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Username" value="username" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Environment" value="environment" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Mode" value="mode" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Method" value="method" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Status" value="status" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Created" value="created" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Scheduled" value="scheduled" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Started" value="started" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Ended" value="ended" hide-details style="margin-top:5px"></v-checkbox>
                  <v-checkbox v-model="columnsRaw" label="Overall" value="overall" hide-details style="margin-top:5px"></v-checkbox>
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

export default {
  data: () => ({
    headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Release', align: 'left', value: 'release' },
      { text: 'Environment', align: 'left', value: 'environment' },
      { text: 'Mode', align: 'left', value: 'mode' },
      { text: 'Method', align: 'left', value: 'method' },
      { text: 'Status', align:'left', value: 'status' },
      { text: 'Created', align: 'left', value: 'created' },
      { text: 'Scheduled', align: 'left', value: 'scheduled' },
      { text: 'Started', align: 'left', value: 'started' },
      { text: 'Ended', align: 'left', value: 'ended' },
      { text: 'Overall', align: 'left', value: 'overall' }
    ],
    items: [],
    current: [],
    selected: [],
    search: '',
    loading: false,

    // Inline Editing
    inline_editing_name: '',
    inline_editing_release: '',

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
    filterOrigin: {},
    filter: {},
    filterApplied: false,
    nameItems: [],
    releaseItems: [],
    deploymentsItems: [],
    deploymentMode: ['BASIC','PRO'],
    deploymentMethod: ['VALIDATE','TEST','DEPLOY'],
    deploymentStatus: ['CREATED','QUEUED','STARTING','SCHEDULED','IN PROGRESS','WARNING','STOPPING','FAILED','STOPPED','SUCCESS'],

    // Date / Time Picker
    dateTimeDialog: false,
    dateTimeField: '',
    dateTimeMode: 'date',
    dateTimeValue: { date: null, time: null },

    // Filter Columns Dialog
    columnsDialog: false,
    columns: ['name','release','username','environment','mode','method','status','created','started','ended','overall'],
    columnsRaw: [],

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  created() {
    this.getDeployments()
  },
  computed: {
    computedHeaders() { return this.headers.filter(x => this.columns.includes(x.value)) },
    pinMode() { return this.selected.length == 0 || this.selected.find(x => !x.is_pinned) ? 'pin' : 'unpin' },
    deploymentsBasic : function() { return this.$store.getters['app/deployments_basic'] },
    deploymentsPro : function() { return this.$store.getters['app/deployments_pro'] },
  },
  methods: {
    getDeployments() {
      // Build Filter
      let filter = null
      if (this.filterApplied) {
        filter = JSON.parse(JSON.stringify(this.filter))
        if (JSON.stringify(this.$route.query) != JSON.stringify(filter)) this.$router.replace({query: filter})
      }
      else if (Object.keys(this.$route.query).length != 0) {
        this.filter = filter = Object.keys(this.$route.query).reduce((acc, val) => {
          if (['mode','method','status'].includes(val) && typeof this.$route.query[val] == 'string') acc[val] = [this.$route.query[val]]
          else acc[val] = this.$route.query[val]
          return acc
        },{})
        this.filterApplied = true
      }
      if (filter != null) {
        this.filterOrigin = JSON.parse(JSON.stringify(this.filter))
        for (let i of ['createdFrom','createdTo','startedFrom','startedTo','endedFrom','endedTo']) {
          if (i in filter) filter[i] = moment(this.filter[i]).utc().format("YYYY-MM-DD HH:mm:ss")
        }
      }
      // Get Deployments
      this.loading = true
      const payload = filter == null ? {} : {'filter': filter}
      axios.get('/deployments', { params: payload })
        .then((response) => {
          this.items = response.data.deployments.map(x => ({...x, created: this.dateFormat(x.created), scheduled: this.dateFormat(x.scheduled), started: this.dateFormat(x.started), ended: this.dateFormat(x.ended)}))
          this.releaseItems = response.data.releases.map(x => x.name)
          this.deploymentsItems = response.data.deployments_list.map(x => x.name)
          this.selected = []
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    openName(item) {
      this.inline_editing_name = item.name
    },
    saveName(item) {
      if (this.inline_editing_name == item.name) {
        this.notification('Deployment edited', '#00b16a')
        return
      }
      this.loading = true
      // Edit release name in the DB
      const payload = {
        put: 'name',
        id: item.id,
        name: this.inline_editing_name
      }
      axios.put('/deployments', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          // Reload Deployments Data
          this.getDeployments()
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        }) 
    },
    openRelease(item) {
      this.inline_editing_release = item.release
    },
    saveRelease(item) {
      if (this.inline_editing_release == item.release) {
        this.notification('Deployment edited', '#00b16a')
        return
      }
      this.loading = true
      // Edit deployment release in the DB
      const payload = {
        put: 'release',
        id: item.id,
        release: this.inline_editing_release
      }
      axios.put('/deployments', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          // Reload Deployments Data
          this.getDeployments()
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    getModeColor (mode) {
      if (mode == 'BASIC') return 'rgb(250, 130, 49)'
      else if (mode == 'PRO') return 'rgb(235, 95, 93)'
    },
    getMethodColor (method) {
      if (method == 'DEPLOY') return '#EF5354'
      else if (method == 'TEST') return '#ff9800'
      else if (method == 'VALIDATE') return '#4caf50'
    },
    getStatusColor (status) {
      if (['CREATED','QUEUED','STARTING'].includes(status)) return '#3498db'
      if (['SCHEDULED','IN PROGRESS','WARNING','STOPPING'].includes(status)) return '#ff9800'
      if (['SUCCESS'].includes(status)) return '#4caf50'
      if (['FAILED','STOPPED'].includes(status)) return '#EF5354'
    },
    getStatusIcon (status) {
      if (['CREATED','SUCCESS','WARNING'].includes(status)) return { name: 'fas fa-check', margin: '0px' }
      if (['SCHEDULED','QUEUED'].includes(status)) return { name: 'fas fa-clock', margin: '0px' }
      if (['STARTING','IN PROGRESS'].includes(status)) return { name: 'fas fa-spinner', margin: '0x' }
      if (['FAILED'].includes(status)) return { name: 'fas fa-times', margin: '2px' }
      if (['STOPPING','STOPPED'].includes(status)) return { name: 'fas fa-ban', margin: '0px' }
    },
    parseSchedule(type, value) {
      if (type == null) return 'Scheduled (One time): ' + value.slice(0,-3)
      return 'Scheduled (' + type.replace('_',' ').charAt(0).toUpperCase() + type.replace('_',' ').slice(1) + '): ' + value.slice(0,-3)
    },
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
    newDeploy() {
      if (this.deploymentsBasic) this.$router.push('/deployments/new/basic')
      else if (this.deploymentsPro) this.$router.push('/deployments/new/pro')
    },
    infoDeploy() {
      this.$router.push({ name:'deployments.execution', params: { uri: this.selected[0]['uri'] }})
    },
    cloneDeploy() {
      this.$router.push({ name: 'deployments.new', params: { mode: this.selected[0]['mode'].toLowerCase(), uri: this.selected[0]['uri'] }})
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
      if (Object.keys(this.filter).length == 1 && 'allExecutions' in this.filter && !this.filter['allExecutions']) {
        this.notification('Enter at least one filter.', '#EF5354')
        return
      }
      if (!Object.keys(this.filter).some(x => this.filter[x] != null && this.filter[x].length != 0)) {
        this.notification('Enter at least one filter.', '#EF5354')
        return
      }
      this.filterDialog = false
      this.filterApplied = true
      this.getDeployments()
    },
    clearFilter() {
      this.filterDialog = false
      this.filter = {}
      this.filterApplied = false
      this.$router.replace({query: {}})
      this.getDeployments()
    },
    pinDeployments() {
      const toPin = this.selected.find(x => !x.is_pinned)
      const payload = this.selected.map(x => x.id)
      if (toPin) {
        axios.post('/deployments/pinned', payload)
          .then((response) => {
            for (let i = 0; i < this.selected.length; ++i) this.selected[i]['is_pinned'] = 1
            this.notification(response.data.message, '#00b16a', Number(1000))
            this.getDeployments()
          })
          .catch((error) => {
            if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
            else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
          })
      }
      else {
        axios.delete('/deployments/pinned', { data: payload })
          .then((response) => {
            for (let i = 0; i < this.selected.length; ++i) this.selected[i]['is_pinned'] = 0
            this.notification(response.data.message, '#00b16a', Number(1000))
            this.getDeployments()
          })
          .catch((error) => {
            if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
            else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
          })
      }
    },
    openColumnsDialog() {
      this.columnsRaw = [...this.columns]
      this.columnsDialog = true
    },
    selectAllColumns() {
      this.columnsRaw = ['name','release','username','environment','mode','method','status','created','scheduled','started','ended','overall']
    },
    deselectAllColumns() {
      this.columnsRaw = []
    },
    filterColumns() {
      this.columns = [...this.columnsRaw]
      this.columnsDialog = false
    },
    notification(message, color, time=Number(3000)) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbarTimeout = time
      this.snackbar = true
    },
    checkboxClick() {
      if (this.search.trim().length == 0) this.selected.length == this.items.length ? this.selected = [] : this.selected = [...this.items]
      else {
        const allSelected = this.current.every(x => this.selected.find(y => y.id == x.id))
        if (allSelected) this.selected = this.selected.filter(x => !this.current.find(y => y.id == x.id))
        else this.selected = this.selected.filter(x => !this.current.find(y => y.id == x.id)).concat(this.current)
      }
    },
  }
}
</script>