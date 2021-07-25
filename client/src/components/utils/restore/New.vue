<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="subtitle-1"><v-icon small style="margin-right:10px">fas fa-plus</v-icon>NEW RESTORE</v-toolbar-title>
        <v-spacer></v-spacer>
        <router-link class="nav-link" to="/utils/restore"><v-btn icon><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn></router-link>
      </v-toolbar>
      <v-container fluid grid-list-lg style="padding:0px; margin-bottom:10px">
        <v-layout row wrap>
          <v-flex xs12 style="padding-bottom:0px">
            <v-stepper v-model="stepper" vertical style="padding-bottom:10px; background-color:#424242">
              <v-stepper-step :complete="stepper > 1" step="1">SOURCE</v-stepper-step>
              <v-stepper-content step="1" style="padding-top:0px; padding-left:10px">
                <v-card style="margin:5px">
                  <v-card-text>
                    <v-form ref="sourceForm" @submit.prevent>
                      <div class="text-body-1">Choose a restoring method:</div>
                      <v-radio-group v-model="mode" style="margin-top:10px; margin-bottom:20px" hide-details>
                        <v-radio value="file">
                          <template v-slot:label>
                            <div>File</div>
                          </template>
                        </v-radio>
                        <v-radio value="url">
                          <template v-slot:label>
                            <div>URL</div>
                          </template>
                        </v-radio>
                        <v-radio disabled value="s3">
                          <template v-slot:label>
                            <div>Amazon S3</div>
                          </template>
                        </v-radio>
                      </v-radio-group>
                      <div v-if="mode == 'file'">
                        <v-file-input v-model="fileObject" label="File" accept=".sql,.tar,.gz" :rules="[v => !!v || '']" prepend-icon truncate-length="1000" style="padding-top:8px" hide-details></v-file-input>
                      </div>
                      <div v-else-if="mode == 'url'">
                        <v-text-field @keyup.enter="inspectURL" v-model="url" label="URL" :rules="[v => this.validURL(v) || '' ]" style="padding-top:8px" hide-details></v-text-field>
                      </div>
                      <div v-if="size != null" class="text-body-1" style="margin-top:20px; color:#fa8131">File Size: <span style="font-weight:500">{{ formatBytes(size) }}</span></div>
                      <div v-if="inspect.items.length > 0" style="margin-top:15px">
                        <div class="text-body-1">Choose the files to restore:</div>
                        <v-toolbar dense flat color="#2e3131" style="margin-top:15px; border-top-left-radius:5px; border-top-right-radius:5px;">
                          <v-text-field v-model="inspectSearch" append-icon="search" label="Search" color="white" single-line hide-details style="padding-right:10px"></v-text-field>
                        </v-toolbar>
                        <v-data-table v-model="inspectSelected" :headers="inspectHeaders" :items="inspect.items" :search="inspectSearch" :hide-default-footer="inspect.items.length < 11" :loading="loading" loading-text="Loading... Please wait" item-key="file" show-select class="elevation-1">
                          <template v-ripple v-slot:[`header.data-table-select`]="{}">
                            <v-simple-checkbox
                              :value="inspect.items.length == 0 ? false : inspectSelected.length == inspect.items.length"
                              :indeterminate="inspectSelected.length > 0 && inspectSelected.length != inspect.items.length"
                              @click="inspectSelected.length == inspect.items.length ? inspectSelected = [] : inspectSelected = JSON.parse(JSON.stringify(inspect.items))">
                            </v-simple-checkbox>
                          </template>
                          <template v-slot:[`item.size`]="{ item }">
                            {{ formatBytes(item.size) }}
                          </template>
                        </v-data-table>
                        <div class="text-body-1" style="margin-top:20px; color:#fa8131">Selected Size: <span style="font-weight:500">{{ formatBytes(inspectSelected.reduce((a, b) => a + b.size, 0)) }}</span></div>
                      </div>
                    </v-form>
                    <div style="margin-top:20px">
                      <v-btn :disabled="inspect.items.length > 0 && inspectSelected.length == 0" :loading="loading" color="primary" @click="nextStep">CONTINUE</v-btn>
                      <router-link :disabled="loading" to="/utils/restore"><v-btn text style="margin-left:5px">CANCEL</v-btn></router-link>
                    </div>
                  </v-card-text>
                </v-card>
              </v-stepper-content>
              <v-stepper-step :complete="stepper > 2" step="2">DESTINATION</v-stepper-step>
              <v-stepper-content step="2" style="padding-top:0px; padding-left:10px">
                <v-card style="margin:5px">
                  <v-card-text>
                    <v-form ref="destinationForm" @submit.prevent>
                      <v-autocomplete ref="server" v-model="server" :items="serverItems" item-value="id" item-text="name" label="Server" :rules="[v => !!v || '']" style="padding-top:8px">
                        <template v-slot:[`selection`]="{ item }">
                          <v-icon small :color="item.shared ? '#EB5F5D' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          {{ item.name }}
                        </template>
                        <template v-slot:[`item`]="{ item }">
                          <v-icon small :color="item.shared ? '#EB5F5D' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          {{ item.name }}
                        </template>
                      </v-autocomplete>
                      <v-text-field ref="database" @keyup.enter="nextStep" v-model="database" label="Database" :rules="[v => !!v || '']" style="padding-top:6px" hide-details></v-text-field>
                    </v-form>
                    <v-row no-gutters style="margin-top:20px;">
                      <v-col cols="auto" class="mr-auto">
                        <v-btn color="primary" @click="nextStep">CONTINUE</v-btn>
                        <v-btn text @click="stepper = 1" style="margin-left:5px">CANCEL</v-btn>
                      </v-col>
                      <v-col cols="auto">
                        <v-btn :disabled="server.length == 0" text>SERVER DETAILS</v-btn>
                      </v-col>
                    </v-row>
                  </v-card-text>
                </v-card>
              </v-stepper-content>
              <v-stepper-step step="3">OVERVIEW</v-stepper-step>
              <v-stepper-content step="3" style="margin:0px; padding:0px 10px 0px 0px">
                <div style="margin-left:10px">
                  <v-card style="margin:5px">
                    <v-toolbar dense flat color="#2e3131">
                      <v-toolbar-title class="subtitle-1">SOURCE</v-toolbar-title>
                    </v-toolbar>
                    <v-card-text>
                      <div class="subtitle-1 white--text">METHOD</div>
                      <v-radio-group v-model="mode" readonly style="margin-top:10px; margin-bottom:20px" hide-details>
                        <v-radio value="file">
                          <template v-slot:label>
                            <div>File</div>
                          </template>
                        </v-radio>
                        <v-radio value="url">
                          <template v-slot:label>
                            <div>URL</div>
                          </template>
                        </v-radio>
                        <v-radio value="s3">
                          <template v-slot:label>
                            <div>Amazon S3</div>
                          </template>
                        </v-radio>
                      </v-radio-group>
                      <div v-if="mode == 'file'">
                        <v-text-field readonly v-model="file" label="File" style="padding-top:8px" hide-details></v-text-field>
                      </div>
                      <div v-else-if="mode == 'url'">
                        <v-text-field readonly v-model="url" label="URL" style="padding-top:8px" hide-details></v-text-field>
                      </div>
                      <div class="text-body-1" style="margin-top:20px; color:#fa8131">File Size: <span style="font-weight:500">{{ formatBytes(size) }}</span></div>
                      <div v-if="inspect.items.length > 0" style="margin-top:15px">
                        <v-toolbar dense flat color="#2e3131" style="margin-top:15px; border-top-left-radius:5px; border-top-right-radius:5px;">
                          <v-text-field v-model="inspectSearch" append-icon="search" label="Search" color="white" single-line hide-details style="padding-right:10px"></v-text-field>
                        </v-toolbar>
                        <v-data-table readonly :headers="inspectHeaders" :items="inspectSelected" :search="inspectSearch" :hide-default-footer="inspect.items.length < 11" :loading="loading" loading-text="Loading... Please wait" item-key="file" class="elevation-1" style="margin-top:15px;">
                          <template v-slot:[`item.size`]="{ item }">
                            {{ formatBytes(item.size) }}
                          </template>
                        </v-data-table>
                        <div class="text-body-1" style="margin-top:20px; color:#fa8131">Selected Size: <span style="font-weight:500">{{ formatBytes(inspectSelected.reduce((a, b) => a + b.size, 0)) }}</span></div>
                      </div>
                    </v-card-text>
                  </v-card>
                  <v-card style="margin:10px 5px 5px 5px">
                    <v-toolbar dense flat color="#2e3131">
                      <v-toolbar-title class="subtitle-1">DESTINATION</v-toolbar-title>
                    </v-toolbar>
                    <v-card-text>
                      <v-autocomplete readonly v-model="server" :items="serverItems" item-value="id" item-text="name" label="Server" :rules="[v => !!v || '']" style="padding-top:8px">
                        <template v-slot:[`selection`]="{ item }">
                          <v-icon small :color="item.shared ? '#EB5F5D' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          {{ item.name }}
                        </template>
                        <template v-slot:[`item`]="{ item }">
                          <v-icon small :color="item.shared ? '#EB5F5D' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                          {{ item.name }}
                        </template>
                      </v-autocomplete>
                      <v-text-field readonly v-model="database" label="Database" :rules="[v => !!v || '']" style="padding-top:6px" hide-details></v-text-field>
                    </v-card-text>
                  </v-card>
                </div>
                <div style="margin-left:15px; margin-top:20px; margin-bottom:5px">
                  <v-btn :disabled="loading" :loading="loading" @click="submitRestore" color="#00b16a">RESTORE</v-btn>
                  <v-btn :disabled="loading" @click="stepper = 2" color="#EF5354" style="margin-left:5px">CANCEL</v-btn>
                </div>
              </v-stepper-content>
            </v-stepper>
          </v-flex>
        </v-layout>
      </v-container>
    </v-card>
    <v-dialog v-model="dialog" persistent max-width="640px">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; margin-bottom:2px">fas fa-spinner</v-icon>UPLOADING</v-toolbar-title>
        </v-toolbar>
        <v-card-text style="padding:0px">
          <v-container style="padding:0px">
            <v-layout wrap>
              <v-flex xs12 style="padding:15px">
                <div class="text-body-1">{{ progress != 100 ? 'Uploading file. Please wait...' : 'File successfully uploaded.' }}</div>
                <v-progress-linear :color="progress != 100 ? 'info' : '#00b16a'" height="5" :value="progress" style="margin-top:10px"></v-progress-linear>
                <v-card style="margin-top:10px">
                  <v-card-text>
                    <div class="text-body-1">
                      <div><span class="white--text">Progress: <span style="color:#fa8131; font-weight:500">{{ `${progress} % `}}</span></span>{{ progressText }}</div>
                    </div>
                  </v-card-text>
                </v-card>
                <v-divider style="margin-top:15px"></v-divider>
                <div style="margin-top:15px">
                  <v-btn :disabled="progress == 100" @click="cancelImport" color="#EF5354">CANCEL</v-btn>
                </div>
              </v-flex>
            </v-layout>
          </v-container>
        </v-card-text>
      </v-card>
    </v-dialog>
    <v-snackbar v-model="snackbar" :multi-line="false" :timeout="snackbarTimeout" :color="snackbarColor" top style="padding-top:0px;">
      {{ snackbarText }}
      <template v-slot:action="{ attrs }">
        <v-btn color="white" text v-bind="attrs" @click="snackbar = false">Close</v-btn>
      </template>
    </v-snackbar>
  </div>
