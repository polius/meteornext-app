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
      <!-- <v-btn @click="refresh" color="info" style="margin-top:20px; margin-left:5px">SHOW USAGE</v-btn> -->
    <!-- 
    <v-dialog v-model="dialog" max-width="90%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:3px">fas fa-rss</v-icon>USERS</v-toolbar-title>
          <v-divider class="mx-3" inset vertical></v-divider>
          <v-text-field v-model="search" append-icon="search" label="Search" color="white" style="margin-left:5px; width:calc(100% - 640px)" single-line hide-details></v-text-field>
          <v-divider class="mx-3" inset vertical style="margin-right:5px!important;"></v-divider>
          <v-btn icon @click="dialog = false" style="width:40px; height:40px"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:0px;">
          <v-container style="padding:0px; max-width:100%!important">
            <v-layout wrap>
              <v-flex xs12>
                <v-data-table :headers="usersHeaders" :items="usersItems" :search="usersSearch" :loading="loading" item-key="id" class="elevation-1" style="margin-top:0px;">
                  <template v-slot:[`item.event`]="{ item }">
                    <v-row no-gutters align="center" style="height:100%">
                      <v-col cols="auto" :style="`width:4px; height:100%; margin-right:10px; background-color:` + getEventColor(item.event)">
                      </v-col>
                      <v-col cols="auto" class="mr-auto">
                        {{ item.event.toUpperCase() }}
                      </v-col>
                      <v-col v-if="item.event == 'parameters'" cols="auto" style="margin-left:10px">
                        <v-btn small @click="eventDetails(item)">Details</v-btn>
                      </v-col>
                    </v-row>
                  </template>
                  <template v-slot:[`item.message`]="{ item }">
                    {{ getEventMessage(item) }}
                  </template>
                  <template v-slot:[`item.time`]="{ item }">
                    {{ dateFormat(item.time) }}
                  </template>
                </v-data-table>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    -->
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
    // Dialog
    dialog: false,
    search: '',
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
      if (this.license.resources === undefined) return ''
      if (this.license.resources == -1) return 'Unlimited'
      return this.license.resources + (this.license.resources == 1 ? ' Server' : ' Servers') + ' / User'
    },
    expiration() {
      if (this.license.expiration === undefined) return ''
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