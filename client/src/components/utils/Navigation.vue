<template>
  <v-content>
    <div>
      <v-tabs background-color="#16a085" color="white" v-model="tabs" slider-color="white" slot="extension" class="elevation-2">
        <v-tabs-slider></v-tabs-slider>
          <v-tab to="/utils"><span class="pl-2 pr-2"><v-icon small style="padding-right:10px">fas fa-database</v-icon>UTILS</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
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
  }
}
</script>