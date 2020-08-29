<template>
  <div style="height:100%">
    <Tables v-show="headerTabSelected == 'info_table'" />
    <Views v-show="headerTabSelected == 'info_view'" />
    <Triggers v-show="headerTabSelected == 'info_trigger'" />
    <Functions v-show="headerTabSelected == 'info_function'" />
    <Procedures v-show="headerTabSelected == 'info_procedure'" />
    <!--<Events v-show="headerTabSelected == 'info_event'" /> -->
  </div>
</template>

<script>
import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'

import Tables from './info/Tables'
import Views from './info/Views'
import Triggers from './info/Triggers'
import Functions from './info/Functions'
import Procedures from './info/Procedures'
// import Events from './info/Events'

export default {
  data() {
    return {
    }
  },
  components: { Tables, Views, Triggers, Functions, Procedures },
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