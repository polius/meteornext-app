<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title>DEPLOYMENTS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down" style="padding-left:0px;">
          <v-btn text @click="refreshDeployment()"><v-icon small style="padding-right:10px">fas fa-sync</v-icon>REFRESH</v-btn>
          <v-btn text @click="searchDeployment()"><v-icon small style="padding-right:10px">fas fa-search</v-icon>SEARCH</v-btn>
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
      const path = this.$store.getters.url + '/admin/deployments'
      axios.get(path)
        .then((res) => {
          this.items = res.data.data
          this.loading = false
        })
        .catch((error) => {
          if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
          // eslint-disable-next-line
          console.error(error)
        });
    },
    refreshDeployment() {
      this.loading = true
      this.getDeployments()
    },
    searchDeployment() {

    },
    infoDeployment() {
      this.$router.push({ name:'deployments.information', params: { executionID: this.selected[0]['execution_id'], deploymentMode: this.selected[0]['mode'] }})
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