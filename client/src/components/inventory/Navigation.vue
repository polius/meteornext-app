<template>
  <v-main>
    <div>
      <v-tabs background-color="#3a539b" color="white" v-model="tabs" slider-color="white" slot="extension" class="elevation-2">
        <v-tab to="/inventory"><span class="pl-2 pr-2"><v-icon small style="padding-right:10px">fas fa-layer-group</v-icon>INVENTORY</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-tab to="/inventory/environments"><span class="pl-2 pr-2">Environments</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-tab to="/inventory/regions"><span class="pl-2 pr-2">Regions</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-tab to="/inventory/servers"><span class="pl-2 pr-2">Servers</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-tab to="/inventory/auxiliary"><span class="pl-2 pr-2">Auxiliary Connections</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
      </v-tabs>
    </div>
    <v-container fluid>
        <v-main style="padding-top:0px;">
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
      tabs: null
    }
  }
}
</script>