</template>

<style scoped>
::v-deep .v-toolbar__content {
  padding-right:5px;
}
</style>

<script>
import axios from 'axios';
import pretty from 'pretty-bytes';

export default {
  data() {
    return {
      loading: false,
      stepper: 1,
      // Source
      mode: 'file',
      file: '',
      size: null,
      fileObject: null,
      url: '',
      // Inspect
      inspect: { items: [] },
      inspectHeaders: [
        { text: 'File', value: 'file',  width: '10%' },
        { text: 'Size', value: 'size' },
      ],
      inspectSearch: '',
      inspectSelected: [],
      // Destination
      serverItems: [],
      server: '',
      database: '',
      // Dialog
      dialog: false,
      progress: 0,
      progressText: '',
      // Axios Cancel Token
      cancelToken: null,
      // Snackbar
      snackbar: false,
      snackbarTimeout: Number(3000),
      snackbarText: '',
      snackbarColor: '',
    }
  },
  created() {
    this.getServers()
  },
  watch: {
    mode() {
      requestAnimationFrame(() => {
        if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
      })
    },
    stepper(val) {
      if (val == 2) {
        requestAnimationFrame(() => {
          if (typeof this.$refs.server !== 'undefined') this.$refs.server.focus()
        })
      }
      if (val == 3) {
        requestAnimationFrame(() => {
          if (typeof this.$refs.server !== 'undefined') this.$refs.server.blur()
          if (typeof this.$refs.database !== 'undefined') this.$refs.database.blur()
        })
      }
    },
    server() {
      requestAnimationFrame(() => {
        if (typeof this.$refs.server !== 'undefined') this.$refs.server.blur()
        if (typeof this.$refs.database !== 'undefined') this.$refs.database.focus()
        if (typeof this.$refs.destinationForm !== 'undefined') this.$refs.destinationForm.resetValidation()
      })
    },
    file(val) {
      this.size = val.size 
    },
    url() {
      if (this.inspect.items.length > 0) {
        this.inspectSearch = ''
        this.inspectSelected = []
        this.inspect = { items: [] }
        this.size = null
      }
    }
  },
  methods: {
    getServers() {
      this.loading = true
      axios.get('/restore/servers')
        .then((response) => {
          this.serverItems = response.data.servers
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
    },
    nextStep() {
      if (this.stepper == 1 && !this.$refs.sourceForm.validate()) return
      else if (this.stepper == 2 && !this.$refs.destinationForm.validate()) return
      if (this.stepper == 1 && this.mode == 'url') this.inspectURL()
      else this.stepper = this.stepper + 1
    },
    submitRestore() {
      if (this.mode == 'file') this.checkFileRestore()
      else if (this.mode == 'url') this.submitURLRestore()
    },
    checkFileRestore() {
      this.progress = 0
      this.progressText = ''
      this.dialog = true
      axios.get('/restore/check', { params: { size: this.size }})
        .then((response) => {
          if (!response.data.check) {
            this.notification('There is not enough space left to proceed with the restore.', '#EF5354')
            this.dialog = false
          }
          else this.submitFileRestore()
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
    },
    submitFileRestore() {
      // Build import
      const data = new FormData();
      data.append('mode', this.mode)
      data.append('file', this.fileObject)
      data.append('server', this.server)
      data.append('database', this.database)
      // Build request options
      const CancelToken = axios.CancelToken;
      this.cancelToken = CancelToken.source();
      const options = {
        onUploadProgress: (progressEvent) => {
          var percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          this.progress = percentCompleted
          this.progressText = '(' + this.formatBytes(progressEvent.loaded) + ' / ' + this.formatBytes(progressEvent.total) + ')'
        },
        cancelToken: this.cancelToken.token
      }
      // Start import
      this.start = true
      axios.post('restore', data, options)
      .then((response) => {
        if (this.progress == 100) {
          this.notification("File successfully uploaded.", "#00b16a")
          setTimeout(() => this.$router.push('/utils/restore/' + response.data.id), 1000)
        }
      })
      .catch((error) => {
        if (axios.isCancel(error)) {
          this.notification("The upload process has been stopped", "info")
          this.dialog = false
        }
        else if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
        else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
      })
    },
    inspectURL() {
      if (this.inspect.items.length > 0 && this.inspectSelected.length > 0) this.stepper = this.stepper + 1
      else {
        this.loading = true
        axios.get('restore/inspect', { params: { url: this.url }})
        .then((response) => {
          this.inspect = response.data.inspect
          this.size = this.inspect.size
          if (this.inspect.items.length == 0) this.nextStep()
        })
        .catch((error) => {
          if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
        })
        .finally(() => this.loading = false)
      }
    },
    submitURLRestore() {
      this.loading = true
      const payload = {
        mode: this.mode,
        url: this.url,
        selected: this.inspectSelected.map(x => x.file),
        server: this.server,
        database: this.database
      }
      axios.post('restore', payload)
      .then((response) => {
        this.$router.push('/utils/restore/' + response.data.id)
      })
      .catch((error) => {
        if ([401,422,503].includes(error.response.status)) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
        else this.notification(error.response.data.message !== undefined ? error.response.data.message : 'Internal Server Error', '#EF5354')
      })
      .finally(() => this.loading = false)
    },
    cancelImport() {
      this.cancelToken.cancel()
      this.dialog = false
    },
    formatBytes(size) {
      if (size == null) return null
      return pretty(size, {binary: true}).replace('i','')
    },
    validURL(str) {
      var pattern = new RegExp('^(https?:\\/\\/)?'+ // protocol
        '((([a-z\\d]([a-z\\d-]*[a-z\\d])*)\\.)+[a-z]{2,}|'+ // domain name
        '((\\d{1,3}\\.){3}\\d{1,3}))'+ // OR ip (v4) address
        '(\\:\\d+)?(\\/[-a-z\\d%_.~+]*)*'+ // port and path
        '(\\?[;&a-z\\d%_.~+=-]*)?'+ // query string
        '(\\#[-a-z\\d_]*)?$','i'); // fragment locator
      return !!pattern.test(str);
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  }
}
</script>