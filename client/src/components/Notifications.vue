<template>
  <v-container fluid>
    <v-main>
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="padding-right:10px; padding-bottom:3px">fas fa-bell</v-icon>NOTIFICATIONS</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-toolbar-items class="hidden-sm-and-down">
            <v-btn v-if="selected.length == 1" text @click="openNotification()"><v-icon small style="padding-right:10px">fas fa-envelope-open</v-icon>OPEN</v-btn>
            <v-btn v-if="selected.length > 0" text @click="deleteNotification()"><v-icon small style="padding-right:10px">fas fa-minus</v-icon>DELETE</v-btn>
          </v-toolbar-items>
          <v-text-field v-model="search" append-icon="search" label="Search" color="white" style="margin-left:10px;" single-line hide-details></v-text-field>
        </v-toolbar>
        <v-data-table v-model="selected" :headers="headers" :items="items" :search="search" :loading="loading" loading-text="Loading... Please wait" item-key="id" show-select class="elevation-1" style="padding-top:3px;">
          <template v-slot:[`item.name`]="{ item }">
            <span><v-icon small :color="item.status.toLowerCase()" :title="item.status.charAt(0).toUpperCase() + item.status.slice(1).toLowerCase()" style="margin-bottom:2px; margin-right:15px;">fas fa-circle</v-icon>{{ item.name }}</span>
          </template>
          <template v-slot:[`item.category`]="{ item }">
            <v-icon v-if="item.category == 'deployment'" small color="#e74c3c" :title="item.category.charAt(0).toUpperCase() + item.category.slice(1)" style="margin-left:14px;">fas fa-meteor</v-icon>
            <v-icon v-if="item.category == 'monitoring'" small color="#fa8231" :title="item.category.charAt(0).toUpperCase() + item.category.slice(1)" style="margin-left:14px;">fas fa-desktop</v-icon>
          </template>
          <template v-slot:[`item.date`]="{ item }">
            <span>{{ dateFormat(item.date) }}</span>
          </template>
          <template v-slot:[`item.show`]="{ item }">
            <v-btn icon small @click="changeSeen(item)">
              <v-icon small :title="item.show ? 'Show in the notification bar' : 'Don\'t show in the notification bar'" :color="item.show ? '#00b16a' : 'error'">fas fa-circle</v-icon>
            </v-btn>
          </template>
        </v-data-table>
      </v-card>

      <v-dialog v-model="openDialog" max-width="640px">
        <v-card>
          <v-toolbar flat color="primary">
            <v-toolbar-title class="white--text">NOTIFICATION</v-toolbar-title>
            <v-spacer></v-spacer>
            <v-btn icon @click="openDialog = false"><v-icon>fas fa-times-circle</v-icon></v-btn>
          </v-toolbar>
          <v-card-text style="padding:15px">
            <v-container style="padding:0px; max-width:100%;">
              <v-layout wrap>
                <v-flex xs12>
                  <v-card>
                    <v-toolbar flat dense color="#2e3131">
                      <v-toolbar-title class="body-1"><v-icon v-if="openDialog" small :color="item.status.toLowerCase()" style="margin-bottom:2px; margin-right:15px;">fas fa-circle</v-icon>{{ this.item['name'] }}</v-toolbar-title>
                      <v-spacer></v-spacer>
                      <v-btn icon @click="openNotificationSubmit()"><v-icon small title="Go to the resource">fas fa-arrow-right</v-icon></v-btn>
                    </v-toolbar>
                  </v-card>
                  <div v-if="this.item.category == 'deployment'" style="padding:5px;">
                    <div class="headline font-weight-regular" style="margin-top:12px; margin-bottom:12px;">{{ item.data.mode.toUpperCase() }}</div>
                    <v-text-field v-model="item.data.name" readonly label="Name"></v-text-field>
                    <v-text-field v-model="item.data.environment" readonly label="Environment" style="padding-top:0px;"></v-text-field>
                    <v-text-field v-model="item.data.overall" readonly label="Overall" style="padding-top:0px; margin-bottom:5px;" hide-details></v-text-field>
                    <v-radio-group v-model="item.data.method" style="margin-top:15px;" readonly hide-details>
                      <v-radio :value="item.data.method" :color="getDeploymentMethodColor(item)">
                        <template v-slot:label>
                          <div :class="`${getDeploymentMethodColor(item)}--text`">{{ item.data.method }}</div>
                        </template>
                      </v-radio>
                    </v-radio-group>
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
                      <v-btn :loading="loading" color="#00b16a" @click="deleteNotificationSubmit()">CONFIRM</v-btn>
                      <v-btn :disabled="loading" color="error" @click="deleteDialog=false" style="margin-left:5px;">CANCEL</v-btn>
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
      { text: 'Show', align: 'left', value: 'show' }
    ],
    items: [],
    item: {},
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
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    openNotification() {
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
      this.openDialog = true
    },
    openNotificationSubmit() {
      if (this.item.category == 'deployments') {
        const id = this.item.data.mode.substring(0, 1) + this.item.data.id
        this.$router.push({ name:'deployment', params: { id: id }})
      }
      else if (this.item.category == 'monitoring') {
        const id = this.item.data.id
        this.$router.push({ name:'monitor', params: { id: id }})
      }
    },
    editNotification() {
      this.item = JSON.parse(JSON.stringify(this.selected[0]))
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
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
          this.deleteDialog = false
        })
    },
    changeSeen(item) {
      // Add item in the DB
      const payload = { id: item.id }
      axios.put('/notifications', payload)
        .then(() => {
          this.getNotifications()
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    dateFormat(date) {
      if (date) return moment.utc(date).local().format('ddd, DD MMM YYYY HH:mm:ss')
      return date
    },
    getDeploymentMethodColor(item) {
      if (item.data.method == 'VALIDATE') return '#00b16a'
      else if (item.data.method == 'TEST') return 'orange'
      else if (item.data.method == 'DEPLOY') return 'red'
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