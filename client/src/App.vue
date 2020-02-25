<template>
  <v-app dark>
    <v-app-bar clipped-left app absolute v-show="isLoggedIn && showTopNavbar()">
      <router-link class="nav-link white--text" to="/" style="text-decoration:none;">
        <v-toolbar-title>Meteor Next</v-toolbar-title>
      </router-link>

      <!-- DEPLOYMENTS -->
      <v-divider class="mx-3" inset vertical></v-divider>
      <router-link v-if="deployments_enable" class="nav-link" to="/deployments">
        <v-btn color="#e74c3c"><v-icon small style="padding-right:10px">fas fa-meteor</v-icon>Deployments</v-btn>
      </router-link>
      <!-- MONITORING -->
      <router-link class="nav-link" to="/monitoring" style="margin-left:10px;">
        <v-btn color="#fa8231"><v-icon small style="padding-right:10px">fas fa-desktop</v-icon>Monitoring</v-btn>
      </router-link>
      <!-- VALIDATION -->
      <router-link class="nav-link" to="/utils" style="margin-left:10px;">
        <v-btn color="#00b16a"><v-icon small style="padding-right:10px">fas fa-database</v-icon>Utils</v-btn>
      </router-link>      
      <!-- #446cb3 -->
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

      <!-- ADMINISTRATION -->
      <router-link v-if="admin" title="Administration" class="nav-link" to="/admin">
        <v-btn icon><v-icon>fas fa-ankh</v-icon></v-btn>
      </router-link>

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
          <v-list-item :title="notification['name']" @click="openNotification(notification)">
            <v-list-item-action style="margin-right:10px;">
              <v-icon small :title="notification.status.charAt(0).toUpperCase() + notification.status.slice(1).toLowerCase()" :color="notification['status'].toLowerCase()">{{ notification['icon'] }}</v-icon>
            </v-list-item-action>
            <v-list-item-content>
              <v-list-item-title>{{ notification['name'] }}</v-list-item-title>
              <v-list-item-subtitle>{{ parseDate(notification['date']) }}</v-list-item-subtitle>
            </v-list-item-content>
          </v-list-item>
          <v-divider></v-divider>
        </div>
        <v-btn v-if="notifications.length > 0" block large text title="Clear all notifications" @click="clearNotifications()">CLEAR</v-btn>
      </v-list>
    </v-navigation-drawer>

    <!-- NOTIFICATIONS Snackbar -->
    <v-snackbar v-model="snackbar" :timeout="snackbarTimeout" :color="snackbarColor" top>
      {{ snackbarText }}
      <v-btn color="white" text @click="snackbar = false">Close</v-btn>
    </v-snackbar>

    <!-- FOOTER -->
    <!--
    <v-footer app v-if="isLoggedIn && showBottomNavbar()" style="height:30px;">
      <span class="px-3"></span>
    </v-footer>
    -->
  </v-app>
</template>

<style>
a { text-decoration: none; }
html { overflow-y: auto!important; }
</style>

<script>
import axios from 'axios'
import moment from 'moment'

export default {
  data: () => ({
    rightDrawer: false,
    notifications: [],
    loading: false,

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarText: '',
    snackbarColor: ''
  }),
  computed : {
    isLoggedIn : function() { return this.$store.getters.isLoggedIn },
    admin : function() { return this.$store.getters.admin },
    coins : function() { return this.$store.getters.coins },
    deployments_enable : function() { return this.$store.getters.deployments_enable }
  },
  created() {
    this.getNotifications(true)
  },
  methods: {
    logout() {
      this.$store.dispatch('logout').then(() => this.$router.push('/login'))
    },
    showTopNavbar() {
      if (!window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/results')) return true
      return false
    },
    showBottomNavbar() {
      if (window.location.pathname != '/login' && !window.location.pathname.startsWith('/results') && window.location.pathname != '/deployments/information') return true
      return false
    },
    openNotifications() {
      this.rightDrawer = !this.rightDrawer
    },
    openNotification(notification) {
      // Go to the selected resource
      const data = JSON.parse(notification.data)
      this.$router.push({ name:'deployment', params: { id: data.mode.substring(0, 1) + data.id }})

      // Remove notification from notifications bar
      const payload = JSON.stringify({ id: notification.id })
      axios.put('/notifications', payload)
        .then(() => {
          for (var i = 0; i < this.notifications.length; ++i) {
            if (this.notifications[i]['id'] == notification['id']) {
              this.notifications.splice(i, 1)
              break
            }
          }
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
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
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
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
            // if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
            // else this.notification(error.response.data.message, 'error')
          })
          .finally(() => {
            this.loading = false
            if (recurrent) setTimeout(this.getNotifications, 60000, true)
          })
      }
    },
    getCoins() {

    },
    parseDate(date) {
      return moment.utc(date).local().format('ddd, DD MMM YYYY HH:mm:ss')
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  }
}
</script>