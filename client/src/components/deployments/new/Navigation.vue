<template>
  <div>
    <v-card>
      <v-toolbar flat color="primary">
        <v-toolbar-title>NEW DEPLOY</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-btn :color="basicColor" @click="basic()">Basic</v-btn>
        <v-btn :color="proColor" @click="pro()" style="margin-left:10px;">Pro</v-btn>
        <v-spacer></v-spacer>
        <router-link class="nav-link" to="/deployments"><v-btn icon><v-icon>fas fa-arrow-alt-circle-left</v-icon></v-btn></router-link>
      </v-toolbar>

      <Basic v-if="mode=='basic'"/>
      <Pro v-if="mode=='pro'"/>
    </v-card>
  </div>
</template>

<script>
import Basic from './Basic'
import Pro from './Pro'

export default {
  data() {
    return {
      mode: 'basic',
      basicColor: '',
      proColor: '' 
    }
  },
  components: {
    Basic,
    Pro
  },
  methods: {
    basic() {
      this.mode = 'basic'
      this.basicColor = 'primary'
      this.proColor = '#779ecb'
    },
    pro() {
      this.mode = 'pro'
      this.basicColor = '#779ecb'
      this.proColor = 'primary'
    }
  },
  created() {
    // Set Default Mode
    this.basic()
  }
}
</script>