<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title class="white--text">DEPLOYMENTS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn v-if="selected.length == 0" text @click='newDeploy()'><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
          <v-btn v-if="selected.length == 1" text @click="infoDeploy()"><v-icon small style="padding-right:10px">fas fa-info</v-icon>INFO</v-btn>
          <v-btn v-if="selected.length == 1" text @click="progressDeploy()"><v-icon small style="padding-right:10px">fas fa-spinner</v-icon>PROGRESS</v-btn>
          <v-btn v-if="selected.length == 1" text :href="this.selected[0]['results']"><v-icon small style="padding-right:10px">fas fa-meteor</v-icon>LOGS</v-btn>
          <v-btn v-if="selected.length > 0" text @click="deleteDeploy()"><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
        </v-toolbar-items>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" style="margin-left:10px;" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="id" show-select class="elevation-1" style="padding-top:5px;">
        <template v-slot:item.name="props">
          <v-edit-dialog :return-value.sync="props.item.name" lazy @open="open(props.item)" @save="save(props.item)"> 
            {{ props.item.name }}
            <template v-slot:input>
              <v-text-field v-model="inline_editing" label="Environment" single-line></v-text-field>
            </template>
          </v-edit-dialog>
        </template>
        <template v-slot:item.mode="props">
          <v-chip :color="getModeColor(props.item.mode)">{{ props.item.mode }}</v-chip>
        </template>
        <template v-slot:item.method="props">
          <span :style="'color: ' + getMethodColor(props.item.method)" style="font-weight:500">{{ props.item.method }}</span>
        </template>
        <template v-slot:item.status="props">
          <v-icon v-if="props.item.status == 'CREATED'" title="Created" small style="color: #3498db; margin-left:9px;">fas fa-check</v-icon>
          <v-icon v-else-if="props.item.status == 'QUEUED'" title="Queued" small style="color: #3498db; margin-left:8px;">fas fa-clock</v-icon>
          <v-icon v-else-if="props.item.status == 'IN PROGRESS'" title="In Progress" small style="color: #ff9800; margin-left:8px;">fas fa-spinner</v-icon>
          <v-icon v-else-if="props.item.status == 'SUCCESS'" title="Success" small style="color: #4caf50; margin-left:9px;">fas fa-check-double</v-icon>
          <v-icon v-else-if="props.item.status == 'FAILED'" title="Failed" small style="color: #f44336; margin-left:11px;">fas fa-times</v-icon>
          <v-icon v-else-if="props.item.status == 'INTERRUPTED'" title="Interrupted" small style="color: #f44336; margin-left:13px;">fas fa-exclamation</v-icon>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="dialog" persistent max-width="768px">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">Delete Environments</v-toolbar-title>
        </v-toolbar>
        <v-card-text>
          <v-container style="padding:0px 10px 0px 10px">
            <v-layout wrap>
              <v-flex xs12 style="padding-bottom:10px">
                <div class="subtitle-1">Are you sure you want to delete the selected deployments?</div>
              </v-flex>
              <v-btn :loading="loading" color="success" @click="deleteDeploySubmit()">Confirm</v-btn>
              <v-btn :disabled="loading" color="error" @click="dialog=false" style="margin-left:10px;">Cancel</v-btn>
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

    // Inline Editing: Environment Name
    inline_editing: '',

    // Dialog: Delete Environments
    dialog: false,

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
      const path = this.$store.getters.url + '/deployments'
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
    open(item) {
      this.inline_editing = item.name
    },
    save(item) {
      if (this.inline_editing == item.name) {
        this.notification('Deployment edited successfully', 'success')
        return
      }
      this.loading = true
      // Edit environment name in the DB
      const path = this.$store.getters.url + '/deployments'
      const payload = {
        id: item.id,
        name: this.inline_editing
      }
      axios.put(path, payload)
        .then((response) => {
          this.notification(response.data.message, 'success')
          // Reload Deployments Data
          this.getDeployments()
        })
        .catch((error) => {
          if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
          // eslint-disable-next-line
          console.error(error)
        }) 
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
    getStatusColor (status) {
      if (status == 'CREATED') return '#bdc3c7'
      else if (status == 'QUEUED') return '#3498db'
      else if (status == 'IN PROGRESS') return '#ff9800'
      else if (status == 'SUCCESS') return '#4caf50'
      else if (status == 'FAILED') return '#f44336'
      else if (status == 'INTERRUPTED') return '#bf55ec'
      else return '#fff'
    },
    newDeploy() {
      this.$router.push({name:'deployments.new'})
    },
    infoDeploy() {
      this.$router.push({ name:'deployments.info', params: { deploymentID: this.selected[0]['id'] }})
    },
    progressDeploy() {
      this.$router.push({ name:'deployments.progress', params: { deploymentID: this.selected[0]['id'] }})
    },
    deleteDeploy() {
      this.dialog = true
    },
    deleteDeploySubmit() {
      // Get Selected Items
      var payload = []
      for (var i = 0; i < this.selected.length; ++i) payload.push(this.selected[i]['id'])
      // Delete items to the DB
      const path = this.$store.getters.url + '/deployments'
      axios.delete(path, { data: payload })
        .then((response) => {
          this.notification(response.data.message, 'success')
          // Reload Deployments Data
          this.getDeployments()
          this.selected = []
        })
        .catch((error) => {
          if (error.response.status === 401) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
          // eslint-disable-next-line
          console.error(error)
        })
        .finally(() => {
          this.loading = false
          this.dialog = false
        })
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  }
}
</script>