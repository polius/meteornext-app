<template>
  <div style="height:100%; margin:min(6%, 60px) 15% 10% 15%">
    <div class="body-2" style="margin-left:10px; margin-bottom:5px;">Login Information</div>
    <v-card>
      <v-card-text style="padding-left:20px;">
        <v-form ref="form">
          <v-text-field ref="username" :readonly="mode == 'edit'" :disabled="disabled" v-model="login['username']" label="Username" :rules="[v => !!v || '']" required></v-text-field>
          <v-text-field :readonly="mode == 'edit'" :disabled="disabled" v-model="login['hostname']" label="Hostname" required :rules="[v => !!v || '']" style="padding-top:0px;"></v-text-field>
          <v-row no-gutters>
            <v-col class="flex-grow-1 flex-shrink-1">
              <v-text-field :disabled="disabled" v-model="login['password']" label="Password" :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'" :type="showPassword ? 'text' : 'password'" @click:append="showPassword = !showPassword" :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>
            </v-col>
            <v-col cols="3" class="flex-grow-0 flex-shrink-1" style="margin-left:10px">
              <v-select :disabled="disabled" v-model="login['passwordType']" label="Type" :items="['String','Hash']" hide-details :rules="[v => !!v || '']" style="padding:0px; margin-bottom:5px;"></v-select>
            </v-col>
          </v-row>
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
      login: {},
      showPassword: false,
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
    login: {
      handler(obj) {
        // Compute diff
        let diff = {}
        for (let [key, value] of Object.entries(obj)) {
          if (value.length > 0 && value != this.rights['login'][key]) diff[key] = value
        }
        this.rightsDiff['login'] = diff
      },
      deep: true
    },
  },
  methods: {
    reloadRights(mode) {
      this.mode = mode
      this.rightsForm['login'] = this.$refs.form
      this.login = JSON.parse(JSON.stringify(this.rights['login']))
      if (mode == 'new') this.login['passwordType'] = 'String'
      if (['new','clone'].includes(mode)) this.$nextTick(() => { this.$refs.username.focus() })
      if (mode == 'clone') this.rights['login'] = {}
      requestAnimationFrame(() => { this.$refs.form.resetValidation() })
    },
  }
}
</script>