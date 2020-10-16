<template>
  <div style="height:100%; margin:min(6%, 60px) 15% 10% 15%">
    <div class="body-2" style="margin-left:10px; margin-bottom:5px;">Login Information</div>
    <v-card>
      <v-card-text style="padding-left:20px;">
        <v-text-field v-model="login['username']" label="Username" required></v-text-field>
        <v-row no-gutters>
          <v-col class="flex-grow-1 flex-shrink-1">
            <v-text-field v-model="login['password']" label="Password" :append-icon="showPassword ? 'mdi-eye' : 'mdi-eye-off'" :type="showPassword ? 'text' : 'password'" @click:append="showPassword = !showPassword" required style="padding-top:0px;"></v-text-field>
          </v-col>
          <v-col cols="3" class="flex-grow-0 flex-shrink-1" style="margin-left:10px">
            <v-select v-model="login['passwordType']" label="Type" :items="['String','Hash']" hide-details style="padding:0px; margin-bottom:5px;"></v-select>
          </v-col>
        </v-row>
        <v-text-field v-model="login['hostname']" label="Hostname" required style="padding-top:0px;"></v-text-field>
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
      login: {},
      showPassword: false,
    }
  },
  computed: {
    ...mapFields([
      'rights',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('reload-rights', this.reloadRights);
  },
  watch: {
    login: {
      handler() {
        let change = JSON.stringify(this.rights['login']) !== JSON.stringify(this.login)
        console.log("change: " + change.toString())
      },
      deep: true
    },
  },
  methods: {
    reloadRights() {
      this.login = JSON.parse(JSON.stringify(this.rights['login']))
    },
  }
}
</script>