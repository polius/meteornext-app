<template>
  <div>
    <v-dialog v-model="dialog" max-width="80%">
      
    </v-dialog>
  </div>
</template>

<script>
import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'

export default {
  data() {
    return {
      dialog: false,
    }
  },
  computed: {
    ...mapFields([
      'headerTab',
      'headerTabSelected',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('SHOW_RIGHTS', this.showDialog);
  },
  watch: {
    dialog: function(value) {
      if (!value) {
        const tab = {'client': 0, 'structure': 1, 'content': 2, 'info': 3, 'objects': 6}
        this.headerTab = tab[this.headerTabSelected]
      }
    }
  },
  methods: {
    showDialog() {
      this.dialog = true
    },
  }
}
</script>