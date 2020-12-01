<template>
  <div>
    <!------------------------->
    <!-- BOTTOMBAR - OBJECTS -->
    <!------------------------->
    <div style="height:35px; border-top:2px solid #2c2c2c;">
      <v-btn :disabled="sidebarLoading" @click="refreshObjects" text small title="Refresh" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
      <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn :disabled="sidebarLoading" @click="bottomBarClick('create')" text small title="Create Database" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
      <v-btn :disabled="sidebarLoading || database.length == 0" @click="bottomBarClick('drop')" text small title="Drop Database" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
      <!-- <v-btn :disabled="sidebarLoading" @click="bottomBarClick('clone')" text small title="Clone Database" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-clone</v-icon></v-btn> -->
      <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn v-if="database.length > 0" :disabled="sidebarLoading" @click="bottomBarClick('import')" text small title="Import SQL" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-arrow-up</v-icon></v-btn>
      <v-btn v-if="database.length > 0" :disabled="sidebarLoading" @click="bottomBarClick('export')" text small title="Export Objects" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-arrow-down</v-icon></v-btn>
      <span v-if="database.length > 0" :disabled="sidebarLoading" style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn :disabled="sidebarLoading" @click="bottomBarClick('variables')" text small title="Server Variables" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-cog</v-icon></v-btn>
    </div>
    <!------------->
    <!-- DIALOGs -->
    <!------------->
    <Create />
    <Drop />
    <Clone />
    <Import />
    <Export />
    <Variables />
  </div>
</template>

<script>
import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'

import Create from './objects/Create'
import Drop from './objects/Drop'
import Clone from './objects/Clone'
import Import from './objects/Import'
import Export from './objects/Export'
import Variables from './objects/Variables'

export default {
  data() {
    return {
      loading: false,
    }
  },
  components: { Create, Drop, Clone, Import, Export, Variables },
  computed: {
    ...mapFields([
      'editor',
    ], { path: 'client/components' }),
    ...mapFields([
      'database',
      'sidebarLoading',
    ], { path: 'client/connection' }),
  },
  methods: {
    bottomBarClick(option) {
      EventBus.$emit('show-bottombar-objects-' + option)
    },
    refreshObjects() {
      new Promise((resolve, reject) => { 
        EventBus.$emit('refresh-sidebar-objects', resolve, reject)
      }).finally(() => { this.editor.focus() })
    },
  }
}
</script>