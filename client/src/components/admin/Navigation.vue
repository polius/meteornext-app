<template>
  <v-main>
    <div>
      <v-tabs @change="changeTab" background-color="#323133" color="white" v-model="tab" slider-color="white" slot="extension" class="elevation-2">
        <v-tab disabled style="opacity:1"><span class="pl-2 pr-2 white--text"><v-icon small style="padding-right:10px">fas fa-ankh</v-icon>ADMINISTRATION</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-tab title="Manage all settings"><span class="pl-2 pr-2">Settings</span></v-tab>
        <v-tab title="Manage all users"><span class="pl-2 pr-2">Users</span></v-tab>
        <v-tab title="Manage all groups"><span class="pl-2 pr-2">Groups</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-tab title="Manage all inventories"><span class="pl-2 pr-2">Inventory</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-tab title="Manage all deployments"><span class="pl-2 pr-2">Deployments</span></v-tab>
        <v-tab title="Manage all monitored servers"><span class="pl-2 pr-2">Monitoring</span></v-tab>
        <v-tab title="Manage all utils"><span class="pl-2 pr-2">Utils</span></v-tab>
        <v-tab title="Manage all client queries and servers"><span class="pl-2 pr-2">Client</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
      </v-tabs>
    </div>
    <v-container fluid style="padding:10px!important">
      <v-main style="padding-top:0px;">
        <router-view/>
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
      tab: 1,
      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarText: '',
      snackbarColor: ''
    }
  },
  created() {
    if (this.$route.path.startsWith('/admin/settings')) this.tab = 1
    else if (this.$route.path.startsWith('/admin/users')) this.tab = 2
    else if (this.$route.path.startsWith('/admin/groups')) this.tab = 3
    else if (this.$route.path.startsWith('/admin/inventory')) this.tab = 4
    else if (this.$route.path.startsWith('/admin/deployments')) this.tab = 5
    else if (this.$route.path.startsWith('/admin/monitoring')) this.tab = 6
    else if (this.$route.path.startsWith('/admin/utils')) this.tab = 7
    else if (this.$route.path.startsWith('/admin/client')) this.tab = 8
  },
  mounted() {
    EventBus.$on('send-notification', this.notification)
  },
  destroyed() {
    EventBus.$off()
  },
  methods: {
    changeTab(val) {
      if (val == 1) this.$router.push("/admin/settings")
      else if (val == 2) this.$router.push("/admin/users")
      else if (val == 3) this.$router.push("/admin/groups")
      else if (val == 4) this.$router.push("/admin/inventory")
      else if (val == 5) this.$router.push("/admin/deployments")
      else if (val == 6) this.$router.push("/admin/monitoring")
      else if (val == 7) this.$router.push("/admin/utils")
      else if (val == 8) this.$router.push("/admin/client")
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    },
  }
}
</script>