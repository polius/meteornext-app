<template>
  <div style="height:100%; margin:min(6%, 60px) 15% 10% 15%">
    <div class="body-2" style="margin-left:10px; margin-bottom:5px;">Resource Limits</div>
    <v-card>
      <v-card-text style="padding-left:20px;">
        <v-form ref="form">
          <v-text-field :disabled="disabled" v-model="resources['max_queries']" label="Max Queries / Hour" required :rules="[v => v == parseInt(v) && v >= 0 || '']"></v-text-field>
          <v-text-field :disabled="disabled" v-model="resources['max_updates']" label="Max Updates / Hour" required :rules="[v => v == parseInt(v) && v >= 0 || '']" style="padding-top:0px;"></v-text-field>
          <v-text-field :disabled="disabled" v-model="resources['max_connections']" label="Max Connections / Hour" required :rules="[v => v == parseInt(v) && v >= 0 || '']" style="padding-top:0px;"></v-text-field>
          <v-text-field :disabled="disabled" v-model="resources['max_simultaneous']" label="Max Simultaneous Connections / Hour" required :rules="[v => v == parseInt(v) && v >= 0 || '']" style="padding-top:0px;"></v-text-field>
          <div class="body-2">Remarks: 0 (default) = no limit</div>
        </v-form>
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
      mode: '',
      disabled: true,
      resources: {},
    }
  },
  computed: {
    ...mapFields([
      'rights',
      'rightsDiff',
      'rightsSelected',
      'rightsForm',
    ], { path: 'client/connection' }),
  },
  activated() {
    EventBus.$on('reload-rights', this.reloadRights);
  },
  watch: {
    rightsSelected: function(val) {
      this.disabled = (Object.keys(val).length == 0 && this.mode == 'edit') ? true : false
    },
    resources: {
      handler(obj) {
        // Compute diff
        let diff = {}
        for (let [key, value] of Object.entries(obj)) {
          if (value.length > 0 && key in this.rights['resources'] && value != this.rights['resources'][key]) diff[key] = value
        }
        this.rightsDiff['resources'] = diff
      },
      deep: true
    },
  },
  methods: {
    reloadRights(mode) {
      this.mode = mode
      this.rightsForm['resources'] = this.$refs.form
      this.resources = JSON.parse(JSON.stringify(this.rights['resources']))
      if (mode == 'clone') this.rights['resources'] = { max_queries: '0', max_updates: '0', max_connections: '0', max_simultaneous: '0' }
      requestAnimationFrame(() => { this.$refs.form.resetValidation() })
    },
  }
}
</script>