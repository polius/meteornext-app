<template>
  <div>
    <!---------------------->
    <!-- BOTTOMBAR - LEFT -->
    <!---------------------->
    <Connections v-if="sidebarMode == 'servers'" />
    <Objects v-else-if="sidebarMode == 'objects'" />
  </div>
</template>

<script>
import { mapFields } from '../js/map-fields'

import Connections from './bottombar/Connections'
import Objects from './bottombar/Objects'

export default {
  data() {
    return {
    }
  },
  components: { Connections, Objects },
  computed: {
    ...mapFields([
      'sidebarMode',
    ], { path: 'client/connection' }),
  },
}
</script>