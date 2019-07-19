<template>
  <v-app dark>
    <v-toolbar clipped-left app absolute v-show="$router.history.current.path != '/login'">
      <router-link class="nav-link white--text" to="/" style="text-decoration:none;">
        <v-toolbar-title>Meteor Next</v-toolbar-title>
      </router-link>

      <!-- DEPLOYMENTS -->
      <v-divider class="mx-3" inset vertical></v-divider>
      <router-link class="nav-link" to="/deployments">
        <v-btn color="success"><v-icon small style="padding-right:10px">fas fa-meteor</v-icon>Deployments</v-btn>
      </router-link>
      <!-- VALIDATION -->
      <router-link class="nav-link" to="/validation">
        <v-btn color="orange"><v-icon small style="padding-right:10px">fas fa-check</v-icon>SQL Validation</v-btn>
      </router-link>
      <!-- MONITORING -->
      <router-link class="nav-link" to="/monitoring">
        <v-btn color="red"><v-icon small style="padding-right:10px">fas fa-desktop</v-icon>Monitoring</v-btn>
      </router-link>

      <v-spacer></v-spacer>

      <!-- NOTIFICATIONSS -->
      <v-tooltip bottom>
        <v-btn icon @click.stop="rightDrawer = !rightDrawer" slot="activator">
          <v-badge color="red" overlap>
            <span slot="badge">2</span>
            <v-icon>fas fa-bell</v-icon>
          </v-badge>
        </v-btn>
        <span>2 unread notifications</span>
      </v-tooltip>

      <!-- PROFILE -->
      <router-link title="Profile" class="nav-link" to="/profile">
        <v-btn icon><v-icon>fas fa-user</v-icon></v-btn>
      </router-link>

      <!-- ADMINISTRATION -->
      <router-link title="Administration" class="nav-link" to="/admin">
        <v-btn icon><v-icon>fas fa-ankh</v-icon></v-btn>
      </router-link>

      <!-- LOGOUT -->
      <router-link title="Logout" class="nav-link" to="/login">
        <v-btn icon>
          <v-icon>fas fa-sign-out-alt</v-icon>
        </v-btn>
      </router-link>
    </v-toolbar>

    <router-view/>

    <v-navigation-drawer temporary right v-model="rightDrawer" fixed app>
      <v-toolbar flat prominent dark class="primary">
        <v-toolbar-title>Notifications</v-toolbar-title>
        <v-spacer></v-spacer>
        <v-btn icon @click.stop="rightDrawer = false">
          <v-icon>close</v-icon>
        </v-btn>
      </v-toolbar>
      <v-list subheader dense>
        <v-subheader>All notifications</v-subheader>
        <v-list-tile @click="">
          <v-list-tile-action>
            <v-icon>person_add</v-icon>
          </v-list-tile-action>
          <v-list-tile-title>
            12 new users registered
          </v-list-tile-title>
        </v-list-tile>
        <v-divider></v-divider>
        <v-list-tile @click="">
          <v-list-tile-action>
            <v-icon>data_usage</v-icon>
          </v-list-tile-action>
          <v-list-tile-title>
            DB overloaded 80%
          </v-list-tile-title>
        </v-list-tile>
      </v-list>
    </v-navigation-drawer>

    <v-footer app v-show="$router.history.current.path != '/login'">
      <span class="px-3"></span>
    </v-footer>
  </v-app>
</template>

<script>
import axios from 'axios';

export default {
  data: () => ({
    rightDrawer: false
  })
}
</script>