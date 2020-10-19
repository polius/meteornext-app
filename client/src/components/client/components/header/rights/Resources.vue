<template>
  <div style="height:100%; margin:min(6%, 60px) 15% 10% 15%">
    <div class="body-2" style="margin-left:10px; margin-bottom:5px;">Resource Limits</div>
    <v-card>
      <v-card-text style="padding-left:20px;">
        <v-text-field :disabled="disabled" v-model="resources['max_queries']" label="Max Queries / hour" required></v-text-field>
        <v-text-field :disabled="disabled" v-model="resources['max_updates']" label="Max Updates / hour" required style="padding-top:0px;"></v-text-field>
        <v-text-field :disabled="disabled" v-model="resources['max_connections']" label="Max Connections / hour" required style="padding-top:0px;"></v-text-field>
        <v-text-field :disabled="disabled" v-model="resources['max_simultaneous']" label="Max Simultaneous Connections / hour" required style="padding-top:0px;"></v-text-field>
        <div class="body-2">Remarks: 0 (default) = no limit</div>
      </v-card-text>
    </v-card>
  </div>
</template>

<script>
import EventBus from '../../../js/event-bus'
import { mapFields } from '../../../js/map-fields'

export default {
  data() {
    return {
      disabled: true,
      resources: {},
    }
  },
  computed: {
    ...mapFields([
      'rights',
      'rightsItem',
      'rightsSelected',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('reload-rights', this.reloadRights);
  },
  watch: {
    rightsSelected: function(val) {
      this.disabled = Object.keys(val).length == 0 ? true : false
    },
    resources: {
      handler(obj) {
        // Compute diff
        let diff = {}
        for (let [key, value] of Object.entries(obj)) {
          if (value.length > 0 && value != this.rights['resources'][key]) diff[key] = value
        }
        this.rightsItem['resources'] = diff
      },
      deep: true
    },
  },
  methods: {
    reloadRights() {
      this.resources = JSON.parse(JSON.stringify(this.rights['resources']))
    },
  }
}
</script>