<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="white--text subtitle-1">DEPLOYMENTS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down" style="padding-left:0px;">
          <v-btn text @click="filter_dialog = true" class="body-2" :style="{ backgroundColor : filter_applied ? '#4ba2f1' : '' }"><v-icon small style="padding-right:10px">fas fa-search</v-icon>FILTER</v-btn>
          <v-btn text v-if="selected.length == 1" @click="infoDeployment()" class="body-2"><v-icon small style="padding-right:10px">fas fa-info</v-icon>INFORMATION</v-btn>
        </v-toolbar-items>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="id" show-select class="elevation-1" style="padding-top:5px;">
        <template v-slot:[`item.mode`]="{ item }">
          <v-chip outlined :color="getModeColor(item.mode)">{{ item.mode }}</v-chip>
        </template>
        <template v-slot:[`item.method`]="{ item }">
          <span :style="'color: ' + getMethodColor(item.method)" style="font-weight:500">{{ item.method }}</span>
        </template>
        <template v-slot:[`item.status`]="{ item }">
          <v-icon v-if="item.status == 'CREATED'" title="Created" small style="color: #3498db; margin-left:9px;">fas fa-check</v-icon>
          <v-icon v-else-if="item.status == 'SCHEDULED'" title="Scheduled" small style="color: #ff9800; margin-left:8px;">fas fa-clock</v-icon>
          <v-icon v-else-if="item.status == 'QUEUED'" title="Queued" small style="color: #3498db; margin-left:8px;">fas fa-clock</v-icon>
          <v-icon v-else-if="item.status == 'STARTING'" title="Starting" small style="color: #3498db; margin-left:8px;">fas fa-spinner</v-icon>
          <v-icon v-else-if="item.status == 'IN PROGRESS'" title="In Progress" small style="color: #ff9800; margin-left:8px;">fas fa-spinner</v-icon>
          <v-icon v-else-if="item.status == 'SUCCESS'" title="Success" small style="color: #4caf50; margin-left:9px;">fas fa-check</v-icon>
          <v-icon v-else-if="item.status == 'WARNING'" title="Some queries failed" small style="color: #ff9800; margin-left:9px;">fas fa-check</v-icon>
          <v-icon v-else-if="item.status == 'FAILED'" title="Failed" small style="color: #e74c3c; margin-left:11px;">fas fa-times</v-icon>
          <v-icon v-else-if="item.status == 'STOPPING'" title="Stopping" small style="color: #ff9800; margin-left:8px;">fas fa-ban</v-icon>
          <v-icon v-else-if="item.status == 'STOPPED'" title="Stopped" small style="color: #e74c3c; margin-left:8px;">fas fa-ban</v-icon>
        </template>
        <template v-slot:[`item.created`]="{ item }">
          <span>{{ dateFormat(item.created) }}</span>
        </template>
        <template v-slot:[`item.started`]="{ item }">
          <span>{{ dateFormat(item.started) }}</span>
        </template>
        <template v-slot:[`item.ended`]="{ item }">
          <span>{{ dateFormat(item.ended) }}</span>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="filter_dialog" persistent max-width="768px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="text-subtitle-1 white--text">FILTER DEPLOYMENTS</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="filter_dialog = false" style="width:40px; height:40px"><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 0px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:25px; margin-bottom:25px;">
                  <v-text-field v-model="filter_dialog_data.name" label="Name" style="padding-top:0px;"></v-text-field>
                  <v-row no-gutters style="margin-top:5px">
                    <v-col style="padding-right:10px">
                      <v-text-field v-model="filter_dialog_data.username" label="Username" style="padding-top:0px;"></v-text-field>
                    </v-col>
                    <v-col style="padding-left:10px">
                      <v-text-field v-model="filter_dialog_data.release" label="Release" style="padding-top:0px;"></v-text-field>
                    </v-col>
                  </v-row>
                  <v-row no-gutters style="margin-top:5px">
                    <v-col style="padding-right:10px">
                      <v-select v-model="filter_dialog_data.mode" :items="deployment_modes" multiple label="Mode" style="padding-top:0px;"></v-select>
                    </v-col>
                    <v-col style="padding-left:10px">
                      <v-select v-model="filter_dialog_data.status" :items="deployment_status" multiple label="Status" style="padding-top:0px;"></v-select>
                    </v-col>
                  </v-row>
                  <v-row no-gutters style="margin-top:5px">
                    <v-col style="padding-right:10px">
                      <v-text-field v-model="filter_dialog_data.created_from" label="Created (From)" placeholder="YYYY-MM-DD hh:mm:ss" @click="picker_change('created_from')" readonly style="padding-top:0px;"></v-text-field>
                    </v-col>
                    <v-col style="padding-left:10px">
                      <v-text-field v-model="filter_dialog_data.created_to" label="Created (To)" placeholder="YYYY-MM-DD hh:mm:ss" @click="picker_change('created_to')" readonly style="padding-top:0px;"></v-text-field>
                    </v-col>
                  </v-row>
                  <v-divider></v-divider>
                  <div style="margin-top:20px;">
                    <v-btn :loading="loading" color="#00b16a" @click="filterDeployments()">Confirm</v-btn>
                    <v-btn :disabled="loading" color="error" @click="closeFilter()" style="margin-left:5px;">Cancel</v-btn>
                    <v-btn v-if="filter_applied" :disabled="loading" color="info" @click="clearFilter()" style="float:right;">Remove Filter</v-btn>
                  </div>
                </v-form>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-dialog v-model="pickerDialog" persistent width="290px">
      <v-date-picker v-if="picker_mode=='date'" v-model="picker_date" color="info" scrollable>
        <v-btn text color="info" @click="picker_now()">Now</v-btn>
        <v-spacer></v-spacer>
        <v-btn text color="error" @click="picker_close()">Cancel</v-btn>
        <v-btn text color="#00b16a" @click="picker_submit()">Confirm</v-btn>
      </v-date-picker>
      <v-time-picker v-else-if="picker_mode=='time'" v-model="picker_time" color="info" format="24hr" scrollable>
        <v-btn text color="info" @click="picker_now()">Now</v-btn>
        <v-spacer></v-spacer>
        <v-btn text color="error" @click="picker_close()">Cancel</v-btn>
        <v-btn text color="#00b16a" @click="picker_submit()">Confirm</v-btn>
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

