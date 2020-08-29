<template>
  <div style="height:100%">
    <Tables v-show="headerTabSelected == 'object_table'" />
    <!-- <Views v-show="headerTabSelected == 'object_view'" />
    <Triggers v-show="headerTabSelected == 'object_trigger'" />
    <Functions v-show="headerTabSelected == 'object_function'" />
    <Procedures v-show="headerTabSelected == 'object_procedure'" />
    <Events v-show="headerTabSelected == 'object_event'" /> -->
  </div>
</template>

<script>
import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'

import Tables from './objects/Tables'
// import Views from './objects/Views'
// import Triggers from './objects/Triggers'
// import Functions from './objects/Functions'
// import Procedures from './objects/Procedures'
// import Events from './objects/Events'

export default {
  data() {
    return {
    }
  },
  components: { Tables /*, Views, Triggers, Functions, Procedures, Events */ },
  computed: {
    ...mapFields([
        'headerTabSelected',
    ], { path: 'client/connection' }),
  },
  mounted() {
    // Register Event
    EventBus.$on('GET_OBJECT', this.getObject);
  },
  methods: {
    getObject(object) {
      if (object == 'table') EventBus.$emit('GET_OBJECT_TABLE')
      else if (object == 'view') EventBus.$emit('GET_OBJECT_VIEW')
      else if (object == 'trigger') EventBus.$emit('GET_OBJECT_TRIGGER')
      else if (object == 'function') EventBus.$emit('GET_OBJECT_FUNCTION')
      else if (object == 'procedure') EventBus.$emit('GET_OBJECT_PROCEDURE')
      else if (object == 'event') EventBus.$emit('GET_OBJECT_EVENT')
    },
  }
}
</script>