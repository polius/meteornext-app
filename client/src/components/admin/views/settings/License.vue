<template>
  <v-flex xs12 style="margin:5px">
    <div class="text-h6 font-weight-regular"><v-icon small style="margin-right:10px; margin-bottom:3px; color:#fa8131">fas fa-certificate</v-icon>LICENSE</div>
    <div class="body-1 font-weight-regular" style="margin-top:10px">This copy of Meteor Next is <span class="body-1 font-weight-medium" style="color:#00b16a;">LICENSED</span>.</div>
    <v-text-field readonly :loading="loading" :disabled="loading" v-model="license.email" label="Email" style="margin-top:15px" required :rules="[v => !!v || '']"></v-text-field>
    <v-text-field readonly :loading="loading" :disabled="loading" v-model="license.key" label="Key" style="padding-top:0px;" @click:append="show_key = !show_key" :append-icon="show_key ? 'visibility' : 'visibility_off'" :type="show_key ? 'text' : 'password'" required :rules="[v => !!v || '']"></v-text-field>
    <v-text-field readonly :loading="loading" :disabled="loading" v-model="license.expiration" label="Expiration" style="padding-top:0px; margin-bottom:5px" required :rules="[v => !!v || '']" hide-details></v-text-field>
  </v-flex>
</template>

<script>
export default {
  data: () => ({
    license: {},
    show_key: false,
    loading: false,
  }),
  props: ['info','init'],
  created() {
    if (Object.keys(this.info).length > 0) this.license = {...this.info}
  },
  watch: {
    info: function(val) {
      this.license = {...val}
    },
    init: function(val) {
      this.loading = val
    }
  }
}
</script>