<template>
  <div>
    <!----------------------------->
    <!-- BOTTOMBAR - CONNECTIONS -->
    <!----------------------------->
    <div style="height:35px; border-top:2px solid #2c2c2c;">
      <v-btn @click="bottomBarClick('refresh')" text small title="Refresh Connections" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
      <span style="background-color:#424242; padding-left:1px; margin-left:1px; margin-right:1px;"></span>
      <v-btn @click="bottomBarClick('new')" text small title="New Connection" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
      <v-btn :disabled="sidebarSelected.length == 0" @click="bottomBarClick('remove')" text small :title="sidebarSelected.length == 1 ? 'Remove Connection' : 'Remove Connections'" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
      <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn @click="bottomBarClick('newFolder')" text small title="New Folder" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-folder</v-icon></v-btn>
    </div>
    <!------------->
    <!-- DIALOGs -->
    <!------------->
    <New />
    <Remove />
    <NewFolder />
  </div>
</template>

<script>
import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'

import New from './connections/New'
import Remove from './connections/Remove'
import NewFolder from './connections/NewFolder'

export default {
  data() {
    return {
      loading: false,
    }
  },
  components: { New, Remove, NewFolder },
  computed: {
    ...mapFields([
      'database',
      'sidebarLoading',
      'sidebarSelected',
    ], { path: 'client/connection' }),
  },
  methods: {
    bottomBarClick(option) {
      EventBus.$emit('show-bottombar-connections-' + option)
    },
    refreshObjects() {
      new Promise((resolve, reject) => { 
        EventBus.$emit('refresh-sidebar-connections', resolve, reject)
      }).finally(() => {  })
    },
  }
}
</script>