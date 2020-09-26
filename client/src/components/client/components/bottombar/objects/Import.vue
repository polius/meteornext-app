<template>
  <div>
    <v-dialog v-model="dialog" persistent max-width="70%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">Import SQL</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="dialog = false" icon><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form @submit.prevent ref="dialogForm" style="margin-top:0px; margin-bottom:15px;">
                  <v-file-input v-model="file" outlined show-size accept=".sql" label="Click to select a .sql file" hide-details style="padding:0px"></v-file-input>
                    <div v-if="start" style="margin-top:15px">
                      <v-progress-linear :value="progress" rounded color="primary" height="25">
                        <template v-slot="{ value }">
                          {{ 'Uploading: ' + Math.ceil(value) }}%
                        </template>
                      </v-progress-linear>
                      <div class="body-1" style="margin-top:10px">
                        <v-icon v-if="step == 'success'" title="Success" small style="color:rgb(0, 177, 106); padding-bottom:2px;">fas fa-check-circle</v-icon>
                        <v-icon v-else-if="step == 'fail'" title="Failed" small style="color:rgb(231, 76, 60); padding-bottom:2px;">fas fa-times-circle</v-icon>
                        <v-icon v-else-if="step == 'stop'" title="Stopped" small style="color:#fa8231; padding-bottom:2px;">fas fa-exclamation-circle</v-icon>
                        <v-progress-circular v-else indeterminate size="16" width="2" color="primary" style="margin-top:-2px"></v-progress-circular>
                        <span style="margin-left:8px">{{ text }}</span>  
                      </div>
                      <v-card v-if="error.length != 0" style="margin-top:10px">
                        <v-card-text>
                          <div class="body-1">{{ error }}</div>
                        </v-card-text>
                      </v-card>
                    </div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn v-if="progress == 0 || ['success','fail','stop'].includes(step)" :loading="loading" @click="importSubmit" color="primary">Import</v-btn>
                      <v-btn v-else @click="cancelImport" color="#e74c3c">Cancel</v-btn>
                    </v-col>
                    <v-col style="margin-bottom:10px;">
                      <v-btn :disabled="loading" @click="dialog = false" outlined color="#e74d3c">Close</v-btn>
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
      step: 'upload', 
      progress: 0, 
      start: false, 
      error: '',
      // Axios Cancel Token
      cancelToken: null,
    }
  },
  computed: {
    ...mapFields([
      'server',
      'database',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('SHOW_BOTTOMBAR_OBJECTS_IMPORT', this.showDialog);
  },
  methods: {
    showDialog() {
      // Init vars
      this.start = false
      this.file = null
      this.dialog = true
    },
    importSubmit() {
      // Check input file
      if (!this.file) {
        EventBus.$emit('SEND_NOTIFICATION', 'Please select a file', 'info')
        return
      }
      // Init vars
      this.loading = true
      this.progress = 0
      this.text = 'Uploading file...' 
      this.error = ''
      this.step = 'upload'
      // Build import
      const data = new FormData();
      data.append('server', this.server.id)
      data.append('database', this.database)
      data.append('file', this.file)
      // Build request options
      const CancelToken = axios.CancelToken;
      this.cancelToken = CancelToken.source();
      const options = {
        onUploadProgress: (progressEvent) => {
          var percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          this.progress = percentCompleted
          if (this.progress == 100) {
            this.step = 'processing'
            this.text = 'Processing file... Please wait.'
          }
        },
        cancelToken: this.cancelToken.token
      }
      // Start import
      this.start = true
      axios.post('client/import', data, options)
        .then(() => {
          return new Promise((resolve, reject) => { 
            EventBus.$emit('REFRESH_SIDEBAR_OBJECTS', resolve, reject)
          }).then(() => {
            // Show success
            this.step = 'success'
            this.text = 'File successfully imported.'
            // Disable loading
            this.loading = false
          }).catch(() => {})
        }).catch((error) => {
          if (axios.isCancel(error)) {
            return new Promise((resolve, reject) => { 
              EventBus.$emit('REFRESH_SIDEBAR_OBJECTS', resolve, reject)
            }).then(() => {
              this.step = 'stop'
              this.text = 'Import stopped.'
              this.error = ''
              this.loading = false
            })
          }
          else if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else {
            return new Promise((resolve, reject) => { 
              EventBus.$emit('REFRESH_SIDEBAR_OBJECTS', resolve, reject)
            }).then(() => {
              this.step = 'fail'
              this.text = 'An error occurred importing the file.'
              this.error = error.response.data.message
              this.loading = false
            }) 
          }
        })
    },
    cancelImport() {
      EventBus.$emit('SEND_NOTIFICATION', 'Stopping the import process...', 'warning')
      this.cancelToken.cancel()
    },
  }
}
</script>