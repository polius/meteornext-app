<template>
  <v-content>
    <div>
      <v-tabs background-color="#EB5F5D" color="white" v-model="tabs" slider-color="white" slot="extension" class="elevation-2">
        <v-tab to="/admin"><span class="pl-2 pr-2"><v-icon small style="padding-right:10px">fas fa-ankh</v-icon>ADMINISTRATION</span></v-tab>
        <v-divider class="mx-3" inset vertical></v-divider>
        <v-tab to="/admin/users"><span class="pl-2 pr-2">Users</span></v-tab>
        <v-tab to="/admin/groups"><span class="pl-2 pr-2">Groups</span></v-tab>
        <v-tab to="/admin/deployments"><span class="pl-2 pr-2">Deployments</span></v-tab>
      </v-tabs>
    </div>
    <v-container fluid>
        <v-content style="padding-top:0px;">
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