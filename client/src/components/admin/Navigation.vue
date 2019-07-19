<template>
  <v-content>
      <v-toolbar dense tabs dark height=0 color="#EB5F5D">
        <v-tabs v-model="tabs" color="transparent" slider-color="white" slot="extension">
          <v-tab to="/admin"><span class="pl-2 pr-2"><v-icon small style="padding-right:10px">fas fa-ankh</v-icon>ADMINISTRATION</span></v-tab>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-tab to="/admin/users"><span class="pl-2 pr-2">Users</span></v-tab>
          <v-tab to="/admin/groups"><span class="pl-2 pr-2">Groups</span></v-tab>
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