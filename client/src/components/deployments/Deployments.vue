<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title class="white--text">DEPLOYMENTS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text @click='newDeploy()'><v-icon small style="padding-right:10px">fas fa-plus</v-icon>NEW</v-btn>
        </v-toolbar-items>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" style="margin-left:10px;" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table :headers="headers" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="id" class="elevation-1" style="padding-top:5px;">
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
          <span :style="'color: ' + getMethodColor(props.item.method)"><b>{{ props.item.method }}</b></span>
        </template>
        <template v-slot:item.status="props">
          <span :style="'color: ' + getStatusColor(props.item.status)">{{ props.item.status }}</span>
        </template>
        <template v-slot:item.actions="props">
          <!-- <v-btn title="Starred" icon small><v-icon small>far fa-star</v-icon></v-btn> -->
          <router-link title="Information" class="nav-link" :to="{ name: 'deployments.info', params: { deploymentID: props.item.id } }">
            <v-btn icon small style="margin-left:-10px;"><v-icon small>fas fa-info</v-icon></v-btn>
          </router-link>
          <a :href="props.item.results" target="_blank" title="Results">
            <v-btn icon small @click="results(props.item)"><v-icon small>fas fa-meteor</v-icon></v-btn>
          </a>
          <a :href="props.item.logs" target="_blank" title="Raw Logs">
            <v-btn icon small @click="logs(props.item)"><v-icon small>fas fa-cloud-download-alt</v-icon></v-btn>
          </a>
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
      { text: 'Environment', align: 'left', value: 'environment' },
      { text: 'Mode', align: 'left', value: 'mode' },
      { text: 'Method', align: 'left', value: 'method' },
      { text: 'Status', align:'left', value: 'status' },
      { text: 'Started', align: 'left', value: 'started' },
      { text: 'Ended', align: 'left', value: 'ended' },
      { text: 'Actions', align: 'left', value: 'actions' }
    ],
    items: [],
    search: '',
    loading: true,

    // Inline Editing: Environment Name
    inline_editing: '',

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
      if (status == 'FAILED') return '#f44336'
      else if (status == 'IN PROGRESS') return '#ff9800'
      else if (status == 'SUCCESS') return '#4caf50'
      else return '#fff'
    },
    newDeploy() {
      this.$router.push({name:'deployments.new'})
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  }
}
</script>