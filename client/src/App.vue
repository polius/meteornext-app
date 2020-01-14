<template>
  <v-app dark>
    <v-app-bar clipped-left app absolute v-show="isLoggedIn && showTopNavbar()">
      <router-link class="nav-link white--text" to="/" style="text-decoration:none;">
        <v-toolbar-title>Meteor Next</v-toolbar-title>
      </router-link>

      <!-- DEPLOYMENTS -->
      <v-divider class="mx-3" inset vertical></v-divider>
      <router-link v-if="deployments_enable" class="nav-link" to="/deployments">
        <v-btn color="success"><v-icon small style="padding-right:10px">fas fa-meteor</v-icon>Deployments</v-btn>
      </router-link>
      <!-- VALIDATION -->
      <router-link class="nav-link" to="/validation" style="margin-left:10px;">
        <v-btn color="orange"><v-icon small style="padding-right:10px">fas fa-check</v-icon>Validation</v-btn>
      </router-link>
      <!-- MONITORING -->
      <router-link class="nav-link" to="/monitoring" style="margin-left:10px;">
        <v-btn color="red"><v-icon small style="padding-right:10px">fas fa-desktop</v-icon>Monitoring</v-btn>
      </router-link>

      <v-spacer></v-spacer>

      <!-- COINS -->
      <v-chip @click="getCoins()" class="subtitle-1 font-weight-medium" style="margin-right:5px;">
        {{ coins }} Coins
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-icon small color="#ffcb05">fas fa-coins</v-icon>
      </v-chip>

      <!-- NOTIFICATIONS -->
      <div>
        <v-tooltip>
          <template v-slot:activator="{ on }">
            <v-btn icon @click.stop="openNotifications()" title="Notifications">
              <v-badge color="red" overlap>
                <span v-if="notifications.length != 0" slot="badge">{{ notifications.length }}</span>
                <v-icon>fas fa-bell</v-icon>
              </v-badge>
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
        <v-subheader>New notifications</v-subheader>
        <div v-for="notification in notifications" :key="notification['id']">
          <v-list-item @click="removeNotification(notification)">
            <v-list-item-action style="margin-right:10px;">
              <v-icon small :color="notification['status'].toLowerCase()">{{ notification['icon'] }}</v-icon>
            </v-list-item-action>
            <v-list-item-content>
              <v-list-item-title>{{ notification['name'] }}</v-list-item-title>
              <v-list-item-subtitle>{{ parseDate(notification['date']) }}</v-list-item-subtitle>
            </v-list-item-content>
          </v-list-item>
          <v-divider v-if="notifications[notifications.length-1]['id'] != notification['id']"></v-divider>
        </div>
      </v-list>
    </v-navigation-drawer>
    <!--
      <v-list-item @click="removeNotification()">
        <v-list-item-action>
          <v-icon>person_add</v-icon>
        </v-list-item-action>
        <v-list-item-title>
          12 new users registered
        </v-list-item-title>
      </v-list-item>
      </div>
      <v-divider></v-divider>
      <v-list-item>
        <v-list-item-action>
          <v-icon>data_usage</v-icon>
        </v-list-item-action>
        <v-list-item-title>
          DB overloaded 80%
        </v-list-item-title>
      </v-list-item>
    -->

    <!-- <v-footer app v-if="isLoggedIn && showBottomNavbar()" style="height:30px;">
      <span class="px-3"></span>
    </v-footer> -->
  </v-app>
</template>

<style>
a { text-decoration: none; }
</style>

<script>
import axios from 'axios'
import moment from 'moment'

export default {
  data: () => ({
    rightDrawer: false,
    notifications: [],
    loading: false
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
    removeNotification(notification) {
      const payload = { id: notification['id'] }
      axios.put('/notifications', payload)
        .then(() => {
          this.getNotifications(false)
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message, 'error')
        })
    },
    getCoins() {

    },
    parseDate(date) {
      return moment(date).local().format('ddd, DD MMM YYYY HH:mm:ss')
    }
  }
}
</script>