<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title>{{ this.title }}</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <div>
          <v-btn :color="basicColor" @click="basic()">Basic</v-btn>
          <v-btn :color="proColor" @click="pro()" style="margin-left:10px;">Pro</v-btn>
        </div>
        <v-spacer></v-spacer>
        <router-link class="nav-link" to="/deployments"><v-btn icon><v-icon>fas fa-arrow-alt-circle-left</v-icon></v-btn></router-link>
      </v-toolbar>

      <Basic v-if="mode=='basic'" :deploymentID="this.deploymentID"/>
      <Pro v-if="mode=='pro'" :deploymentID="this.deploymentID"/>
    </v-card>
  </div>
</template>

<script>
import Basic from './Basic'
import Pro from './Pro'

export default {
  data() {
    return {
      route: '',
      mode: 'basic',
      title: '',
      basicColor: '',
      proColor: '',
      deployment: ''
    }
  },
  components: {
    Basic,
    Pro
  },
  methods: {
    basic() {
      if (this.route == 'info') return
      this.mode = 'basic'
      this.basicColor = 'primary'
      this.proColor = '#779ecb'
    },
    pro() {
      if (this.route == 'info') return
      this.mode = 'pro'
      this.basicColor = '#779ecb'
      this.proColor = 'primary'
    }
  },
  props: ['deploymentID'],
  created() {
    this.route = this.$router.currentRoute.name.endsWith('.new') ? 'new' : 'info'
    if (this.route == 'info' && typeof this.deploymentID === "undefined") this.$router.push('/deployments')
    this.title = (this.route == 'new') ? 'NEW DEPLOY' : 'INFORMATION'
    // Set Default Mode: Basic
    this.mode = 'basic'
    this.basicColor = 'primary'
    this.proColor = '#779ecb'
  }
}
</script>