<template>
  <v-app style="overflow-x:auto">
    <v-app-bar app absolute v-show="isLoggedIn && showTopNavbar()" height="64">
      <router-link class="nav-link white--text" to="/" style="text-decoration:none;">
        <v-toolbar-title>Meteor Next</v-toolbar-title>
      </router-link>
      <v-divider class="mx-3" inset vertical></v-divider>
      <!-- DEPLOYMENTS -->
      <v-btn @click="() => $router.push('/deployments').catch(() => {})" :disabled="!deployments_enabled" color="#EF5354" style="margin-right:10px"><v-icon small style="margin-right:10px">fas fa-meteor</v-icon>Deployments</v-btn>
      <!-- MONITORING -->
      <v-btn @click="() => $router.push('/monitoring').catch(() => {})" :disabled="!monitoring_enabled" color="#fa8231" style="margin-right:10px"><v-icon small style="margin-right:10px">fas fa-desktop</v-icon>Monitoring</v-btn>
      <!-- UTILS -->
      <v-btn @click="() => $router.push('/utils').catch(() => {})" :disabled="!utils_enabled" color="#00b16a" style="margin-right:10px"><v-icon small style="margin-right:10px">fas fa-database</v-icon>Utils</v-btn>
      <!-- CLIENT -->
      <v-btn @click="() => $router.push('/client').catch(() => {})" :disabled="!client_enabled" color="#8e44ad" style="margin-right:10px"><v-icon small style="margin-right:10px">fas fa-bolt</v-icon>Client</v-btn>
      <!-- VAULT -->
      <!-- <v-btn @click="() => $router.push('/vault').catch(() => {})" color="#1b72f5" style="margin-right:10px"><v-icon small style="margin-right:10px">fas fa-dice-d6</v-icon>Vault</v-btn> -->
      <!-- COINS -->
      <v-spacer></v-spacer>
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
              <v-badge v-if="notifications.length > 0" color="#EF5354" overlap>
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
      <!-- DATA VIEWER -->
      <router-link title="Data Viewer" class="nav-link" to="/viewer" target="_blank">
        <v-btn icon><v-icon>fas fa-chart-area</v-icon></v-btn>
      </router-link>
      <!-- ADMINISTRATION -->
      <router-link v-if="admin" title="Administration" class="nav-link" to="/admin">
        <v-btn icon><v-icon>fas fa-ankh</v-icon></v-btn>
      </router-link>
      <!-- DOCUMENTATION -->
      <a href="https://docs.meteornext.io" target="_blank" title="Documentation">
        <v-btn icon><v-icon style="font-size:22px">fas fa-question</v-icon></v-btn>
      </a>
      <!-- FULL SCREEN -->
      <v-btn icon :title="fullScreenEnabled ? 'Exit Full Screen' : 'Full Screen'" @click="fullScreen">
        <v-icon>{{ fullScreenEnabled ? 'fas fa-compress' : 'fas fa-expand' }}</v-icon>
      </v-btn>
      <!-- LOGOUT -->
      <v-btn icon title="Logout" @click="logout()">
        <v-icon>fas fa-sign-out-alt</v-icon>
      </v-btn>
    </v-app-bar>
    <keep-alive>
      <router-view v-if="$route.meta.keepAlive"/>
    </keep-alive>
    <router-view v-if="!$route.meta.keepAlive"/>
    <v-navigation-drawer temporary right v-model="rightDrawer" fixed app style="width:380px">
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
        <v-subheader v-else>{{ `New notifications (${notifications.length})` }}</v-subheader>
        <div v-for="notification in notifications" :key="notification['id']">
          <v-list-item :title="notification['name']" @click="openNotification(notification)" style="padding-left:0px">
            <div :style="`margin-right:15px; height:51px; width:5px; background-color:` + getStatusColor(notification['status'])"></div>
            <v-list-item-content>
              <v-list-item-title v-if="notification['category'] == 'deployment'"><v-icon small title="Deployment" color="#EF5354" style="margin-right:10px; margin-bottom:2px">fas fa-meteor</v-icon>{{ notification['name'] }}</v-list-item-title>
              <v-list-item-title v-else-if="notification['category'] == 'monitoring'"><v-icon small title="Monitoring" color="#fa8231" style="margin-right:10px; margin-bottom:2px">fas fa-desktop</v-icon>{{ notification['name'] }}</v-list-item-title>
              <v-list-item-title v-else-if="notification['category'] == 'utils-import'"><v-icon small title="Utils - Import" color="#00b16a" style="margin-right:10px; margin-bottom:2px">fas fa-arrow-up</v-icon>{{ notification['name'] }}</v-list-item-title>
              <v-list-item-title v-else-if="notification['category'] == 'utils-export'"><v-icon small title="Utils - Export" color="#00b16a" style="margin-right:10px; margin-bottom:2px">fas fa-arrow-down</v-icon>{{ notification['name'] }}</v-list-item-title>
              <v-list-item-title v-else-if="notification['category'] == 'utils-clone'"><v-icon small title="Utils - Clone" color="#00b16a" style="margin-right:10px; margin-bottom:2px">fas fa-clone</v-icon>{{ notification['name'] }}</v-list-item-title>
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
    <v-dialog v-model="coinsDialog" max-width="384px">
      <v-card>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12>
                <div style="text-align:center; margin:10px">
                  <v-icon size="70" color="#ffcb05">fas fa-coins</v-icon>
                </div>
                <div class="text-h5 white--text" style="margin:20px; text-align:center; font-weight:400;">{{ coins + ' Coins' }}</div>
                <v-divider></v-divider>
                <div class="text-subtitle-1" style="text-align:center; margin-top:15px; font-weight:400">{{ "1 Deployment = " + this.deployments_coins + " Coins" }}</div>
                <div class="text-subtitle-1" style="text-align:center; margin-top:10px; margin-bottom:5px; font-weight:400">{{ "1 Import / Export / Clone = " + this.utils_coins + " Coins" }}</div>
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
body { background: #303030; }

/* Dark Scrollbar */
.dark_scrollbar::-webkit-scrollbar {
  -webkit-appearance: none;
  width: 15px;
  background-color: #424242;
}
.dark_scrollbar::-webkit-scrollbar-track {
  background: #424242;
}
.dark_scrollbar::-webkit-scrollbar-thumb {
  min-height: 25px;
  background: #303030;
  border: 3px solid transparent;
  border-radius: 10px;
  background-clip: content-box;
}
.dark_scrollbar::-webkit-scrollbar-corner {
  background: #303030;
}
::-webkit-scrollbar {
  -webkit-appearance: none;
  width: 15px;
  background-color: #424242;
}
::-webkit-scrollbar-track {
  background: #424242;
}
::-webkit-scrollbar-thumb {
  min-height: 25px;
  background:  #303030;
  border: 3px solid transparent;
  border-radius: 10px;
  background-clip: content-box;
}
::-webkit-scrollbar-corner {
  background: #303030 ;
}
</style>

<style src="@/fonts/roboto.css"></style>
<style src="@/fonts/materialicons.css"></style>

<script>
// Scrollbar - Firefox
document.documentElement.style.setProperty('scrollbar-color', '#303030 #424242');
// Scrollbar - Chrome
document.documentElement.classList.add("dark_scrollbar");
import axios from 'axios'
import moment from 'moment'

export default {
  data: () => ({
    rightDrawer: false,
    notifications: [],
    loading: false,
    fullScreenEnabled: false,
    coinsDialog: false,
    activeSession: true,

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(1000),
    snackbarText: '',
    snackbarColor: ''
  }),
  computed: {
    isLoggedIn: function() { return this.$store.getters['app/isLoggedIn'] },
    admin: function() { return this.$store.getters['app/admin'] == 0 ? false : this.$store.getters['app/admin'] },
    coins: function() { return this.$store.getters['app/coins'] },
    coins_day: function() { return this.$store.getters['app/coins_day'] },
    inventory_enabled: function() { return this.$store.getters['app/inventory_enabled'] },
    deployments_enabled: function() { return this.$store.getters['app/deployments_enabled'] },
    monitoring_enabled: function() { return this.$store.getters['app/monitoring_enabled'] },
    utils_enabled: function() { return this.$store.getters['app/utils_enabled'] },
    client_enabled: function() { return this.$store.getters['app/client_enabled'] },
    deployments_coins: function() { return this.$store.getters['app/deployments_coins'] },
    utils_coins: function() { return this.$store.getters['app/utils_coins'] },
  },
  created() {
    this.getNotifications(true)
  },
  mounted() {
    this.checkStyle()
  },
  watch: {
    isLoggedIn(value) {
      this.activeSession = value
      this.checkStyle()
    }
  },
  methods: {
    checkStyle() {
      var element = document.getElementsByClassName('v-application--wrap');
      if (element.length > 0) {
        if (this.$store.getters['app/isLoggedIn']) element[0].style.minWidth = 'max(calc(100vw - 20px),1280px)'
        else element[0].style.minWidth = ''
      }
    },
    fullScreen() {
      if (!this.fullScreenEnabled) {
        if (document.documentElement.requestFullscreen) document.documentElement.requestFullscreen().catch(() => {})
        else if (document.documentElement.mozRequestFullScreen) document.documentElement.mozRequestFullScreen().catch(() => {})
        else if (document.documentElement.webkitRequestFullscreen) document.documentElement.webkitRequestFullscreen().catch(() => {})
        else if (document.documentElement.msRequestFullscreen) document.documentElement.msRequestFullscreen().catch(() => {})
      }
      else {
        if (document.exitFullscreen) document.exitFullscreen().catch(() => {})
        else if (document.mozCancelFullScreen) document.mozCancelFullScreen().catch(() => {})
        else if (document.webkitExitFullscreen) document.webkitExitFullscreen().catch(() => {})
      }
      this.fullScreenEnabled = !this.fullScreenEnabled
    },
    logout() {
      this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
    },
    showTopNavbar() {
      if (!window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/viewer') && !window.location.pathname.startsWith('/results') && !window.location.pathname.startsWith('/install')) return true
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
            if (this.$router.history.current.name != 'deployment' || this.$router.history.current.params.uri != data.id) {
              this.$router.push({ name: 'deployments.execution', params: { uri: data.id }})
            }
          }
          else if (notification.category == 'monitoring') {
            if (this.$router.history.current.name != 'monitor' || this.$router.history.current.params.id != data.id) {
              this.$router.push({ name: 'monitor', params: { id:  data.id }})
            }
          }
          else if (notification.category == 'utils-import') {
            if (this.$router.history.current.name != 'utils.imports.info' || this.$router.history.current.params.uri != data.uri) {
              this.$router.push({ name: 'utils.imports.info', params: { uri:  data.id }})
            }
          }
          else if (notification.category == 'utils-export') {
            if (this.$router.history.current.name != 'utils.exports.info' || this.$router.history.current.params.uri != data.uri) {
              this.$router.push({ name: 'utils.exports.info', params: { uri:  data.id }})
            }
          }
          else if (notification.category == 'utils-clone') {
            if (this.$router.history.current.name != 'utils.clones.info' || this.$router.history.current.params.uri != data.uri) {
              this.$router.push({ name: 'utils.clones.info', params: { uri:  data.id }})
            }
          }
          this.rightDrawer = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, '#EF5354')
        })
    },
    clearNotifications() {
      axios.delete('/notifications/clear')
        .then((response) => {
          this.notifications = []
          this.notification(response.data.message, '#00b16a')
          this.rightDrawer = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, '#EF5354')
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
      if (recurrent && (!this.isLoggedIn || !this.activeSession || this.rightDrawer)) setTimeout(this.getNotifications, 1000, true)
      else {
        axios.get('/notifications/bar')
          .then((response) => {
            this.notifications = response.data.data
          })
          .catch((error) => {
            if (error.response.status == 401) this.activeSession = false
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
      return moment.utc(date).local().format("YYYY-MM-DD HH:mm:ss")
    },
    getStatusColor(status) {
      if (status == 'SUCCESS') return '#4caf50'
      else if (status == 'WARNING') return '#ff9800'
      else if (status == 'ERROR') return '#EF5354'
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