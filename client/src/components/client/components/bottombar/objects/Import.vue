<template>
  <div>
    <v-dialog v-model="dialog" persistent max-width="70%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="padding-right:10px; padding-bottom:3px">fas fa-arrow-up</v-icon>IMPORT SQL</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="dialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form @submit.prevent ref="dialogForm" style="margin-top:0px; margin-bottom:15px;">
                  <v-card>
                    <v-row no-gutters align="center" justify="center">
                      <v-col cols="auto" style="display:flex; margin:15px">
                        <v-icon size="20" color="info">fas fa-info-circle</v-icon>
                      </v-col>
                      <v-col>
                        <div class="text-body-1" style="color:#e2e2e2">To import files larger than 10 MB use the Utils section.</div>
                      </v-col>
                    </v-row>
                  </v-card>
                  <v-file-input :disabled="step == 'success'" v-model="file" dense outlined show-size accept=".sql" label="Click to select a .sql file" truncate-length="100" hide-details style="margin-top:20px"></v-file-input>
                  <div v-if="start" style="margin-top:15px">
                    <v-progress-linear v-if="!(['success','fail','stop'].includes(step))" :value="progress" rounded color="primary" height="25">
                      <template v-slot="{ value }">
                        {{ (progress == 100) ? 'Importing... Please wait, It might take several minutes to finish.' : 'Uploading: ' + Math.ceil(value) + '%' }}
                      </template>
                    </v-progress-linear>
                    <div class="body-1" style="margin-top:10px">
                      <v-row no-gutters>
                        <v-col cols="auto">
                          <v-icon v-if="step == 'success'" title="Success" small style="color:rgb(0, 177, 106); padding-bottom:2px;">fas fa-check-circle</v-icon>
                          <v-icon v-else-if="step == 'fail'" title="Failed" small style="color:#EF5354; padding-bottom:2px;">fas fa-times-circle</v-icon>
                          <v-icon v-else-if="step == 'stop'" title="Stopped" small style="color:#fa8231; padding-bottom:2px;">fas fa-exclamation-circle</v-icon>
                          <v-progress-circular v-else indeterminate size="16" width="2" color="primary" style="margin-top:-2px"></v-progress-circular>
                        </v-col>
                        <v-col style="margin-left:8px">
                          <span>{{ text }}</span>
                        </v-col>
                        <!-- <v-col v-if="progressTimeValue != null" class="flex-grow-0 flex-shrink-0">
                          <div class="body-1">{{ progressTimeValue.format('HH:mm:ss') }}</div>
                        </v-col> -->
                      </v-row>
                    </div>
                    <v-card v-if="error.length != 0" style="margin-top:10px">
                      <v-card-text>
                        <div class="body-1">{{ error }}</div>
                      </v-card-text>
                    </v-card>
                  </div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px; margin-bottom:10px;">
                  <v-row no-gutters>
                    <v-col v-show="step == 'success'" style="margin-right:5px">
                      <v-btn :disabled="loading" @click="dialog = false" color="primary">Close</v-btn>
                    </v-col>
                    <v-col v-show="step != 'success'" style="margin-right:5px">
                      <v-btn :loading="loading" @click="importSubmit" color="#00b16a" style="margin-right:5px">Import</v-btn>
                      <v-btn v-if="['upload','processing','stopping'].includes(step)" :loading="step == 'stopping'" @click="cancelImport" color="#EF5354">Cancel</v-btn>
                      <v-btn v-else :disabled="loading" @click="dialog = false" color="#EF5354">Cancel</v-btn>
                    </v-col>
                  </v-row>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
  </div>
</template>

<script>
import axios from 'axios'
import moment from 'moment'
import EventBus from '../../../js/event-bus'
import { mapFields } from '../../../js/map-fields'

export default {
  data() {
    return {
      loading: false,
      // Dialog
      dialog: false,
      file: null, 
      text: 'Uploading file...', 
      step: 'import', 
      progress: 0, 
      progressTimeEvent: null,
      progressTimeValue: null,
      start: false, 
      error: '',
      // Axios Abort Controller
      abortController: null,
    }
  },
  computed: {
    ...mapFields([
      'dialogOpened',
    ], { path: 'client/client' }),
    ...mapFields([
      'index',
      'id',
      'server',
      'database',
    ], { path: 'client/connection' }),
  },
  activated() {
    EventBus.$on('show-bottombar-objects-import', this.showDialog);
  },
  watch: {
    dialog: function(val) {
      this.dialogOpened = val
    },
  },
  methods: {
    showDialog() {
      // Init vars
      this.start = false
      this.step = 'import'
      this.file = null
      this.dialog = true
    },
    importSubmit() {
      // Check input file
      if (!this.file) {
        EventBus.$emit('send-notification', 'Please select a file', 'info')
        return
      }
      // Check input file size
      if (this.file.size/1024/1024 > 10) {
        EventBus.$emit('send-notification', 'The upload file exceeds the maximum allowed size (10 MB)', '#EF5354')
        return
      }
      // Init vars
      this.loading = true
      this.progress = 0
      this.text = '[1/2] Uploading file...'
      this.error = ''
      this.step = 'upload'
      // Build import
      const data = new FormData();
      data.append('connection', this.id + '-shared')
      data.append('server', this.server.id)
      data.append('database', this.database)
      data.append('file', this.file)
      // Build request options
      this.abortController = new AbortController()
      const options = {
        onUploadProgress: (progressEvent) => {
          var percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          this.progress = percentCompleted
          if (this.progress == 100) {
            this.step = 'processing'
            this.text = '[2/2] Importing file...'
          }
        },
        signal: this.abortController.signal
      }
      // Start Timer
      this.progressTimeValue = moment().startOf("day");
      this.progressTimeEvent = setInterval(() => requestAnimationFrame(() => this.progressTimeValue.add(1, 'second')), 1000)
      // Start import
      this.start = true
      axios.post('client/import', data, options)
        .then(() => {
          return new Promise((resolve, reject) => { 
            EventBus.$emit('refresh-sidebar-objects', resolve, reject)
          }).then(() => {
            // Show success
            this.step = 'success'
            this.text = 'Import finished successfully.'
            // Disable loading
            this.loading = false
          }).catch(() => {})
        }).catch((error) => {
          if (axios.isCancel(error)) {
            return new Promise((resolve, reject) => { 
              EventBus.$emit('refresh-sidebar-objects', resolve, reject)
            }).then(() => {
              this.step = 'stop'
              this.text = 'Import stopped.'
              this.error = ''
              this.loading = false
            })
          }
          else if ([401,404,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else {
            return new Promise((resolve, reject) => { 
              EventBus.$emit('refresh-sidebar-objects', resolve, reject)
            }).then(() => {
              this.step = 'fail'
              this.text = 'An error occurred importing the file.'
              this.error = error.response.data.message
              this.loading = false
            }) 
          }
        })
        .finally(() => clearInterval(this.progressTimeEvent))
    },
    cancelImport() {
      this.step = 'stopping'
      this.abortController.abort()
    },
  }
}
</script>