<template>
  <v-flex xs12 style="margin:5px">
    <div class="text-h6 font-weight-regular" style="margin-bottom:10px;"><v-icon small style="margin-right:10px; margin-bottom:2px; color:#fa8131">fas fa-cog</v-icon>ADVANCED</div>
    <v-form ref="advanced_form">
      <div class="body-1 font-weight-regular" style="margin-top:10px; margin-bottom:15px">Perform automatic memory cleanups to free unused memory.</div>
      <div class="body-2 font-weight-regular" style="margin-top:10px; margin-bottom:15px">To maximize performance and reduce memory consumption it's recommended to enable this feature (preferable in non-working hours).</div>
      <v-switch :disabled="loading" v-model="advanced.memory_enabled" label="Enable Memory Cleanup" style="margin-top:15px" hide-details></v-switch>
      <div v-if="advanced.memory_enabled" style="margin-top:20px; margin-bottom:25px">
        <span class="body-1 font-weight-light white--text">Select the execution time.</span>
        <div @click="schedule_change">
          <v-text-field :disabled="loading" ref="schedule_time" filled readonly v-model="advanced.memory_time" label="Execution time" hide-details style="margin-top:15px; margin-bottom:15px"></v-text-field>
        </div>
        <span class="body-1 font-weight-light white--text">Select what days of the week the clean should execute.</span>
        <v-row no-gutters>
          <v-col cols="auto" style="width:150px">
            <v-checkbox :disabled="loading" v-model="advanced.memory_days" label="Monday" value="1" hide-details style="padding-top:0px"></v-checkbox>
          </v-col>
          <v-col cols="auto" style="width:150px">
            <v-checkbox :disabled="loading" v-model="advanced.memory_days" label="Tuesday" value="2" hide-details style="padding-top:0px"></v-checkbox>
          </v-col>
          <v-col cols="auto" style="width:150px">
            <v-checkbox :disabled="loading" v-model="advanced.memory_days" label="Wednesday" value="3" hide-details style="padding-top:0px"></v-checkbox>
          </v-col>
        </v-row>
        <v-row no-gutters>
          <v-col cols="auto" style="width:150px">
            <v-checkbox :disabled="loading" v-model="advanced.memory_days" label="Thursday" value="4" hide-details style="padding-top:0px"></v-checkbox>
          </v-col>
          <v-col cols="auto" style="width:150px">
            <v-checkbox :disabled="loading" v-model="advanced.memory_days" label="Friday" value="5" hide-details style="padding-top:0px"></v-checkbox>
          </v-col>
          <v-col cols="auto" style="width:150px">
            <v-checkbox :disabled="loading" v-model="advanced.memory_days" label="Saturday" value="6" hide-details style="padding-top:0px"></v-checkbox>
          </v-col>
        </v-row>
        <v-row no-gutters style="margin-bottom:15px">
          <v-col cols="auto" style="width:150px">
            <v-checkbox :disabled="loading" v-model="advanced.memory_days" label="Sunday" value="7" hide-details style="padding-top:0px"></v-checkbox>
          </v-col>
        </v-row>
      </div>
    </v-form>
    <div style="margin-top:20px">
      <v-btn :disabled="loading" color="#00b16a" @click="saveAdvanced()"><v-icon small style="margin-right:10px">fas fa-save</v-icon>SAVE</v-btn>
    </div>
    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>

    <v-dialog v-model="scheduleDialog" persistent width="290px">
      <v-time-picker v-model="schedule_time" color="info" format="24hr" scrollable>
        <v-btn text color="info" @click="schedule_now">Now</v-btn>
        <v-spacer></v-spacer>
        <v-btn text color="#EF5354" @click="schedule_close">Cancel</v-btn>
        <v-btn text color="#00b16a" @click="schedule_submit">Confirm</v-btn>
      </v-time-picker>
    </v-dialog>
  </v-flex>
</template>

<script>
import axios from 'axios'
import moment from 'moment'

export default {
  data: () => ({
    advanced: {},
    schedule_week: [],
    scheduleDialog: false,
    schedule_time: '',
    loading: false,
    // Snackbar
    snackbar: false,
    snackbarTimeout: Number(3000),
    snackbarColor: '',
    snackbarText: ''
  }),
  props: ['info','init'],
  mounted() {
    if (Object.keys(this.info).length > 0) this.initAdvanced(this.info)
  },
  watch: {
    info: function(val) {
      this.initAdvanced(val)
    },
    init: function(val) {
      this.loading = val
    }
  },
  methods: {
    initAdvanced(val) {
      this.advanced = JSON.parse(JSON.stringify(val))
      this.advanced.memory_time = moment.utc(this.advanced.memory_time, 'HH:mm').local().format('HH:mm')
      this.advanced.memory_days = this.advanced.memory_days.map(x => x.toString())
    },
    saveAdvanced() {
      // Check if all fields are filled
      if (!this.$refs.advanced_form.validate()) {
        this.notification('Please fill the required fields', '#EF5354')
        return
      }
      // Disable the fields while updating fields to the DB
      this.loading = true
      // Construct path & payload
      const payload = {
        name: 'ADVANCED',
        value: {
          memory_enabled: this.advanced.memory_enabled,
          memory_time: moment(this.advanced.memory_time, 'HH:mm').utc().format('HH:mm'),
          memory_days: this.advanced.memory_days.map(x => parseInt(x)).sort()
        }
      }
      // Update Amazon values to the DB
      axios.post('/admin/settings', payload)
        .then((response) => {
          this.notification(response.data.message, '#00b16a')
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    schedule_close() {
      this.scheduleDialog = false
    },
    schedule_now() {
      const date = moment()
      this.schedule_time = date.format("HH:mm")
    },
    schedule_change() {
      if (this.loading) return
      this.schedule_time = this.advanced.memory_time
      this.scheduleDialog = true
    },
    schedule_submit() {
      this.advanced.memory_time = this.schedule_time
      this.scheduleDialog = false
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    },
  }
}
</script>