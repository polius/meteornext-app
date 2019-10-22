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

      <!-- NOTIFICATIONSS -->
      <v-tooltip bottom>
        <template v-slot:activator="{ on }">
          <v-btn icon @click.stop="rightDrawer = !rightDrawer" slot="activator">
            <v-badge color="red" overlap>
              <span slot="badge">2</span>
              <v-icon>fas fa-bell</v-icon>
            </v-badge>
          </v-btn>
        </template>
        <span>2 unread notifications</span>
      </v-tooltip>

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

    <v-navigation-drawer temporary right v-model="rightDrawer" fixed app>
      <v-toolbar flat class="primary">
        <v-toolbar-title>Notifications</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn icon @click.stop="rightDrawer = false">
          <v-icon>close</v-icon>
        </v-btn>
      </v-toolbar>
      <v-list subheader dense>
        <v-subheader>All notifications</v-subheader>
        <v-list-item>
          <v-list-item-action>
            <v-icon>person_add</v-icon>
          </v-list-item-action>
          <v-list-item-title>
            12 new users registered
          </v-list-item-title>
        </v-list-item>
        <v-divider></v-divider>
        <v-list-item>
          <v-list-item-action>
            <v-icon>data_usage</v-icon>
          </v-list-item-action>
          <v-list-item-title>
            DB overloaded 80%
          </v-list-item-title>
        </v-list-item>
      </v-list>
    </v-navigation-drawer>

    <v-footer app v-if="isLoggedIn && showBottomNavbar()" style="height:30px;">
      <span class="px-3"></span>
    </v-footer>
  </v-app>
</template>

<style>
a { text-decoration: none; }
</style>

<script>
export default {
  data: () => ({
    rightDrawer: false
  }),
  computed : {
    isLoggedIn : function(){ return this.$store.getters.isLoggedIn },
    admin : function(){ return this.$store.getters.admin },
    deployments_enable : function(){ return this.$store.getters.deployments_enable }
  },
  methods: {
    logout() {
      this.$store.dispatch('logout').then(() => this.$router.push('/login'))
    },
    showTopNavbar() {
      if (!window.location.pathname.startsWith('/login') && !window.location.pathname.startsWith('/results')) return true
      return false
      // console.log(this.$router.history.current.path)
      // console.log(window.location.pathname)
    },
    showBottomNavbar() {
      if (window.location.pathname != '/login' && !window.location.pathname.startsWith('/results') && window.location.pathname != '/deployments/information') return true
      return false
    }
  }
}
</script>