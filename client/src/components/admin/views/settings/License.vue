<template>
  <v-flex xs12 style="margin:5px">
    <div class="text-h6 font-weight-regular"><v-icon small style="margin-right:10px; margin-bottom:3px; color:#fa8131">fas fa-certificate</v-icon>LICENSE</div>
    <div class="body-1 font-weight-regular" style="margin-top:10px">This copy of Meteor Next is <span class="body-1 font-weight-medium" style="color:#00b16a">LICENSED</span>.</div>
    <v-text-field readonly :loading="loading" v-model="license.email" label="Email" style="margin-top:15px" required :rules="[v => !!v || '']"></v-text-field>
    <v-text-field readonly :loading="loading" v-model="license.key" label="Key" style="padding-top:0px" @click:append="show_key = !show_key" :append-icon="show_key ? 'visibility' : 'visibility_off'" :type="show_key ? 'text' : 'password'" required :rules="[v => !!v || '']"></v-text-field>
    <v-text-field readonly :loading="loading" v-model="resources" label="Resources" style="padding-top:0px" required :rules="[v => !!v || '']"></v-text-field>
    <v-text-field readonly :loading="loading" v-model="license.expiration" label="Expiration" style="padding-top:0px" required :rules="[v => !!v || '']"></v-text-field>
    <v-switch readonly :loading="loading" v-model="renewal" label="Automatic Renewal" color="#00b16a" style="padding-top:0px; margin-top:0px" hide-details></v-switch>
    <v-btn @click="refresh" :loading="loading" color="info" style="margin-top:20px"><v-icon small style="margin-right:10px">fas fa-spinner</v-icon>Refresh</v-btn>
  </v-flex>
</template>

<script>
export default {
  data: () => ({
    renewal: true,
    license: {},
    show_key: false,
    loading: false,
  }),
  props: ['info','init'],
  created() {
    if (Object.keys(this.info).length > 0) this.license = JSON.parse(JSON.stringify(this.info))
  },
  computed: {
    resources() {
      if (this.license.resources == -1) return 'Unlimited'
      return this.license.resources + (this.license.resources == 1 ? ' Server' : ' Servers') + ' / User'
    },
  },
  watch: {
    info: function(val) {
      this.license = JSON.parse(JSON.stringify(val))
    },
    init: function(val) {
      this.loading = val
    }
  },
  methods: {
    refresh() {
      this.loading = true
      // axios.get('/admin/settings')
      //   .then((response) => {
      //     this.settings = response.data.settings
      //   })
      //   .catch((error) => {
      //     if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
      //     else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
      //   })
      //   .finally(() => this.loading = false)
    }
  }
}
</script>