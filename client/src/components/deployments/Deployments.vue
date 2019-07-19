<template>
  <div>
    <v-toolbar dark color="primary">
      <v-toolbar-title class="white--text">DEPLOYMENTS</v-toolbar-title>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-toolbar-items class="hidden-sm-and-down">
        <v-btn flat @click='newDeploy()'><v-icon style="padding-right:10px">fas fa-plus-circle</v-icon>NEW</v-btn>
      </v-toolbar-items>
    </v-toolbar>
    <v-card>
      <v-card-title style="padding-top:0px;">
        <v-text-field v-model="search" append-icon="search" label="Search" single-line hide-details></v-text-field>
      </v-card-title>
      <v-data-table :headers="headers" :items="data" :search="search">
        <template v-slot:items="props">
          <td>
            <v-edit-dialog :return-value.sync="props.item.name" lazy @save="save"> 
              {{ props.item.name }}
              <template v-slot:input>
                <v-text-field v-model="props.item.name" label="Edit" single-line></v-text-field>
              </template>
            </v-edit-dialog>
          </td>

          <td>{{ props.item.environment }}</td>
          <td class="text-xs-center"><v-chip label :color="getModeColor(props.item.mode)" dark>{{ props.item.mode }}</v-chip></td>
          <td class="text-xs-center"><v-chip label :color="getStatusColor(props.item.status)" dark>{{ props.item.status }}</v-chip></td>
          <td>{{ props.item.started }}</td>
          <td>{{ props.item.ended }}</td>
          <td>{{ props.item.time }}</td>
          <td>
            <router-link class="nav-link" :to="{ name: 'deployments.info', params: { deploymentID: props.item.id } }">
              <v-icon small style="padding:10px;">fas fa-info</v-icon>
            </router-link>
            <a :href="props.item.logs" target="_blank">
              <v-icon small @click="logs(props.item)" style="padding:10px;">fas fa-meteor</v-icon>
            </a>
          </td>
        </template>
        <template v-slot:no-results>
          <v-alert :value="true" color="error" icon="warning">
            Your search for "{{ search }}" found no results.
          </v-alert>
        </template>
      </v-data-table>
    </v-card>

    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn color="white" flat @click="snackbar = false">Close</v-btn>
    </v-snackbar>
  </div>
</template>

<script>
import axios from 'axios';

export default {
  data: () => ({
    headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Environment', value: 'environment' },
      { text: 'Mode', align: 'center', value: 'mode' },
      { text: 'Status', align:'center', value: 'status' },
      { text: 'Started', align: 'left', value: 'started' },
      { text: 'Ended', align: 'left', value: 'ended' },
      { text: 'Overall Time', value: 'time' },
      { text: 'Actions', value: 'actions' }
    ],
    data: [
      {
        id: 1,
        name: 'Release 3.33.0',
        environment: 'Production',
        mode: 'DEPLOYMENT',
        status: 'SUCCESS',
        started: '2019-07-07 08:00:00',
        ended: '2019-07-07 08:12:15',
        time: '12m 15s',
        logs: 'https://dba.inbenta.me/meteor/?uri=24a5bd97-4fae-4868-b960-2b30b3b184f4'
      }
    ],
    search: '',
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  methods: {
    save() {
      this.notification('Deployment edited successfully', 'success')
    },
    logs() {

    },
    getModeColor (mode) {
      if (mode == 'DEPLOYMENT') return 'red'
      else if (mode == 'TEST') return 'orange'
      else if (mode == 'VALIDATION') return 'green'
    },
    getStatusColor (status) {
      if (status == 'FAILED') return 'red'
      else if (status == 'WARNINGS') return 'orange'
      else if (status == 'SUCCESS') return 'green'
    },
    newDeploy() {
      this.$router.push({name:'deployments.new'})
    },
    getDeployments() {
      const path = 'http://34.242.255.177:5000/deployments';
      axios.get(path)
        .then((res) => {
          this.books = res.data.books;
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
        });
    },
    addDeployment(payload) {
      const path = 'http://34.242.255.177:5000/deployments';
      axios.post(path, payload)
        .then(() => {
          this.getDeployments();
          this.message = 'Book added!';
          this.showMessage = true;
        })
        .catch((error) => {
          // eslint-disable-next-line
          this.getDeployments();
        });
    },
    updateDeployment(payload, deploymentID) {
      const path = `http://34.242.255.177:5000/deployments/${deploymentID}`;
      axios.put(path, payload)
        .then(() => {
          this.getDeployments();
          this.message = 'Book updated!';
          this.showMessage = true;
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
          this.getDeployments();
        });
    },
    removeDeployment(deploymentID) {
      const path = `http://34.242.255.177:5000/deployments/${deploymentID}`;
      axios.delete(path)
        .then(() => {
          this.getDeployments();
          this.message = 'Book removed!';
          this.showMessage = true;
        })
        .catch((error) => {
          // eslint-disable-next-line
          console.error(error);
          this.getDeployments();
        });
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  },
  created() {
    // this.getDeployments();
  }
}
</script>