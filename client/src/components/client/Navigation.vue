<template>
  <v-content>
    <div>
      <v-tabs show-arrows background-color="#9b59b6" color="white" v-model="tabs" slider-color="white" slot="extension" class="elevation-2">
        <v-tabs-slider></v-tabs-slider>
          <v-tab><span class="pl-2 pr-2"><v-icon small style="padding-right:10px">fas fa-bolt</v-icon>CLIENT</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-tab disabled><span class="pl-2 pr-2"><v-icon small style="padding-bottom:2px; padding-right:10px">fas fa-dice-d6</v-icon>Structure</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-tab disabled><span class="pl-2 pr-2"><v-icon small style="padding-bottom:2px; padding-right:10px">far fa-window-maximize</v-icon>Content</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-tab disabled><span class="pl-2 pr-2"><v-icon small style="padding-bottom:2px; padding-right:10px">fas fa-sitemap</v-icon>Relations</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-tab disabled><span class="pl-2 pr-2"><v-icon small style="padding-bottom:2px; padding-right:10px">fas fa-fire</v-icon>Triggers</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-tab disabled><span class="pl-2 pr-2"><v-icon small style="padding-bottom:2px; padding-right:10px">fas fa-th</v-icon>Table Info</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-tab><span class="pl-2 pr-2"><v-icon small style="padding-bottom:2px; padding-right:10px; font-size:14px;">fas fa-terminal</v-icon>Query</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-spacer></v-spacer>
          <v-tab title="Users" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-user-lock</v-icon></span></v-tab>
          <v-tab title="Saved Queries" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-star</v-icon></span></v-tab>
          <v-tab title="Query History" style="min-width:10px;"><span class="pl-2 pr-2"><v-icon small>fas fa-history</v-icon></span></v-tab>
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