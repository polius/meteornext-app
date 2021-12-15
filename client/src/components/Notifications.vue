<template>
  <v-container fluid style="padding:10px!important">
    <v-main>
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:3px">fas fa-bell</v-icon>NOTIFICATIONS</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-toolbar-items>
            <v-btn :disabled="selected.length != 1" text @click="infoNotification()"><v-icon small style="margin-right:10px">fas fa-info</v-icon>INFORMATION</v-btn>
            <v-btn :disabled="selected.length == 0" text @click="deleteNotification()"><v-icon small style="margin-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
            <v-divider class="mx-3" inset vertical></v-divider>
          </v-toolbar-items>
          <v-text-field v-model="search" append-icon="search" label="Search" color="white" single-line hide-details></v-text-field>
        </v-toolbar>
        <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="id" show-select class="elevation-1" style="padding-top:3px;" mobile-breakpoint="0">
          <template v-ripple v-slot:[`header.data-table-select`]="{}">
            <v-simple-checkbox
              :value="items.length == 0 ? false : selected.length == items.length"
              :indeterminate="selected.length > 0 && selected.length != items.length"
              @click="selected.length == items.length ? selected = [] : selected = [...items]">
            </v-simple-checkbox>
          </template>
          <template v-slot:[`item.name`]="{ item }">
            <v-row no-gutters align="center" style="height:100%">
              <v-col cols="auto" :style="`width:4px; height:100%; margin-right:10px; background-color:` + getNotificationColor(item.status)">
              </v-col>
              <v-col cols="auto">
                {{ item.name }}
              </v-col>
            </v-row>
          </template>
          <template v-slot:[`item.category`]="{ item }">
            <div v-if="item.category == 'deployment'"><v-icon small color="#EF5354" title="Deployments" style="margin-right:10px">fas fa-meteor</v-icon>Deployments</div>
            <div v-else-if="item.category == 'monitoring'"><v-icon small color="#fa8231" title="Monitoring" style="margin-right:10px">fas fa-desktop</v-icon>Monitoring</div>
            <div v-else-if="item.category == 'utils-restore'"><v-icon small color="#00b16a" title="Utils - Restore" style="margin-right:10px">fas fa-database</v-icon>Utils - Restore</div>
          </template>
          <template v-slot:[`item.date`]="{ item }">
            {{ dateFormat(item.date) }}
          </template>
          <template v-slot:[`item.show`]="{ item }">
            <v-btn icon small @click="changeSeen(item)">
              <v-icon :title="item.show ? 'Show in the notification bar' : 'Don\'t show in the notification bar'" :color="item.show ? '#00b16a' : '#EF5354'" small>fas fa-circle</v-icon>
            </v-btn>
          </template>
        </v-data-table>
      </v-card>

      <v-dialog v-model="deleteDialog" persistent max-width="768px">
        <v-card>
          <v-toolbar dense flat color="primary">
            <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-minus</v-icon>DELETE NOTIFICATIONS</v-toolbar-title>
          </v-toolbar>
          <v-card-text style="padding: 0px 15px 0px;">
            <v-container style="padding:0px">
              <v-layout wrap>
                <v-flex xs12>
                  <v-form ref="form" style="margin-top:15px; margin-bottom:15px;">
                    <div style="padding-bottom:10px" class="subtitle-1">Are you sure you want to delete the selected notifications?</div>
                    <v-divider></v-divider>
                    <div style="margin-top:20px;">
                      <v-btn :loading="loading" color="#00b16a" @click="deleteNotificationSubmit()">CONFIRM</v-btn>
                      <v-btn :disabled="loading" color="#EF5354" @click="deleteDialog=false" style="margin-left:5px;">CANCEL</v-btn>
                    </div>
                  </v-form>
                </v-flex>
              </v-layout>
            </v-container>
          </v-card-text>
        </v-card>
      </v-dialog>

      <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
    </v-main>
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
      { text: 'Category', align: 'left', value: 'category' },
      { text: 'Date', align: 'left', value: 'date' },
      { text: 'Visible', align: 'left', value: 'show' }
    ],
    items: [],
    selected: [],
    search: '',
    loading: true,
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
          this.items = []
          this.$nextTick(() => {
            this.items = response.data.data
            for (let i = 0; i < this.items.length; ++i) this.items[i]['data'] = JSON.parse(this.items[i]['data'])
          })
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    infoNotification() {
      const id = this.selected[0].data.id
      if (this.selected[0].category == 'deployment') {
        this.$router.push({ name: 'deployments.execution', params: { uri: id }})
      }
      else if (this.selected[0].category == 'monitoring') {
        this.$router.push({ name: 'monitor', params: { id: id }})
      }
      else if (this.selected[0].category == 'utils-restore') {
        this.$router.push({ name: 'utils.restore.info', params: { id: id }})
      }
    },
    deleteNotification() {
      this.deleteDialog = true
    },
    deleteNotificationSubmit() {
      // Get Selected Items
      var payload = []
      for (var i = 0; i < this.selected.length; ++i) payload.push(this.selected[i]['id'])
      // Delete items to the DB
      this.loading = true
      axios.delete('/notifications', { data: payload })
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
          // Delete items from the data table
          while(this.selected.length > 0) {
            var s = this.selected.pop()
            for (var i = 0; i < this.items.length; ++i) {
              if (this.items[i]['id'] == s['id']) {
                // Delete Item
                this.items.splice(i, 1)
                break
              }
            }
          }
          this.selected = []
          this.deleteDialog = false
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    changeSeen(item) {
      // Add item in the DB
      const payload = { id: item.id }
      axios.put('/notifications', payload)
        .then(() => {
          this.getNotifications()
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    dateFormat(date) {
      if (date) return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
      return date
    },
    getNotificationColor(status) {
      if (status == 'SUCCESS') return '#4caf50'
      else if (status == 'WARNING') return '#ff9800'
      else if (status == 'ERROR') return '#EF5354'
      else if (status == 'INFO') return '#3e9cef'
      else return ''
    },
    getDeploymentMethodColor(item) {
      if (item.data.method == 'VALIDATE') return '#00b16a'
      else if (item.data.method == 'TEST') return 'orange'
      else if (item.data.method == 'DEPLOY') return '#EF5354'
      return ''
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  }
}
</script>