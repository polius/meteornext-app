<template>
  <v-main>
    <div>
      <v-tabs background-color="#ed7b2f" color="white" v-model="tabs" slider-color="white" slot="extension" class="elevation-2"> <!-- #16a085 -->
        <v-tabs-slider></v-tabs-slider>
          <v-tab to="/monitoring"><span class="pl-2 pr-2"><v-icon small style="margin-right:10px">fas fa-desktop</v-icon>MONITORING</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-tab to="/monitoring/parameters"><span class="pl-2 pr-2"><v-icon size="14" style="margin-right:10px; margin-bottom:2px">fas fa-code</v-icon>Parameters</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-tab to="/monitoring/processlist"><span class="pl-2 pr-2"><v-icon size="14" style="margin-right:10px; margin-bottom:2px">fas fa-server</v-icon>Processlist</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-tab to="/monitoring/queries"><span class="pl-2 pr-2"><v-icon size="14" style="margin-right:10px; margin-bottom:2px">fas fa-stream</v-icon>Queries</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
        </v-tabs>
    </div>
    <v-container fluid>
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
  }
}
</script>