<template>
  <div style="height:100%">
    <Tables v-show="headerTabSelected == 'info_table'" />
    <Views v-show="headerTabSelected == 'info_view'" />
    <Triggers v-show="headerTabSelected == 'info_trigger'" />
    <Functions v-show="headerTabSelected == 'info_function'" />
    <Procedures v-show="headerTabSelected == 'info_procedure'" />
    <Events v-show="headerTabSelected == 'info_event'" />
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
import Events from './info/Events'

export default {
  data() {
    return {
    }
  },
  components: { Tables, Views, Triggers, Functions, Procedures, Events },
  computed: {
    ...mapFields([
        'headerTabSelected',
    ], { path: 'client/connection' }),
  },
  mounted() {
    // Register Event
    EventBus.$on('get-info', this.getInfo);
  },
  methods: {
    getInfo(object) {
      if (object == 'table') EventBus.$emit('get-info-table')
      else if (object == 'view') EventBus.$emit('get-info-view')
      else if (object == 'trigger') EventBus.$emit('get-info-trigger')
      else if (object == 'function') EventBus.$emit('get-info-function')
      else if (object == 'procedure') EventBus.$emit('get-info-procedure')
      else if (object == 'event') EventBus.$emit('get-info-event')
    },
  }
}
</script>