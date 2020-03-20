<template>
  <div>
    <v-card style="margin-bottom:15px;">
      <v-toolbar flat dense color="#292929">
        <v-toolbar-title class="subtitle-1">Templates EU</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" style="margin-left:10px; margin-bottom:2px;" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table :headers="headers" :items="items" :search="search" :hide-default-footer="items.length < 11" class="elevation-1" style="padding-top:3px;">
      </v-data-table>
    </v-card>

    <v-card style="margin-bottom:15px;">
      <v-toolbar flat dense color="#292929">
        <v-toolbar-title class="subtitle-1">Templates US</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" style="margin-left:10px; margin-bottom:2px;" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table :headers="headers" :items="items" :search="search" :hide-default-footer="items.length < 11" class="elevation-1" style="padding-top:3px;">
      </v-data-table>
    </v-card>

    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn color="white" text @click="snackbar = false">Close</v-btn>
    </v-snackbar>
  </div>
</template>

<script>
// import axios from 'axios'

export default {
  data: () => ({
    // Data Table
    headers: [
        { text: 'Id', align: 'left', value: 'id' },
        { text: 'User', align: 'left', value: 'user' },
        { text: 'Host', align: 'left', value: 'host' },
        { text: 'db', align: 'left', value: 'db' },
        { text: 'Command', align: 'left', value: 'command' },
        { text: 'Time', align: 'left', value: 'time' },
        { text: 'State', align: 'left', value: 'state' },
        { text: 'Info', align: 'left', value: 'info' }
    ],
    items: [],
    selected: [],
    search: '',
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  created() {
    this.getProcesslist()
  },
  methods: {
    getProcesslist() {
    //   axios.get('/monitoring/processlist')
    //     .then((response) => {
    //       this.items = response.data.data
    //       this.loading = false
    //     })
    //     .catch((error) => {
    //       if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
    //       else this.notification(error.response.data.message, 'error')
    //     })
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  }
}
</script>