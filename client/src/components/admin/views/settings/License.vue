<template>
    <v-flex xs12 style="margin:5px">
      <div class="text-h6 font-weight-regular"><v-icon small style="margin-right:10px; margin-bottom:3px; color:#fa8131">fas fa-certificate</v-icon>LICENSE</div>
      <div class="body-1 font-weight-regular" style="margin-top:10px">This copy of Meteor Next is <span class="body-1 font-weight-medium" style="color:#00b16a">LICENSED</span>.</div>
      <v-text-field readonly :loading="loading" v-model="license.account" label="Account" style="margin-top:15px"></v-text-field>
      <v-text-field readonly :loading="loading" v-model="resources" label="Resources" style="padding-top:0px"></v-text-field>
      <v-text-field readonly :loading="loading" v-model="license.access_key" label="Access Key" style="margin-top:0px" @click:append="show_access_key = !show_access_key" :append-icon="show_access_key ? 'visibility' : 'visibility_off'" :type="show_access_key ? 'text' : 'password'"></v-text-field>
      <v-text-field readonly :loading="loading" v-model="license.secret_key" label="Secret Key" style="padding-top:0px" @click:append="show_secret_key = !show_secret_key" :append-icon="show_secret_key ? 'visibility' : 'visibility_off'" :type="show_secret_key ? 'text' : 'password'" hide-details></v-text-field>
      <!-- <v-btn @click="refresh" :loading="loading || diff == null" :disabled="diff == null || diff < 60" color="info" style="margin-top:20px"><v-icon small style="margin-right:10px">fas fa-spinner</v-icon>{{ `Refresh ${diff == null || diff >= 60 ? '' : '- Wait ' + (60-diff) + ' seconds'}` }}</v-btn> -->
      <!-- <v-btn @click="getUsage" text :disabled="diff == null" style="margin-top:20px; margin-left:5px">SHOW USAGE</v-btn> -->
      <!-- <v-btn @click="manageLicense" text :disabled="diff == null" style="margin-top:20px; margin-left:5px">MANAGE LICENSE</v-btn> -->
      <!-- DIALOG -->
      <v-dialog v-model="dialog" width="1024px">
        <v-card>
          <v-toolbar dense flat color="primary">
            <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-chart-bar</v-icon>USAGE</v-toolbar-title>
            <v-divider class="mx-3" inset vertical></v-divider>
            <v-btn text class="body-2" @click="filterBy('all')" :style="`height:100%; ${filter == 'all' ? 'font-weight:600' : 'font-weight:400'}`">ALL</v-btn>
            <v-btn text class="body-2" @click="filterBy('exceeded')" :style="`height:100%; ${filter == 'exceeded' ? 'font-weight:600' : 'font-weight:400'}`">EXCEEDED</v-btn>
            <v-btn text class="body-2" @click="filterBy('not_exceeded')" :style="`height:100%; ${filter == 'not_exceeded' ? 'font-weight:600' : 'font-weight:400'}`">NOT EXCEEDED</v-btn>
            <v-divider class="mx-3" inset vertical></v-divider>
            <v-text-field v-model="search" append-icon="search" label="Search" color="white" style="margin-left:5px; width:calc(100% - 640px)" single-line hide-details></v-text-field>
            <v-divider class="mx-3" inset vertical style="margin-right:5px!important;"></v-divider>
            <v-btn icon @click="dialog = false" style="width:40px; height:40px"><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn>
          </v-toolbar>
          <v-card-text style="padding:0px;">
            <v-container style="padding:0px; max-width:100%!important">
              <v-layout wrap>
                <v-flex xs12>
                  <v-data-table :headers="headers" :items="items" :search="search" :loading="loading" item-key="username" class="elevation-1" style="margin-top:0px" mobile-breakpoint="0">
                    <template v-slot:[`item.servers`]="{ item }">
                      <div style="padding-right:18px">{{ item.servers }}</div>
                    </template>
                    <template v-slot:[`item.resources`]="{ item }">
                      <div style="padding-right:18px">{{ item.resources == -1 ? 'Unlimited' : item.resources }}</div>
                    </template>
                    <template v-slot:[`item.exceeded`]="{ item }">
                      <v-icon small :title="!item.exceeded ? 'This user has no resources disabled' : 'This user has resources disabled'" :color="!item.exceeded ? '#00b16a' : '#EF5354'" style="margin-right:8px; font-size:17px">{{ !item.exceeded ? 'fas fa-check-circle' : 'fas fa-exclamation-circle' }}</v-icon>
                    </template>
                    <template v-slot:[`footer.prepend`]>
                      <div v-if="expiredResources" class="text-body-2 font-weight-regular" style="margin:10px"><v-icon small color="warning" style="margin-right:10px; margin-bottom:2px">fas fa-exclamation-triangle</v-icon>Some users have disabled resources. Consider the possibility of upgrading your license.</div>
                    </template>
                  </v-data-table>
                </v-flex>
              </v-layout>
            </v-container>
          </v-card-text>
        </v-card>
      </v-dialog>
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
    show_access_key: false,
    show_secret_key: false,
    loading: true,
    // Dialog
    dialog: false,
    search: '',
    filter: 'all',
    headers: [
      { text: 'Username', align: 'left', value: 'username' },
      { text: 'Servers owned', align: 'center', value: 'servers'},
      { text: 'Maximum allowed servers', align: 'center', value: 'resources'},
      { text: 'Resources exceeded', align: 'center', value: 'exceeded'}
    ],
    usage: [],
    items: [],
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
    expiredResources() {
      return this.usage.some(x => x.exceeded)
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
          EventBus.$emit('send-notification', 'License refreshed', '#00b16a')
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else {
            EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
            this.license = error.response.data.license
          }
        })
        .finally(() => {
          this.checkLicense()
          this.loading = false
        })
    },
    getUsage() {
      this.loading = true
      this.dialog = true
      axios.get('/admin/settings/license/usage')
        .then((response) => {
          this.usage = response.data.usage
          this.items = response.data.usage
        })
        .catch((error) => {
          if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    manageLicense() {
      window.open('https://account.meteornext.io', '_blank').focus()
    },
    filterBy(val) {
      this.filter = val
      if (val == 'all') this.items = this.usage.slice(0)
      else if (val == 'exceeded') this.items = this.usage.filter(x => x.exceeded)
      else if (val == 'not_exceeded') this.items = this.usage.filter(x => !x.exceeded)
    },
  }
}
</script>