<template>
  <div>
    <!---------------------->
    <!-- BOTTOMBAR - LEFT -->
    <!---------------------->
    <!-- SERVERS -->
    <div v-if="sidebarMode == 'servers'" style="height:35px; border-top:2px solid #2c2c2c;">
      <v-btn text small title="Refresh Connections" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
      <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
      <v-btn text small title="New Connection" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
      <v-btn text small title="Delete Connection" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
      <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
    </div>
    <!-- OBJECTS -->
    <div v-else-if="sidebarMode == 'objects'" style="height:35px; border-top:2px solid #2c2c2c;">
      <v-btn :loading="sidebarLoading" :disabled="sidebarLoading" @click="refreshObjects" text small title="Refresh" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
      <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn :disabled="sidebarLoading" @click="createDatabase" text small title="Create Database" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
      <v-btn :disabled="sidebarLoading" @click="dropDatabase" text small title="Drop Database" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
      <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn v-if="database.length > 0" :disabled="sidebarLoading" text small title="Import SQL" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-arrow-up</v-icon></v-btn>
      <v-btn v-if="database.length > 0" :disabled="sidebarLoading" text small title="Export Objects" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-arrow-down</v-icon></v-btn>
      <span v-if="database.length > 0" :disabled="sidebarLoading" style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn v-if="database.length > 0" :disabled="sidebarLoading" text small title="Database Settings" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-cog</v-icon></v-btn>
    </div>
  </div>
</template>

<script>
import EventBus from '../js/event-bus'
import { mapFields } from '../js/map-fields'

export default {
  data() {
    return {
    }
  },
  computed: {
    ...mapFields([
      'sidebarMode',
      'sidebarLoading',
      'database',
    ], { path: 'client/connection' }),
  },
  methods: {
    refreshObjects() {
      EventBus.$emit('REFRESH_SIDEBAR_OBJECTS')
    },
    createDatabase() {
    },
    dropDatabase() {
    },
  }
}
</script>