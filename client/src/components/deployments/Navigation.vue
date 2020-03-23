<template>
  <v-content>
    <div>
      <v-tabs background-color="#EB5F5D" color="white" v-model="tabs" slider-color="white" slot="extension" class="elevation-2">
        <v-tabs-slider></v-tabs-slider>
        <v-tab to="/deployments"><span class="pl-2 pr-2"><v-icon small style="padding-right:10px">fas fa-meteor</v-icon>DEPLOYMENTS</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-tab to="/deployments/releases"><span class="pl-2 pr-2">RELEASES</span></v-tab>
      </v-tabs>
    </div>
    <v-container fluid>
      <v-content style="padding-top:0px; padding-bottom:0px;">
        <v-slide-y-transition mode="out-in">
          <router-view/>
        </v-slide-y-transition>
      </v-content>
    </v-container>
  </v-content>
</template>

<script>
export default {
  data() {
    return {
      tabs: null
    }
  },
  computed : {
    deployments_edit : function() { return this.$store.getters.deployments_edit }
  }
}
</script>