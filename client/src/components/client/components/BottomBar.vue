<template>
  <div>
    <!---------------------->
    <!-- BOTTOMBAR - LEFT -->
    <!---------------------->
    <Servers v-if="sidebarMode == 'servers'" />
    <Objects v-else-if="sidebarMode == 'objects'" />
  </div>
</template>

<script>
import { mapFields } from '../js/map-fields'

import Servers from './bottombar/Servers'
import Objects from './bottombar/Objects'

export default {
  data() {
    return {
    }
  },
  components: { Servers, Objects },
  computed: {
    ...mapFields([
      'sidebarMode',
    ], { path: 'client/connection' }),
  },
}
</script>