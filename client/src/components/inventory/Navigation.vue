<template>
  <v-main>
    <div>
      <v-tabs background-color="#3a539b" color="white" v-model="tabs" slider-color="white" slot="extension" class="elevation-2">
        <v-tab disabled to="/inventory" style="opacity:1"><span class="pl-2 pr-2 white--text"><v-icon small style="margin-right:10px">fas fa-layer-group</v-icon>INVENTORY</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-tab to="/inventory/servers"><span class="pl-2 pr-2">Servers</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-tab to="/inventory/regions"><span class="pl-2 pr-2">Regions</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-tab to="/inventory/environments"><span class="pl-2 pr-2">Environments</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-tab to="/inventory/auxiliary"><span class="pl-2 pr-2">Auxiliary Connections</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-tab to="/inventory/cloud"><span class="pl-2 pr-2">Cloud Keys</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
      </v-tabs>
    </div>
    <v-container fluid style="padding:10px!important">
        <v-main style="padding-top:0px;">
          <router-view/>
        </v-main>
    </v-container>      
  </v-main>
</template>

<script>

export default {
  data() {
    return {
      tabs: 1
    }
  }
}
</script>