<script>
import axios from 'axios';
import moment from 'moment';

export default {
  data: () => ({
    headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Release', align: 'left', value: 'release' },
      { text: 'Username', align: 'left', value: 'username' },
      { text: 'Environment', align: 'left', value: 'environment' },
      { text: 'Mode', align: 'left', value: 'mode' },
      { text: 'Method', align: 'left', value: 'method' },
      { text: 'Status', align:'left', value: 'status' },
      { text: 'Created', align: 'left', value: 'created' },
      { text: 'Started', align: 'left', value: 'started' },
      { text: 'Ended', align: 'left', value: 'ended' }
    ],
    items: [],
    selected: [],
    search: '',
    loading: true,

    // Filter Dialog
    filter_dialog: false,
    filter_dialog_data: {},
    filter_applied: false,
    deployment_modes: ['Basic','Pro'],
    deployment_status: ['CREATED','SCHEDULED','QUEUED','STARTING','IN PROGRESS','SUCCESS','WARNING','FAILED','STOPPING','STOPPED'],

    // Date / Time Picker
    pickerDialog: false,
    picker_mode: 'date',
    picker_component: '',
    picker_date: '',
    picker_time: '',

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  created() {
    this.getDeployments()
  },
  methods: {
    getDeployments() {
      axios.get('/admin/deployments')
        .then((res) => {
          this.items = res.data.data
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
    },
    filterDeployments() {
      // Parse Filter
      if (this.filter_dialog_data.name == '') delete this.filter_dialog_data.name
      if (this.filter_dialog_data.release == '') delete this.filter_dialog_data.release
      if (this.filter_dialog_data.username == '') delete this.filter_dialog_data.username
      if (this.filter_dialog_data.mode == '') delete this.filter_dialog_data.mode
      if (this.filter_dialog_data.status == '') delete this.filter_dialog_data.status
      if (this.filter_dialog_data.created_from == '') delete this.filter_dialog_data.created_from
      if (this.filter_dialog_data.created_to == '') delete this.filter_dialog_data.created_to
      // Set filter var
      this.filter_applied = Object.keys(this.filter_dialog_data).length > 0
      // Enable Loading
      this.loading = true
      // Get Deployment Data
      axios.get('/admin/deployments/filter', { params: { data: this.filter_dialog_data }})
        .then((response) => {
          this.items = response.data.data
          this.filter_dialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', 'error')
        })
        .finally(() => this.loading = false)
    },
    closeFilter() {
      this.filter_dialog = false
      if (!this.filter_applied) this.filter_dialog_data = {}
    },
    clearFilter() {
      this.loading = true
      this.filter_applied = false
      this.filter_dialog_data = {}
      this.filter_dialog = false
      this.getDeployments()
    },
    infoDeployment() {
      const id = this.selected[0]['mode'].substring(0, 1) + this.selected[0]['execution_id']
      this.$router.push({ name:'deployment', params: { id: id }})
    },
    picker_close() {
      this.pickerDialog = false
      this.picker_mode = 'date'
    },
    picker_init(datetime='') {
      var date = moment()
      if (datetime) date = moment(datetime)
      this.picker_date = date.format("YYYY-MM-DD")
      this.picker_time = date.format("HH:mm")
    },
    picker_now() {
      const date = moment()
      if (this.picker_mode == 'date') this.picker_date = date.format("YYYY-MM-DD")
      else if (this.picker_mode == 'time') this.picker_time = date.format("HH:mm")
    },
    picker_change(component) {
      this.picker_component = component
      if (component == 'created_from') this.picker_init(this.filter_dialog_data.created_from)
      else if (component == 'created_to') this.picker_init(this.filter_dialog_data.created_to)
      this.pickerDialog = true
    },
    picker_submit() {
      if (this.picker_mode == 'date') this.picker_mode = 'time'
      else if (this.picker_mode == 'time') {
        if (this.picker_component == 'created_from') this.filter_dialog_data.created_from = this.picker_date + ' ' + this.picker_time
        else if (this.picker_component == 'created_to') this.filter_dialog_data.created_to = this.picker_date + ' ' + this.picker_time
        this.pickerDialog = false
        this.picker_mode = 'date'
      }
    },
    getModeColor (mode) {
      if (mode == 'BASIC') return 'rgb(250, 130, 49)'
      else if (mode == 'PRO') return 'rgb(235, 95, 93)'
    },
    getMethodColor (method) {
      if (method == 'DEPLOY') return '#e74c3c'
      else if (method == 'TEST') return '#ff9800'
      else if (method == 'VALIDATE') return '#4caf50'
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