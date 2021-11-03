<template>
  <v-flex xs12 style="margin:5px">
    <div class="text-h6 font-weight-regular"><v-icon small style="margin-right:10px; margin-bottom:3px; color:#fa8131">fas fa-certificate</v-icon>LICENSE</div>
    <div class="body-1 font-weight-regular" style="margin-top:10px">This copy of Meteor Next is <span class="body-1 font-weight-medium" style="color:#00b16a">LICENSED</span>.</div>
    <v-text-field readonly :loading="loading" v-model="license.email" label="Email" style="margin-top:15px" required :rules="[v => !!v || '']"></v-text-field>
    <v-text-field readonly :loading="loading" v-model="license.key" label="Key" style="padding-top:0px" @click:append="show_key = !show_key" :append-icon="show_key ? 'visibility' : 'visibility_off'" :type="show_key ? 'text' : 'password'" required :rules="[v => !!v || '']"></v-text-field>
    <v-text-field readonly :loading="loading" v-model="resources" label="Resources" style="padding-top:0px" required :rules="[v => !!v || '']"></v-text-field>
    <v-text-field readonly :loading="loading" v-model="expiration" label="Expiration" style="padding-top:0px" required :rules="[v => !!v || '']" hide-details></v-text-field>
    <!-- <v-switch readonly :loading="loading" v-model="renewal" label="Automatic Renewal" color="#00b16a" style="padding-top:0px; margin-top:0px" hide-details></v-switch> -->
    <v-btn @click="refresh" :loading="loading || diff == null" :disabled="diff == null || diff < 60" color="info" style="margin-top:20px"><v-icon small style="margin-right:10px">fas fa-spinner</v-icon>{{ `Refresh ${diff == null || diff >= 60 ? '' : '- Wait ' + (60-diff) + ' seconds'}` }}</v-btn>
  </v-flex>
</template>

<script>
import axios from 'axios'
import moment from 'moment'
import EventBus from '../../js/event-bus'

export default {
  data: () => ({
    timer: null,
    diff: null,
    // renewal: true,
    license: {},
    show_key: false,
    loading: true,
  }),
  props: ['info','init'],
  created() {
    if (Object.keys(this.info).length > 0) this.license = JSON.parse(JSON.stringify(this.info))
  },
  mounted() {
    this.loading = false
    this.checkLicense()
  },
  beforeDestroy() {
    clearInterval(this.timer)
  },
  computed: {
    resources() {
      if (this.license.resources == -1) return 'Unlimited'
      return this.license.resources + (this.license.resources == 1 ? ' Server' : ' Servers') + ' / User'
    },
    expiration() {
      if (this.license.expiration == null) return 'Lifetime'
      return this.license.expiration
    }
  },
  watch: {
    info: function(val) {
      this.license = JSON.parse(JSON.stringify(val))
    },
    init: function(val) {
      this.loading = val
    },
  },
  methods: {
    checkLicense() {
      clearInterval(this.timer)
      this.timer = setInterval(() => {
        this.diff = moment.utc().diff(moment.utc(this.license.last_check_date), 'seconds')
        if (this.diff == 60) clearInterval(this.timer)
      }, 1000)
    },
    refresh() {
      this.loading = true
      this.diff = null
      axios.get('/admin/settings/license')
        .then((response) => {
          this.license = response.data.license
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else {
            EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
            this.license = error.response.data.license
          }
        })
        .finally(() => {
          this.checkLicense()
          this.loading = false
        })
    }
  }
}
</script>