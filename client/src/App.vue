<template>
  <v-app>
    <v-app-bar clipped-left app absolute v-show="isLoggedIn && showTopNavbar()">
      <router-link class="nav-link white--text" to="/" style="text-decoration:none;">
        <v-toolbar-title>Meteor Next</v-toolbar-title>
      </router-link>
      <v-divider class="mx-3" inset vertical></v-divider>
      <!-- DEPLOYMENTS -->
      <router-link v-if="deployments_enabled" class="nav-link" to="/deployments" style="margin-right:10px;">
        <v-btn color="#e74c3c"><v-icon small style="padding-right:10px">fas fa-meteor</v-icon>Deployments</v-btn>
      </router-link>
      <!-- MONITORING -->
      <router-link v-if="monitoring_enabled" class="nav-link" to="/monitoring" style="margin-right:10px;">
        <v-btn color="#fa8231"><v-icon small style="padding-right:10px">fas fa-desktop</v-icon>Monitoring</v-btn>
      </router-link>
      <!-- UTILS -->
      <router-link v-if="utils_enabled" class="nav-link" to="/utils" style="margin-right:10px;">
        <v-btn color="#00b16a"><v-icon small style="padding-right:10px">fas fa-database</v-icon>Utils</v-btn>
      </router-link>
      <!-- CLIENT -->
      <router-link v-if="client_enabled" class="nav-link" to="/client">
        <v-btn color="#8e44ad"><v-icon small style="padding-right:10px">fas fa-bolt</v-icon>Client</v-btn>
      </router-link>
      <v-spacer></v-spacer>
      <!-- COINS -->
      <v-chip @click="getCoins()" class="subtitle-1 font-weight-medium" style="margin-right:5px;">
        {{ coins }} Coins
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-icon small color="#ffcb05">fas fa-coins</v-icon>
      </v-chip>
      <!-- NOTIFICATIONS BAR -->
      <div>
        <v-tooltip>
          <!-- eslint-disable-next-line -->
          <template v-slot:activator="{ on }">
            <v-btn icon @click.stop="openNotifications()" title="Notifications">
              <v-badge v-if="notifications.length > 0" color="red" overlap>
                <span slot="badge">{{ notifications.length }}</span>
                <v-icon>fas fa-bell</v-icon>
              </v-badge>
              <v-icon v-else>fas fa-bell</v-icon>
            </v-btn>
          </template>
        </v-tooltip>
      </div>
      <!-- PROFILE -->
      <router-link title="Profile" class="nav-link" to="/profile">
        <v-btn icon><v-icon>fas fa-user</v-icon></v-btn>
      </router-link>
      <!-- INVENTORY -->
      <router-link v-if="inventory_enabled" title="Inventory" class="nav-link" to="/inventory">
        <v-btn icon><v-icon>fas fa-layer-group</v-icon></v-btn>
      </router-link>
      <!-- VIEWER -->
      <router-link title="Viewer" class="nav-link" to="/viewer" target="_blank">
        <v-btn icon><v-icon>fas fa-chart-area</v-icon></v-btn>
      </router-link>
      <!-- ADMINISTRATION -->
      <router-link v-if="admin" title="Administration" class="nav-link" to="/admin">
        <v-btn icon><v-icon>fas fa-ankh</v-icon></v-btn>
      </router-link>
      <!-- FULL SCREEN -->
      <v-btn icon :title="fullScreenEnabled ? 'Exit Full Screen' : 'Full Screen'" @click="fullScreen">
        <v-icon>{{ fullScreenEnabled ? 'fas fa-compress' : 'fas fa-expand' }}</v-icon>
      </v-btn>
      <!-- LOGOUT -->
      <v-btn icon title="Logout" @click="logout()">
        <v-icon>fas fa-sign-out-alt</v-icon>
      </v-btn>
    </v-app-bar>
    <router-view/>
    <v-navigation-drawer temporary right v-model="rightDrawer" fixed app style="width:320px;">
      <v-toolbar flat class="primary">
        <v-toolbar-title>Notifications</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn icon title="See all notifications" @click.stop="notificationsSubmit()"><v-icon small>fas fa-bars</v-icon></v-btn>
        <v-btn :disabled="loading" icon title="Refresh" @click.stop="notificationsRefresh()"><v-icon>refresh</v-icon></v-btn>
        <v-btn icon title="Close" @click.stop="rightDrawer = false"><v-icon>close</v-icon></v-btn>
      </v-toolbar>
      <v-progress-linear v-if="loading" indeterminate></v-progress-linear>
      <v-list :disabled="loading" subheader dense>
        <v-subheader v-if="notifications.length == 0" class="justify-center">No Notifications</v-subheader>
        <v-subheader v-else>New notifications</v-subheader>
        <div v-for="notification in notifications" :key="notification['id']">
          <v-list-item :title="notification['name']" @click="openNotification(notification)" style="padding-left:0px">
            <div :style="`margin-right:20px; height:51px; width:5px; background-color:` + getStatusColor(notification['status'])"></div>
            <v-list-item-content>
              <v-list-item-title v-if="notification['category'] == 'deployment'"><v-icon small title="Deployment" color="#fa8231" style="padding-right:5px;">fas fa-meteor</v-icon> {{ notification['name'] }}</v-list-item-title>
              <v-list-item-title v-else-if="notification['category'] == 'monitoring'"><v-icon small title="Monitoring" color="#fa8231" style="padding-right:5px;">fas fa-desktop</v-icon> {{ notification['name'] }}</v-list-item-title>
              <v-list-item-subtitle>{{ parseDate(notification['date']) }}</v-list-item-subtitle>
            </v-list-item-content>
          </v-list-item>
          <v-divider></v-divider>
        </div>
        <v-btn v-if="notifications.length > 0" block large text title="Clear all notifications" @click="clearNotifications()">CLEAR</v-btn>
      </v-list>
    </v-navigation-drawer>
    <!-- NOTIFICATIONS Snackbar -->
    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
    <!----------->
    <!-- COINS -->
    <!----------->
    <v-dialog v-model="coinsDialog" max-width="360px">
      <v-card>
        <v-card-text style="padding:10px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-row justify="space-around" style="margin-top:0px">
                  <v-avatar size="130"><i class="fas fa-coins fa-7x" style="color:#ffcb05"></i></v-avatar>
                </v-row>
                <v-row justify="space-around" style="margin-top:20px; margin-bottom:15px;">
                  <div class="text-h5" style="font-weight:400;">{{ coins + ' Coins' }}</div>
                </v-row>
                <v-row justify="space-around" style="margin-top:0px">
                  <div class="text-subtitle-1" style="font-weight:400">{{ "1 Deployment = " + this.coins_execution + " Coins" }}</div>
                </v-row>
                <v-row justify="space-around" style="margin-top:20px; margin-bottom:15px">
                  <div class="text-subtitle-1" style="font-weight:400;">{{ "+" + this.coins_day + " Coins / Day" }}</div>
                </v-row>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn @click="coinsDialog = false" color="primary">Close</v-btn>
                    </v-col>
                  </v-row>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
  </v-app>
