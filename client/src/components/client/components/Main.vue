<template>
  <div style="height:100%">
    <ServerInfo v-show="sidebarMode == 'servers'" />
    <Client v-if="mounted" v-show="sidebarMode == 'objects' && headerTabSelected == 'client'" />
    <Structure v-if="mounted" v-show="headerTabSelected == 'structure'" />
    <Content v-if="mounted" v-show="headerTabSelected == 'content'" />
    <Info v-if="mounted" v-show="headerTabSelected.startsWith('info')" />
    <Objects v-if="mounted" v-show="headerTabSelected.startsWith('objects')" />
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
      mounted: false
    }
  },
  components: { ServerInfo, Client, Content, Structure, Info, Objects },
  computed: {
    ...mapFields([
      'headerTabSelected',
      'sidebarMode',
    ], { path: 'client/connection' }),
  },
  mounted() {
    setTimeout(() => { this.mounted = true }, 1000);
  },
}
</script>