<template>
  <div style="height:100%">
    <ServerInfo v-show="sidebarMode == 'servers'" />
    <Client v-show="sidebarMode == 'objects' && headerTabSelected == 'client'" />
    <Structure v-show="headerTabSelected == 'structure'" />
    <Content v-show="headerTabSelected == 'content'" />
    <Info v-show="headerTabSelected.startsWith('info')" />
    <Objects v-show="headerTabSelected.startsWith('objects')" />
  </div>
</template>

<script>
import { mapFields } from '../js/map-fields'

import ServerInfo from './main/ServerInfo'
import Client from './main/Client'
import Content from './main/Content'
import Structure from './main/Structure'
import Info from './main/Info'
import Objects from './main/Objects'

export default {
  data() {
    return {
    }
  },
  components: { ServerInfo, Client, Content, Structure, Info, Objects },
  computed: {
    ...mapFields([
      'headerTabSelected',
      'sidebarMode',
    ], { path: 'client/connection' }),
  },
}
</script>