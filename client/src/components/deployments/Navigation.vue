<template>
  <v-main>
    <div>
      <v-tabs background-color="#FF6666" color="white" v-model="tabs" slider-color="white" slot="extension" class="elevation-2">
        <v-tabs-slider></v-tabs-slider>
        <v-tab to="/deployments"><span class="pl-2 pr-2"><v-icon small style="margin-right:10px">fas fa-meteor</v-icon>DEPLOYMENTS</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-tab title="Manage releases" to="/deployments/releases"><span class="pl-2 pr-2"><v-icon size="14" style="margin-right:10px; margin-bottom:2px">fas fa-list</v-icon>RELEASES</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-tab title="Manage shared deployments" to="/deployments/shared"><span class="pl-2 pr-2"><v-icon size="14" style="margin-right:10px; margin-bottom:3px">fas fa-share</v-icon>SHARED</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
      </v-tabs>
    </div>
    <v-container fluid style="padding:10px!important">
      <v-main style="padding-top:0px; padding-bottom:0px;">
        <router-view/>
      </v-main>
    </v-container>
  </v-main>
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