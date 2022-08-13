<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="subtitle-1">NEW DEPLOY</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <div>
          <v-btn v-if="deploymentsBasic" @click="basic()" :color="basicColor" style="margin-right:10px"><v-icon small style="margin-right:10px; margin-bottom:1px">fas fa-chess-knight</v-icon>Basic</v-btn>
          <v-btn v-if="deploymentsPro" @click="pro()" :color="proColor"><v-icon small style="margin-right:10px; margin-bottom:1px">fas fa-chess-queen</v-icon>Pro</v-btn>
        </div>
        <v-spacer></v-spacer>
        <router-link class="nav-link" to="/deployments"><v-btn icon><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn></router-link>
      </v-toolbar>
      <keep-alive>
        <Basic v-if="mode == 'basic'" :fields="fields" @change="updateFields"/>
        <Pro v-else-if="mode == 'pro'" :fields="fields" @change="updateFields"/>
      </keep-alive>
    </v-card>
    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<style scoped>
::v-deep .v-toolbar__content {
  padding-right:5px;
}
</style>

<script>
import axios from 'axios'

import Basic from './Basic'
import Pro from './Pro'

export default {
  data() {
    return {
      mode: '',
      basicColor: 'primary',
      proColor: '#779ecb',
      fields: { name: '', release: '', environment: '', databases: null, queries: [], code: null },
      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarColor: '',
      snackbarText: ''
    }
  },
  components: { Basic, Pro },
  computed : {
    deploymentsEnabled : function() { return this.$store.getters['app/deployments_enabled'] },
    deploymentsBasic : function() { return this.$store.getters['app/deployments_basic'] },
    deploymentsPro : function() { return this.$store.getters['app/deployments_pro'] },
  },
  created() {
    // Check permissions
    if (!this.deploymentsEnabled || (!this.deploymentsBasic && !this.deploymentsPro)) this.$router.back()
    // Choose the Deploment Template
    else {
      if (this.$route.path.startsWith('/deployments/new/basic') && this.deploymentsBasic) this.basic()
      else if (this.$route.path.startsWith('/deployments/new/pro') && this.deploymentsPro) this.pro()
      // else this.$router.back()
    }
    // Get deployment (clone)
    if (this.$route.params.uri !== undefined) this.getDeployment()
 },
  methods: {
    basic() {
      if (!this.$route.path.startsWith('/deployments/new/basic')) this.$router.push('/deployments/new/basic')
      this.mode = 'basic'
      this.basicColor = 'primary'
      this.proColor = '#779ecb'
    },
    pro() {
      if (!this.$route.path.startsWith('/deployments/new/pro')) this.$router.push('/deployments/new/pro')
      this.mode = 'pro'
      this.basicColor = '#779ecb'
      this.proColor = 'primary'
    },
    updateFields(field) {
      this.fields[field.name] = field.value
    },
    getDeployment() {
      axios.get('/deployments', { params: { uri: this.$route.params.uri } })
        .then((response) => {
          const deployment = response.data.deployment
          // Build queries
          let queries = []
          if (deployment['mode'] == 'BASIC') {
            let items = JSON.parse(deployment['queries'])
            for (let i = 0; i < items.length; ++i) queries.push({id: i+1, query: items[i]['q']})
          }
          // Assign fields from retrieved deployment
          this.fields = {
            name: deployment['name'],
            release: deployment['release'],
            environment: deployment['environment_id'],
            databases: deployment['databases'],
            queries: queries,
            code: deployment['code'],
          }
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color
      this.snackbar = true
    }
  },
}
</script>