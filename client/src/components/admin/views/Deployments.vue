<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title>DEPLOYMENTS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down" style="padding-left:0px;">
          <v-btn text @click="refreshDeployment()"><v-icon small style="padding-right:10px">fas fa-sync</v-icon>REFRESH</v-btn>
          <v-btn text @click="search_dialog = true"><v-icon small style="padding-right:10px">fas fa-search</v-icon>SEARCH</v-btn>
          <v-btn text v-if="selected.length == 1" @click="infoDeployment()"><v-icon small style="padding-right:10px">fas fa-info</v-icon>INFORMATION</v-btn>
        </v-toolbar-items>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" style="margin-left:10px;" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="id" show-select class="elevation-1" style="padding-top:5px;">
        <template v-slot:item.mode="props">
          <v-chip :color="getModeColor(props.item.mode)">{{ props.item.mode }}</v-chip>
        </template>
        <template v-slot:item.method="props">
          <span :style="'color: ' + getMethodColor(props.item.method)" style="font-weight:500">{{ props.item.method }}</span>
        </template>
        <template v-slot:item.status="props">
          <v-icon v-if="props.item.status == 'CREATED'" title="Created" small style="color: #3498db; margin-left:9px;">fas fa-check</v-icon>
          <v-icon v-else-if="props.item.status == 'QUEUED'" title="Queued" small style="color: #3498db; margin-left:8px;">fas fa-clock</v-icon>
          <v-icon v-else-if="props.item.status == 'STARTING'" title="Starting" small style="color: #3498db; margin-left:8px;">fas fa-spinner</v-icon>
          <v-icon v-else-if="props.item.status == 'IN PROGRESS'" title="In Progress" small style="color: #ff9800; margin-left:8px;">fas fa-spinner</v-icon>
          <v-icon v-else-if="props.item.status == 'SUCCESS'" title="Success" small style="color: #4caf50; margin-left:9px;">fas fa-check</v-icon>
          <v-icon v-else-if="props.item.status == 'WARNING'" title="Some queries failed" small style="color: #ff9800; margin-left:9px;">fas fa-check</v-icon>
          <v-icon v-else-if="props.item.status == 'FAILED'" title="Failed" small style="color: #f44336; margin-left:11px;">fas fa-times</v-icon>
          <v-icon v-else-if="props.item.status == 'STOPPING'" title="Stopping" small style="color: #ff9800; margin-left:8px;">fas fa-ban</v-icon>
          <v-icon v-else-if="props.item.status == 'STOPPED'" title="Stopped" small style="color: #f44336; margin-left:8px;">fas fa-ban</v-icon>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="search_dialog" persistent max-width="768px">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">Search Deployments</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn icon @click="search_dialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding: 0px 20px 0px;">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="form" style="margin-top:15px; margin-bottom:20px;">
                  <v-text-field v-model="search_dialog_data.username" label="Username"></v-text-field>
                  <v-select v-model="search_dialog_data.mode" :items="deployment_modes" multiple label="Mode" required style="padding-top:0px;"></v-select>
                  <v-select v-model="search_dialog_data.status" :items="deployment_status" multiple label="Status" required style="padding-top:0px;"></v-select>
                  <v-text-field v-model="search_dialog_data.created_from" label="Created (From)" placeholder="YYYY-MM-DD hh:mm:ss" style="padding-top:0px;"></v-text-field>
                  <v-text-field v-model="search_dialog_data.created_to" label="Created (To)" placeholder="YYYY-MM-DD hh:mm:ss" style="padding-top:0px;"></v-text-field>
                  <v-divider></v-divider>
                  <div style="margin-top:20px;">
                    <v-btn :loading="loading" color="success" @click="searchDeployments()">Confirm</v-btn>
                    <v-btn :disabled="loading" color="error" @click="search_dialog=false" style="margin-left:10px;">Cancel</v-btn>
                  </div>
                </v-form>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn color="white" text @click="snackbar = false">Close</v-btn>
    </v-snackbar>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data: () => ({
    headers: [
      { text: 'Name', align: 'left', value: 'name' },
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

    // Search Dialog
    search_dialog: false,
    search_dialog_data: {},
    deployment_modes: ['Basic','Pro','Inbenta'],
    deployment_status: ['CREATED','QUEUED','STARTING','IN PROGRESS','SUCCESS','WARNING','FAILED','STOPPING','STOPPED'],

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
          this.loading = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        });
    },
    searchDeployments() {
      // Parse Search Filter
      if (this.search_dialog_data.username == '') delete this.search_dialog_data.username
      if (this.search_dialog_data.mode == '') delete this.search_dialog_data.mode
      if (this.search_dialog_data.status == '') delete this.search_dialog_data.status
      if (this.search_dialog_data.created_from == '') delete this.search_dialog_data.created_from
      if (this.search_dialog_data.created_to == '') delete this.search_dialog_data.created_to
      // Enable Loading
      this.loading = true
      // Get Deployment Data
      axios.get('/admin/deployments/search', { params: { data: this.search_dialog_data }})
        .then((response) => {
          this.items = response.data.data
          this.loading = false
          this.search_dialog = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    refreshDeployment() {
      this.loading = true
      this.getDeployments()
    },
    infoDeployment() {
      const id = this.selected[0]['mode'].substring(0, 1) + this.selected[0]['execution_id']
      this.$router.push({ name:'deployment', params: { id: id, admin: true }})
    },
    getModeColor (mode) {
      if (mode == 'BASIC') return '#67809f'
      else if (mode == 'PRO') return '#22313f'
    },
    getMethodColor (method) {
      if (method == 'DEPLOY') return '#f44336'
      else if (method == 'TEST') return '#ff9800'
      else if (method == 'VALIDATE') return '#4caf50'
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  }
}
</script>