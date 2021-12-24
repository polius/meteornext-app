<template>
  <v-main>
    <div>
      <v-tabs background-color="#019875" color="white" slider-color="white" slot="extension" class="elevation-2">
        <v-tabs-slider></v-tabs-slider>
          <v-tab disabled style="opacity:1"><span class="pl-2 pr-2 white--text"><v-icon small style="margin-right:10px">fas fa-database</v-icon>UTILS</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-tab to="/utils/restore"><span class="pl-2 pr-2">Restore</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
        </v-tabs>
    </div>
    <v-container fluid style="padding:10px!important">
      <v-main style="padding-top:0px; padding-bottom:0px">
        <v-slide-y-transition mode="out-in">
          <router-view/>
        </v-slide-y-transition>
      </v-main>
    </v-container>
  </v-main>
</template>

<script>

export default {
  data() {
    return {
    }
  },
}
</script>