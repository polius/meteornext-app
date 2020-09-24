<template>
  <div>
    <!------------------------->
    <!-- BOTTOMBAR - OBJECTS -->
    <!------------------------->
    <div style="height:35px; border-top:2px solid #2c2c2c;">
      <v-btn :loading="sidebarLoading" :disabled="sidebarLoading" @click="refreshObjects" text small title="Refresh" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
      <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn :disabled="sidebarLoading" @click="bottomBarClick('create')" text small title="Create Database" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
      <v-btn :disabled="sidebarLoading || database.length == 0" @click="bottomBarClick('drop')" text small title="Drop Database" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
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
    <Import />
    <Export />
  </div>
</template>

<script>
import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'

import Create from './objects/Create'
import Drop from './objects/Drop'
import Import from './objects/Import'
import Export from './objects/Export'

export default {
  data() {
    return {
      loading: false,
    }
  },
  components: { Create, Drop, Import, Export },
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
      EventBus.$emit('SHOW_BOTTOMBAR_OBJECTS_' + option.toUpperCase())
    },
    refreshObjects() {
      new Promise((resolve, reject) => { 
        EventBus.$emit('REFRESH_SIDEBAR_OBJECTS', resolve, reject)
      }).finally(() => { this.editor.focus() })
    },
  }
}
</script>