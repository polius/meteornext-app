<template>
  <div>
    <v-toolbar color="primary" dark>
      <v-toolbar-title>NEW DEPLOY</v-toolbar-title>
      <v-divider class="mx-3" inset vertical></v-divider>
      <v-btn :color="basicColor" dark @click="basic()">Basic</v-btn>
      <v-btn :color="proColor" dark @click="pro()">Pro</v-btn>
      <v-btn :color="inbentaColor" dark @click="inbenta()">Inbenta</v-btn>
      <v-spacer></v-spacer>
      <router-link class="nav-link" to="/deployments"><v-btn icon><v-icon>fas fa-arrow-alt-circle-left</v-icon></v-btn></router-link>
    </v-toolbar>

    <Basic v-if="mode=='basic'"/>
    <Pro v-if="mode=='pro'"/>
    <Inbenta v-if="mode=='inbenta'"/>
  </div>
</template>

<script>
import Basic from './Basic'
import Pro from './Pro'
import Inbenta from './Inbenta'

export default {
  data() {
    return {
      mode: 'basic',
      basicColor: '',
      inbentaColor: '',
      proColor: '' 
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
  created() {
    // Set Default Mode
    this.basic()
  }
}
</script>