<template>
  <div>
    <v-toolbar dark color="primary">
      <v-toolbar-title class="white--text">QUERIES</v-toolbar-title>
      <v-spacer></v-spacer>
      <div class="subheadline">Updated: <b>2019-07-22 10:22:05</b></div>
    </v-toolbar>

    <v-card>
      <v-card-title style="padding-top:0px">
        <v-text-field v-model="search" append-icon="search" label="Search" single-line hide-details></v-text-field>
      </v-card-title>
      <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" item-key="id" class="elevation-1">
        <template v-slot:items="props">
          <td>{{ props.item.query }}</td>
          <td>{{ props.item.database }}</td>
          <td>{{ props.item.server }}</td>
          <td>{{ props.item.user }}</td>
          <td>{{ props.item.host }}</td>
          <td>{{ props.item.seen }}</td>
          <td>{{ props.item.time }}</td>
        </template>
        <template v-slot:no-results>
          <v-alert :value="true" color="error" icon="warning">
            Your search for "{{ search }}" found no results.
          </v-alert>
        </template>
      </v-data-table>
    </v-card>

    <v-dialog v-model="itemDialog" persistent max-width="768px">
      <v-toolbar dark color="primary">
        <v-toolbar-title class="white--text">{{ itemDialogTitle }}</v-toolbar-title>
      </v-toolbar>
      <v-card>
        <v-card-text>
          <v-container style="padding:0px 10px 0px 10px">
            <v-layout wrap>
              <v-flex xs12 v-if="mode!='delete'">
                <v-text-field ref="field" v-model="item.name" label="Environment Name" required></v-text-field>
              </v-flex>
              <v-flex xs12 style="padding-bottom:10px" v-if="mode=='delete'">
                <div class="subheading">Are you sure you want to delete the selected environments?</div>
              </v-flex>
              <v-btn color="success" dark style="margin-left:0px">Confirm</v-btn>
              <v-btn color="error" @click="itemDialog=false" dark style="margin-left:0px">Cancel</v-btn>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>

    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn color="white" flat @click="snackbar = false">Close</v-btn>
    </v-snackbar>
  </div>
</template>

<script>
// import axios from 'axios'

export default {
  data: () => ({
    // Data Table
    headers: [
      { text: 'Query', align: 'left', value: 'query' },
      { text: 'Database', align: 'left', value: 'database' },
      { text: 'Server', align: 'left', value: 'server' },
      { text: 'User', align: 'left', value: 'user' },
      { text: 'Host', align: 'left', value: 'host' },
      { text: 'Seen', align: 'left', value: 'seen' },
      { text: 'Time', align: 'left', value: 'time' }
    ],
    items: [
      { 
        query: "SELECT COUNT(*) AS n FROM t_ticket_archive WHERE id_responsible='0'",
        database: "ilf_sky_tickets",
        server: "awseu-sql03",
        user: "ilf",
        host: "localhost",
        seen: "2019-07-17 11:23:52",
        time: 158
      }
    ],
    selected: [],
    search: '',
    // Item
    item: { name: '' },
    // Action Mode (new, edit, delete)
    mode: '',
    // Dialog: Item
    itemDialog: false,
    itemDialogTitle: '',
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  methods: {
  },
  created() {
  }
}
</script>