</template>

<style>
a { text-decoration: none; }
html { overflow-y: auto!important; }

::-webkit-scrollbar {
  -webkit-appearance: none;
  width: 15px;
  background-color: #4f4d56;
}
::-webkit-scrollbar-track {
  background: #4f4d56;
}
::-webkit-scrollbar-thumb {
  min-height: 25px;
  background: #373540;
  border: 3px solid transparent;
  border-radius: 10px;
  background-clip: content-box;
}
::-webkit-scrollbar-corner {
  background: #373540;
}
</style>

<script>
import axios from 'axios'
import moment from 'moment'

export default {
  data: () => ({
    rightDrawer: false,
    notifications: [],
    loading: false,
    fullScreenEnabled: false,
    coinsDialog: false,

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  computed: {
    isLoggedIn: function() { return this.$store.getters['app/isLoggedIn'] },
    admin: function() { return this.$store.getters['app/admin'] == 0 ? false : this.$store.getters['app/admin'] },
    coins: function() { return this.$store.getters['app/coins'] },
    inventory_enabled: function() { return this.$store.getters['app/inventory_enabled'] },
    deployments_enabled: function() { return this.$store.getters['app/deployments_enabled'] },
    monitoring_enabled: function() { return this.$store.getters['app/monitoring_enabled'] },
    utils_enabled: function() { return this.$store.getters['app/utils_enabled'] },
    client_enabled: function() { return this.$store.getters['app/client_enabled'] },
    coins_execution: function() { return this.$store.getters['app/coins_execution'] },
    coins_day: function() { return this.$store.getters['app/coins_day'] },
  },
  created() {
    this.getNotifications(true)
  },
  methods: {
    fullScreen() {
      if (this.fullScreenEnabled) {
        document.exitFullscreen()
        .catch(() => {})
        .finally(() => this.fullScreenEnabled = false)
      }
      else {
        document.body.requestFullscreen()
        .catch(() => this.notification('This browser does not support full screen', 'error'))
        .finally(() => this.fullScreenEnabled = true)
      }
    },
    logout() {
      this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
    },
    showTopNavbar() {
      if (!window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/viewer')) return true
      return false
    },
    showBottomNavbar() {
      if (window.location.pathname != '/login' && !window.location.pathname.startsWith('/viewer') && window.location.pathname != '/deployments/information') return true
      return false
    },
    openNotifications() {
      this.rightDrawer = !this.rightDrawer
    },
    openNotification(notification) {
      // Remove notification from notifications bar
      const payload = { id: notification.id }
      axios.put('/notifications', payload)
        .then(() => {
          for (var i = 0; i < this.notifications.length; ++i) {
            if (this.notifications[i]['id'] == notification['id']) {
              this.notifications.splice(i, 1)
              break
            }
          }
          // Go to the selected resource
          const data = JSON.parse(notification.data)
          if (notification.category == 'deployment') {
            this.$router.push({ name: 'deployment', params: { id: data.mode.substring(0, 1) + data.id }})
          }
          else if (notification.category == 'monitoring') {
            this.$router.push({ name: 'monitor', params: { id:  data.id }})
          }
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    clearNotifications() {
      axios.delete('/notifications/clear')
        .then((response) => {
          this.notifications = []
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    notificationsSubmit() {
      if (window.location.pathname != '/notifications') this.$router.push('/notifications')
      else this.rightDrawer = false
    },
    notificationsRefresh() {
      this.loading = true
      this.getNotifications(false)
    },
    getNotifications(recurrent) {
      if (recurrent && (!this.isLoggedIn || this.rightDrawer)) setTimeout(this.getNotifications, 1000, true)
      else {
        axios.get('/notifications/bar')
          .then((response) => {
            this.notifications = response.data.data
          })
          .catch(() => {
            // if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
            // else this.notification(error.response.data.message, 'error')
          })
          .finally(() => {
            this.loading = false
            if (recurrent) setTimeout(this.getNotifications, 60000, true)
          })
      }
    },
    getCoins() {
      this.coinsDialog = true
    },
    parseDate(date) {
      return moment.utc(date).local().format('ddd, DD MMM YYYY HH:mm:ss')
    },
    getStatusColor(status) {
      if (status == 'SUCCESS') return '#4caf50'
      else if (status == 'WARNING') return '#ff9800'
      else if (status == 'ERROR') return '#e74c3c'
      else if (status == 'INFO') return '#3e9cef'
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