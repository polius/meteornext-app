<template>
  <v-main>
    <div>
      <v-tabs background-color="#323133" color="white" v-model="tabs" slider-color="white" slot="extension" class="elevation-2">
        <v-tab disabled to="/admin" style="opacity:1"><span class="pl-2 pr-2 white--text"><v-icon small style="padding-right:10px">fas fa-ankh</v-icon>ADMINISTRATION</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-tab to="/admin/settings"><span class="pl-2 pr-2">Settings</span></v-tab>
        <v-tab to="/admin/users"><span class="pl-2 pr-2">Users</span></v-tab>
        <v-tab to="/admin/groups"><span class="pl-2 pr-2">Groups</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-tab to="/admin/inventory" title="Manage all inventories"><span class="pl-2 pr-2">Inventory</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-tab to="/admin/deployments" title="Manage all deployments"><span class="pl-2 pr-2">Deployments</span></v-tab>
        <v-tab to="/admin/monitoring" title="Manage all monitoring"><span class="pl-2 pr-2">Monitoring</span></v-tab>
        <!-- <v-tab to="/admin/utils" title="Manage all utils"><span class="pl-2 pr-2">Utils</span></v-tab> -->
        <v-tab to="/admin/client" title="Manage all client queries and servers"><span class="pl-2 pr-2">Client</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
      </v-tabs>
    </div>
    <v-container fluid style="padding:10px!important">
      <v-main style="padding-top:0px;">
        <v-slide-y-transition mode="out-in">
          <router-view/>
        </v-slide-y-transition>
      </v-main>
    </v-container>
    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>      
  </v-main>
</template>

<script>
import EventBus from './js/event-bus'

export default {
  data() {
    return {
      tabs: null,
      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarText: '',
      snackbarColor: ''
    }
  },
  mounted() {
    EventBus.$on('send-notification', this.notification)
  },
  methods: {
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    },
  }
}
</script>