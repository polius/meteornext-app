<template>
  <div>
    <v-card>
      <v-toolbar dense flat color="primary">
        <v-toolbar-title class="subtitle-1"><v-icon small style="margin-right:10px">fas fa-plus</v-icon>NEW RESTORE</v-toolbar-title>
        <v-spacer></v-spacer>
        <router-link class="nav-link" to="/utils/restore"><v-btn icon><v-icon style="font-size:22px">fas fa-times-circle</v-icon></v-btn></router-link>
      </v-toolbar>
      <v-container fluid grid-list-lg>
        <v-layout row wrap>
          <v-flex xs12>
            <v-stepper v-model="stepper" vertical>
              <v-stepper-step :complete="stepper > 1" step="1">SOURCE</v-stepper-step>
              <v-stepper-content step="1" style="padding-top:0px; padding-left:10px">
                <v-form ref="sourceForm" style="margin-left:10px">
                  <div class="text-body-1">Choose a restoring method:</div>
                  <v-radio-group v-model="source" style="margin-top:10px; margin-bottom:20px" hide-details>
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
                  <v-file-input v-if="source == 'file'" v-model="file" show-size accept=".sql" label="Select an .sql file" :rules="[v => !!v || '']" prepend-icon truncate-length="100" hide-details></v-file-input>
                  <v-text-field v-else-if="source == 'url'" v-model="url" label="Enter an URL" :rules="[v => !!v || '']" hide-details></v-text-field>
                </v-form>
                <div style="margin-left:10px; margin-top:20px">
                  <v-btn color="primary" @click="nextStep">CONTINUE</v-btn>
                  <router-link to="/utils/restore"><v-btn text style="margin-left:5px">CANCEL</v-btn></router-link>
                </div>
              </v-stepper-content>
              <v-stepper-step :complete="stepper > 2" step="2">DESTINATION</v-stepper-step>
              <v-stepper-content step="2" style="padding-top:0px; padding-left:10px">
                <v-form ref="destinationForm" style="margin-left:10px">
                  <v-autocomplete v-model="server" :items="serverItems" item-value="id" item-text="name" label="Server" :rules="[v => !!v || '']" style="margin-top:10px">
                    <template v-slot:[`selection`]="{ item }">
                      <v-icon small :color="item.shared ? '#EB5F5D' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                      {{ item.name }}
                    </template>
                    <template v-slot:[`item`]="{ item }">
                      <v-icon small :color="item.shared ? '#EB5F5D' : 'warning'" style="margin-right:10px">{{ item.shared ? 'fas fa-users' : 'fas fa-user' }}</v-icon>
                      {{ item.name }}
                    </template>
                  </v-autocomplete>
                  <v-text-field v-model="database" label="Database" :rules="[v => !!v || '']" style="padding-top:0px" hide-details></v-text-field>
                </v-form>
                <div style="margin-left:10px; margin-top:20px">
                  <v-btn color="primary" @click="nextStep">CONTINUE</v-btn>
                  <v-btn text @click="stepper = 1" style="margin-left:5px">CANCEL</v-btn>
                </div>
              </v-stepper-content>
              <v-stepper-step step="3">OVERVIEW</v-stepper-step>
              <v-stepper-content step="3" style="padding-top:0px; padding-left:10px">
                <div style="margin-left:10px">
                </div>
                <div style="margin-left:10px; margin-top:20px">
                  <v-btn color="#00b16a">RESTORE</v-btn>
                  <v-btn color="#EF5354" @click="stepper = 2" style="margin-left:5px">CANCEL</v-btn>
                </div>
              </v-stepper-content>
            </v-stepper>
          </v-flex>
        </v-layout>
      </v-container>
    </v-card>
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

export default {
  data() {
    return {
      loading: false,
      stepper: 1,
      serverItems: [],
      server: '',
      database: '',
      source: 'file',
      file: null,
      url: '',

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
    source() {
      requestAnimationFrame(() => {
        if (typeof this.$refs.form !== 'undefined') this.$refs.form.resetValidation()
      })
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
      if (this.stepper == 1) {
        if (!this.$refs.sourceForm.validate()) {
          this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
          return
        }
      }
      else if (this.stepper == 2) {
        if (!this.$refs.destinationForm.validate()) {
          this.notification('Please make sure all required fields are filled out correctly', '#EF5354')
          return
        }
      }
      this.stepper = this.stepper + 1
    },
    submitRestore() {
      this.stepper = 1
    },
    notification(message, color) {
      this.snackbarText = message
      this.snackbarColor = color 
      this.snackbar = true
    }
  }
}
</script>