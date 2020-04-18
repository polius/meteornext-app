<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title class="subtitle-1">{{ this.title }}</v-toolbar-title>
        <v-divider v-if="route == 'new'" class="mx-3" inset vertical></v-divider>
        <div v-if="route == 'new'">
          <v-btn v-if="deployments_basic" :color="basicColor" @click="basic()" style="margin-right:10px;">Basic</v-btn>
          <v-btn v-if="deployments_pro" :color="proColor" @click="pro()" style="margin-right:10px;">Pro</v-btn>
          <v-btn v-if="deployments_inbenta" :color="inbentaColor" @click="inbenta()">Inbenta</v-btn>
        </div>
        <v-spacer></v-spacer>
        <router-link class="nav-link" to="/deployments"><v-btn icon><v-icon>fas fa-arrow-alt-circle-left</v-icon></v-btn></router-link>
      </v-toolbar>

      <Basic v-if="mode=='basic'" :deploymentID="this.deploymentID"/>
      <Pro v-if="mode=='pro'" :deploymentID="this.deploymentID"/>
      <Inbenta v-if="mode=='inbenta'" :deploymentID="this.deploymentID"/>
    </v-card>
  </div>
</template>

<script>
import Basic from './Basic'
import Pro from './Pro'
import Inbenta from './Inbenta'

export default {
  data() {
    return {
      route: '',
      mode: '',
      title: '',
      basicColor: '',
      proColor: '',
      inbentaColor: ''
    }
  },
  components: {
    Basic,
    Pro,
    Inbenta
  },
  methods: {
    basic() {
      this.mode = 'basic'
      this.basicColor = 'primary'
      this.proColor = '#779ecb'
      this.inbentaColor = '#779ecb'
    },
    pro() {
      this.mode = 'pro'
      this.basicColor = '#779ecb'
      this.proColor = 'primary'
      this.inbentaColor = '#779ecb'
    },
    inbenta() {
      this.mode = 'inbenta'
      this.basicColor = '#779ecb'
      this.proColor = '#779ecb'
      this.inbentaColor = 'primary'
    }
  },
  props: ['deploymentID', 'deploymentMode'],
  computed : {
    deployments_basic : function(){ return this.$store.getters.deployments_basic },
    deployments_pro : function(){ return this.$store.getters.deployments_pro },
    deployments_inbenta : function(){ return this.$store.getters.deployments_inbenta }
  },
  created() {
    // Get Route
    this.route = (this.$router.currentRoute.name == 'deployments.new') ? 'new' : 'edit'

    // Validates route & deploymentID
    if (this.route != 'new' && typeof this.deploymentID === "undefined") this.$router.push('/deployments')

    // Set Title
    this.title = (this.route == 'new') ? 'NEW DEPLOY' : 'EDIT DEPLOY'

    // Choose the Deploment Template
    if (this.deploymentMode == 'BASIC' || this.deployments_basic) this.basic()
    else if (this.deploymentMode == 'PRO' || this.deployments_pro) this.pro()
    else if (this.deploymentMode == 'INBENTA' || this.deployments_inbenta) this.inbenta()
  }
}
</script>