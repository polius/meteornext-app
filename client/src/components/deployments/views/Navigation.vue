<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="subtitle-1">NEW DEPLOY</v-toolbar-title>
        <v-divider class="mx-3" inset vertical></v-divider>
        <div>
          <v-btn v-if="deployments_basic" :color="basicColor" @click="basic()"><v-icon small style="padding-right:10px; padding-bottom:1px">fas fa-chess-knight</v-icon>Basic</v-btn>
          <v-btn v-if="deployments_pro" :color="proColor" @click="pro()" style="margin-left:10px;"><v-icon small style="padding-right:10px; padding-bottom:1px">fas fa-chess-queen</v-icon>Pro</v-btn>
        </div>
        <v-spacer></v-spacer>
        <router-link class="nav-link" to="/deployments"><v-btn icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn></router-link>
      </v-toolbar>
      <Basic v-if="mode=='basic'"/>
      <Pro v-else-if="mode=='pro'"/>
    </v-card>
  </div>
</template>

<style scoped>
::v-deep .v-toolbar__content {
  padding-right:5px;
}
</style>

<script>
import Basic from './Basic'
import Pro from './Pro'

export default {
  data() {
    return {
      mode: '',
      basicColor: '',
      proColor: '',
    }
  },
  components: { Basic, Pro },
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
  computed : {
    deployments_basic : function() { return this.$store.getters['app/deployments_basic'] },
    deployments_pro : function() { return this.$store.getters['app/deployments_pro'] },
  },
  created() {
    // Choose the Deploment Template
    if (this.deployments_basic) this.basic()
    else if (this.deployments_pro) this.pro()
  }
}
</script>