<template>
  <v-content>
      <v-toolbar dense tabs dark height=0 color="#EB5F5D">
        <v-tabs v-model="tabs" color="transparent" slider-color="white" slot="extension">
          <v-tab to="/deployments"><span class="pl-2 pr-2"><v-icon small style="padding-right:10px">fas fa-meteor</v-icon>DEPLOYMENTS</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-tab to="/deployments/environments"><span class="pl-2 pr-2">Environments</span></v-tab>
          <v-tab to="/deployments/regions"><span class="pl-2 pr-2">Regions</span></v-tab>
          <v-tab to="/deployments/servers"><span class="pl-2 pr-2">Servers</span></v-tab>
          <v-tab to="/deployments/auxiliary"><span class="pl-2 pr-2">Auxiliary Connections</span></v-tab>
          <v-tab to="/deployments/slack"><span class="pl-2 pr-2">Slack</span></v-tab>
          <v-tab to="/deployments/s3"><span class="pl-2 pr-2">Amazon S3</span></v-tab>
          <v-tab to="/deployments/web"><span class="pl-2 pr-2">Web</span></v-tab>
        </v-tabs>
      </v-toolbar>

      <v-container fluid>
        <v-layout row wrap>
          <v-content style="padding-top:0px;">
            <v-slide-y-transition mode="out-in">
              <router-view/>
            </v-slide-y-transition>
          </v-content>
          </v-layout>
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