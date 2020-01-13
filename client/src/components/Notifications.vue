<template>
  <v-container fluid>
    <v-content>
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">NOTIFICATIONS</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-toolbar-items class="hidden-sm-and-down">
            <v-btn v-if="selected.length == 1" text @click="openNotification()"><v-icon small style="padding-right:10px">fas fa-envelope-open</v-icon>OPEN</v-btn>
            <v-btn v-if="selected.length > 0" text @click="deleteNotification()"><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
          </v-toolbar-items>
          <v-text-field v-model="search" append-icon="search" label="Search" color="white" style="margin-left:10px;" single-line hide-details></v-text-field>
        </v-toolbar>
        <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="name" show-select class="elevation-1" style="padding-top:3px;">
          <template v-slot:item.name="props">
            <span><v-icon small :color="props.item.status" :title="props.item.status.charAt(0).toUpperCase() + props.item.status.slice(1)" style="margin-bottom:2px; margin-right:15px;">fas fa-circle</v-icon>{{ props.item.name }}</span>
          </template>
          <template v-slot:item.date="props">
            <span>{{ dateFormat(props.item.date) }}</span>
          </template>
        </v-data-table>
      </v-card>

      <v-dialog v-model="openDialog" max-width="40%">
        <v-card>
          <v-toolbar flat color="primary">
            <v-toolbar-title class="white--text">NOTIFICATION</v-toolbar-title>
            <v-spacer></v-spacer>
            <v-btn icon @click="openDialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
          </v-toolbar>
          <v-card-text style="padding: 15px 20px 20px;">
            <v-container style="padding:0px; max-width:100%;">
              <v-layout wrap>
                <v-flex xs12>
                  <v-card>
                    <v-toolbar flat dense color="#2e3131">
                      <v-toolbar-title class="body-1"><v-icon small :color="item['status']" style="margin-bottom:2px; margin-right:15px;">fas fa-circle</v-icon>{{ this.item['name'] }}</v-toolbar-title>
                      <v-spacer></v-spacer>
                      <v-btn icon @click="openNotificationSubmit()"><v-icon small title="Go to the resource">fas fa-arrow-right</v-icon></v-btn>
                    </v-toolbar>
                  </v-card>
                  <div v-if="this.item.category == 'deployments' && 'data' in this.item" style="padding:5px;">
                    <div class="headline font-weight-regular" style="margin-top:12px; margin-bottom:12px;">{{ item.data.mode.toUpperCase() }}</div>
                    <v-text-field v-model="item.data.name" readonly label="Name"></v-text-field>
                    <v-text-field v-model="item.data.environment" readonly label="Environment" style="padding-top:0px;"></v-text-field>
                    <v-text-field v-model="item.data.overall" readonly label="Overall" style="padding-top:0px; margin-bottom:5px;" hide-details></v-text-field>
                  </div>
                </v-flex>
              </v-layout>
            </v-container>
          </v-card-text>
        </v-card>
      </v-dialog>

      <v-dialog v-model="deleteDialog" persistent max-width="768px">
        <v-card>
          <v-toolbar flat color="primary">
            <v-toolbar-title class="white--text">Delete Notifications</v-toolbar-title>
          </v-toolbar>
          <v-card-text style="padding: 0px 20px 0px;">
            <v-container style="padding:0px">
              <v-layout wrap>
                <v-flex xs12>
                  <v-form ref="form" style="margin-top:15px; margin-bottom:20px;">
                    <div style="padding-bottom:10px" class="subtitle-1">Are you sure you want to delete the selected notifications?</div>
                    <v-divider></v-divider>
                    <div style="margin-top:20px;">
                      <v-btn :loading="loading" color="success" @click="deleteNotificationSubmit()">CONFIRM</v-btn>
                      <v-btn :disabled="loading" color="error" @click="deleteDialog=false" style="margin-left:5px;">CANCEL</v-btn>
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
    </v-content>
  </v-container>
</template>

<script>
import axios from 'axios'
import moment from 'moment'

export default {
  data: () => ({
    // Data Table
    headers: [
      { text: 'Name', align: 'left', value: 'name' },
      { text: 'Date', align: 'left', value: 'date' }
    ],
    items: [],
    selected: [],
    search: '',
    loading: true,
    openDialog: false,
    deleteDialog: false,
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  created() {
    this.getNotifications()
  },
  methods: {
    getNotifications() {
      axios.get('/notifications')
        .then((response) => {
          this.items = response.data.data
          for (var i = 0; i < this.items.length; ++i) this.items[i]['data'] = JSON.parse(this.items[i]['data'])
          this.loading = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    openNotification() {
      this.openDialog = true
    },
    openNotificationSubmit() {
      const id = this.selected[0]['mode'].substring(0, 1) + this.selected[0]['id']
      this.$router.push({ name:'deployment', params: { id: id }})
    },
    deleteNotification() {
      this.deleteDialog = true
    },
    deleteNotificationSubmit() {
      // Get Selected Items
      var payload = []
      for (var i = 0; i < this.selected.length; ++i) payload.push(this.selected[i]['id'])
      // Delete items to the DB
      axios.delete('/notifications', { data: payload })
        .then((response) => {
          this.notification(response.data.message, 'success')
          // Delete items from the data table
          while(this.selected.length > 0) {
            var s = this.selected.pop()
            for (var i = 0; i < this.items.length; ++i) {
              if (this.items[i]['name'] == s['name']) {
                // Delete Item
                this.items.splice(i, 1)
                break
              }
            }
          }
          this.selected = []
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
          this.deleteDialog = false
        })
    },
    dateFormat(date) {
      if (date) return moment(date).format("YYYY-MM-DD HH:mm:ss") // + ' UTC'
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