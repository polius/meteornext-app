<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="body-2 white--text font-weight-medium" style="font-size:0.95rem!important">SETTINGS</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-toolbar-items style="padding-left:0px;">
          <v-btn text @click="changeTab('license')" :style="{ backgroundColor : mode == 'license' ? '#489ff0' : '' }"><v-icon small style="margin-right:10px">fas fa-certificate</v-icon>LICENSE</v-btn>
          <v-btn text @click="changeTab('sql')" :style="{ backgroundColor : mode == 'sql' ? '#489ff0' : '' }"><v-icon small style="margin-right:10px">fas fa-database</v-icon>SQL</v-btn>
          <v-btn text @click="changeTab('files')" :style="{ backgroundColor : mode == 'files' ? '#489ff0' : '' }"><v-icon small style="margin-right:10px">fas fa-folder-open</v-icon>FILES</v-btn>
          <v-btn text @click="changeTab('amazon')" :style="{ backgroundColor : mode == 'amazon' ? '#489ff0' : '' }"><v-icon style="font-size:20px; margin-right:10px; margin-top:3px">fab fa-aws</v-icon>AMAZON S3</v-btn>
          <v-btn text @click="changeTab('security')" :style="{ backgroundColor : mode == 'security' ? '#489ff0' : '' }"><v-icon small style="margin-right:10px">fas fa-shield-alt</v-icon>SECURITY</v-btn>
          <v-btn text @click="changeTab('advanced')" :style="{ backgroundColor : mode == 'advanced' ? '#489ff0' : '' }"><v-icon small style="margin-right:10px">fas fa-cog</v-icon>ADVANCED</v-btn>
        </v-toolbar-items>
      </v-toolbar>
      <v-container fluid grid-list-lg>
        <v-layout row wrap>
          <License v-if="mode == 'license'" :info="settings.license" :init="loading"/>
          <SQL v-else-if="mode == 'sql'" :info="settings.sql" :init="loading"/>
          <Files v-else-if="mode == 'files'" :info="settings.files" :init="loading"/>
          <Amazon v-else-if="mode == 'amazon'" :info="settings.amazon" :init="loading"/>
          <Security v-else-if="mode == 'security'" :info="settings.security" :init="loading"/>
          <Advanced v-else-if="mode == 'advanced'" :info="settings.advanced" :init="loading"/>
        </v-layout>
      </v-container>
    </v-card>
    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<script>
import axios from 'axios'
import License from './settings/License'
import SQL from './settings/SQL'
import Files from './settings/Files'
import Amazon from './settings/Amazon'
import Security from './settings/Security'
import Advanced from './settings/Advanced'

export default {
  data: () => ({
    // Settings
    settings: { license: {}, sql: {}, files: {}, amazon: {}, security: {}, advanced: {}},
    mode: 'license',
    loading: true,

    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarColor: '',
    snackbarText: ''
  }),
  components: { License, SQL, Files, Amazon, Security, Advanced },
  created() {
    this.getSettings()
    if (this.$route.path.startsWith('/admin/settings/license')) this.mode = 'license'
    else if (this.$route.path.startsWith('/admin/settings/sql')) this.mode = 'sql'
    else if (this.$route.path.startsWith('/admin/settings/files')) this.mode = 'files'
    else if (this.$route.path.startsWith('/admin/settings/amazon')) this.mode = 'amazon'
    else if (this.$route.path.startsWith('/admin/settings/security')) this.mode = 'security'
    else if (this.$route.path.startsWith('/admin/settings/advanced')) this.mode = 'advanced'
    else this.$router.push('/admin/settings/license')
  },
  methods: {
    changeTab(val) {
      if (val == 'license' && this.$route.path != '/admin/settings/license') this.$router.push('/admin/settings/license')
      else if (val == 'sql' && this.$route.path != '/admin/settings/sql') this.$router.push('/admin/settings/sql')
      else if (val == 'files' && this.$route.path != '/admin/settings/files') this.$router.push('/admin/settings/files')
      else if (val == 'amazon' && this.$route.path != '/admin/settings/amazon') this.$router.push('/admin/settings/amazon')
      else if (val == 'security' && this.$route.path != '/admin/settings/security') this.$router.push('/admin/settings/security')
      else if (val == 'advanced' && this.$route.path != '/admin/settings/advanced') this.$router.push('/admin/settings/advanced')
      this.mode = val
    },
    getSettings() {
      axios.get('/admin/settings')
        .then((response) => {
          this.settings = response.data.settings
          if (this.settings.license.resources == null) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  }
}
</script>