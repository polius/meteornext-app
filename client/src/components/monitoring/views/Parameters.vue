<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title class="white--text">PARAMETERS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items class="hidden-sm-and-down">
          <v-btn text title="Settings" ><v-icon small style="padding-right:10px">fas fa-cog</v-icon>SETTINGS</v-btn>
        </v-toolbar-items>
        <v-text-field v-model="search" append-icon="search" label="Search" color="white" style="margin-left:10px;" single-line hide-details></v-text-field>
      </v-toolbar>
      <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" :hide-default-footer="items.length < 11" :loading="loading" loading-text="Loading... Please wait" item-key="id" show-select class="elevation-1" style="padding-top:5px;">
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
      { text: 'Variables', align: 'left', value: 'variables' },
      { text: 'Templates EU', align: 'left', value: '1' },
      { text: 'Templates US', align: 'left', value: '2' },
      { text: 'Templates JP', align: 'left', value: '3' }
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