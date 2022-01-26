<template>
  <v-flex xs12 style="margin:5px">
    <div class="text-h6 font-weight-regular" style="margin-bottom:10px;"><v-icon small style="margin-right:10px; margin-bottom:3px; color:#fa8131">fas fa-meteor</v-icon>DEPLOYMENTS</div>
    <div class="body-1 font-weight-regular" style="margin-top:10px; margin-bottom:15px">The amount of days to keep the deployments results before being automatically removed.</div>
    <v-form ref="deployments_form">
      <v-select :loading="loading" :disabled="loading" v-model="deployments.retention" :items="[{id: '0', text: 'Never'}, {id: '1', text: '1 Day'}, {id: '7', text: '1 Week'}, {id: '30', text: '1 Month'}, {id: '90', text: '3 Months'}, {id: '180', text: '6 Months'}, {id: '365', text: '1 Year'}]" item-value="id" item-text="text" label="Retention Days" style="margin-top:15px" hide-details></v-select>
    </v-form>
    <div style="margin-top:20px">
      <v-btn :disabled="loading" color="#00b16a" @click="saveDeployments()"><v-icon small style="margin-right:10px">fas fa-save</v-icon>SAVE</v-btn>
    </div>
    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </v-flex>
</template>

<script>
import axios from 'axios'

export default {
  data: () => ({
    deployments: {},
    loading: false,
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarColor: '',
    snackbarText: ''
  }),
  props: ['info','init'],
  mounted() {
    if (Object.keys(this.info).length > 0) this.deployments = JSON.parse(JSON.stringify(this.info))
  },
  watch: {
    info: function(val) {
      this.deployments = JSON.parse(JSON.stringify(val))
    },
    init: function(val) {
      this.loading = val
    }
  },
  methods: {
    saveDeployments() {
      // Check if all fields are filled
      if (!this.$refs.deployments_form.validate()) {
        this.notification('Please fill the required fields', '#EF5354')
        return
      }
      // Disable the fields while updating fields to the DB
      this.loading = true
      // Construct path & payload
      const payload = { name: 'DEPLOYMENTS', value: this.deployments }
      // Update Deployments values to the DB
      axios.post('/admin/settings', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    },
  }
}
</script>