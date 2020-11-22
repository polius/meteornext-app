<template>
  <div>
    <!------------------------->
    <!-- BOTTOMBAR - SERVERS -->
    <!------------------------->
    <div style="height:35px; border-top:2px solid #2c2c2c;">
      <v-btn :disabled="sidebarLoading" @click="refreshServers" text small title="Refresh Servers" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
      <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
      <v-btn :disabled="sidebarLoading" @click="bottomBarClick('new')" text small title="New Server" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
      <v-btn :disabled="sidebarLoading || sidebarSelected.length == 0" @click="bottomBarClick('remove')" text small :title="sidebarSelected.length == 1 ? 'Remove Server' : 'Remove Servers'" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
      <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn :disabled="sidebarLoading" @click="bottomBarClick('new-folder')" text small title="New Folder" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-folder</v-icon></v-btn>
    </div>
    <!------------->
    <!-- DIALOGs -->
    <!------------->
    <New />
    <Remove />
    <Move />
    <NewFolder />
    <RemoveFolder />
    <RenameFolder />
  </div>
</template>

<script>
import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'

import New from './servers/New'
import Remove from './servers/Remove'
import Move from './servers/Move'
import NewFolder from './servers/NewFolder'
import RemoveFolder from './servers/RemoveFolder'
import RenameFolder from './servers/RenameFolder'

export default {
  data() {
    return {
    }
  },
  components: { New, Remove, Move, NewFolder, RemoveFolder, RenameFolder },
  computed: {
    ...mapFields([
      'database',
      'sidebarLoading',
      'sidebarSelected',
    ], { path: 'client/connection' }),
  },
  methods: {
    bottomBarClick(option) {
      EventBus.$emit('show-bottombar-servers-' + option)
    },
    refreshServers() {
      new Promise((resolve, reject) => EventBus.$emit('get-sidebar-servers', resolve, reject))
    },
  }
}
</script>