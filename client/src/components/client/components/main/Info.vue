<template>
  <div style="height:100%">
    <Tables v-show="headerTabSelected == 'info_table'" />
    <Views v-show="headerTabSelected == 'info_view'" />
    <!-- <Triggers v-show="headerTab == 0" />
    <Functions v-show="headerTab == 0" />
    <Procedures v-show="headerTab == 0" />
    <Events v-show="headerTab == 0" /> -->
  </div>
</template>

<script>
import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'

import Tables from './info/Tables'
import Views from './info/Views'
// import Triggers from './info/Triggers'
// import Functions from './info/Functions'
// import Procedures from './info/Procedures'
// import Events from './info/Events'

export default {
  data() {
    return {
    }
  },
  components: { Tables, Views },
  computed: {
    ...mapFields([
        'headerTabSelected',
    ], { path: 'client/connection' }),
  },
  mounted() {
    // Register Event
    EventBus.$on('GET_INFO', this.getInfo);
  },
  methods: {
    getInfo(object) {
      if (object == 'table') EventBus.$emit('GET_INFO_TABLE')
      else if (object == 'view') EventBus.$emit('GET_INFO_VIEW')
      else if (object == 'trigger') EventBus.$emit('GET_INFO_TRIGGER')
      else if (object == 'function') EventBus.$emit('GET_INFO_FUNCTION')
      else if (object == 'procedure') EventBus.$emit('GET_INFO_PROCEDURE')
      else if (object == 'event') EventBus.$emit('GET_INFO_EVENT')
    },
  }
}
</script>