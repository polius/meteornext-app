<template>
  <div>
    <!---------------------->
    <!-- BOTTOMBAR - LEFT -->
    <!---------------------->
    <Servers v-show="sidebarMode == 'servers'" />
    <Objects v-show="sidebarMode == 'objects'" />
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