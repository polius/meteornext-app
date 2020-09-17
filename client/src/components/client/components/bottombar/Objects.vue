<template>
  <div>
    <!------------------------->
    <!-- BOTTOMBAR - OBJECTS -->
    <!------------------------->
    <div style="height:35px; border-top:2px solid #2c2c2c;">
      <v-btn :loading="sidebarLoading" :disabled="sidebarLoading" @click="refreshObjects" text small title="Refresh" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-redo-alt</v-icon></v-btn>
      <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn :disabled="sidebarLoading" @click="createDatabase" text small title="Create Database" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-plus</v-icon></v-btn>
      <v-btn :disabled="sidebarLoading || database.length == 0" @click="dropDatabase" text small title="Drop Database" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-minus</v-icon></v-btn>
      <span style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn v-if="database.length > 0" :disabled="sidebarLoading" @click="importSQL" text small title="Import SQL" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-arrow-up</v-icon></v-btn>
      <v-btn v-if="database.length > 0" :disabled="sidebarLoading" text small title="Export Objects" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-arrow-down</v-icon></v-btn>
      <span v-if="database.length > 0" :disabled="sidebarLoading" style="background-color:#424242; padding-left:1px;margin-left:1px; margin-right:1px;"></span>
      <v-btn v-if="database.length > 0" :disabled="sidebarLoading" text small title="Database Settings" style="height:30px; min-width:36px; margin-top:1px; margin-left:2px; margin-right:2px;"><v-icon small style="font-size:12px;">fas fa-cog</v-icon></v-btn>
    </div>
    <!------------>
    <!-- DIALOG -->
    <!------------>
    <v-dialog v-model="dialog" persistent max-width="60%">
      <v-card>
        <v-toolbar v-if="dialogOptions.text.length == 0" flat color="primary">
          <v-toolbar-title class="white--text">{{ dialogOptions.title }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="dialog = false" icon><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <div v-if="dialogOptions.text.length > 0" class="text-h6" style="font-weight:400;"> {{ dialogOptions.title }}</div>
              <v-flex xs12>
                <v-form @submit.prevent ref="dialogForm" style="margin-top:10px; margin-bottom:15px;">
                  <div v-if="dialogOptions.text.length > 0" class="body-1" style="font-weight:300; font-size:1.05rem!important;">{{ dialogOptions.text }}</div>
                  <div v-if="dialogOptions.mode == 'createDatabase'">
                    <v-text-field @keyup.enter="dialogSubmit" v-model="dialogOptions.item.name" :rules="[v => !!v || '']" label="Database Name" autofocus required style="padding-top:0px;"></v-text-field>
                    <v-autocomplete @change="getCollations" v-model="dialogOptions.item.encoding" :items="encodings" :rules="[v => !!v || '']" label="Database Encoding" auto-select-first required style="padding-top:0px;"></v-autocomplete>
                    <v-autocomplete :disabled="dialogOptions.item.collation.length == 0" :loading="loading" v-model="dialogOptions.item.collation" :items="collations" :rules="[v => !!v || '']" label="Database Collation" auto-select-first required hide-details style="padding-top:0px;"></v-autocomplete>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'dropDatabase'">
                    <div class="body-1" style="margin-top:15px; font-weight:300; font-size:1.05rem!important;">Type the database name to confirm.</div>
                    <v-text-field @keyup.enter="database == dialogOptions.item.name ? dialogSubmit() : {}" v-model="dialogOptions.item.name" :rules="[v => !!v || '']" label="Database Name" autofocus required hide-details style="margin-top:15px;"></v-text-field>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'importSQL'">
                    <!-- <div class="body-1" style="margin-top:15px; font-weight:300; font-size:1.05rem!important;">Type the database name to confirm.</div> -->
                    <v-file-input @change="importSQLSelected" show-size accept=".sql" label="File input" style="padding:0px"></v-file-input>
                    <v-progress-linear v-model="dialogOptions.item.progress" rounded color="light-blue" height="25">
                      <template v-slot="{ value }">
                        <strong>{{ Math.ceil(value) }}%</strong>
                      </template>
                    </v-progress-linear>
                  </div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col v-if="dialogOptions.submit.length > 0" cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :disabled="dialogOptions.mode == 'dropDatabase' && database != dialogOptions.item.name" :loading="loading" @click="dialogSubmit" color="primary">{{ dialogOptions.submit }}</v-btn>
                    </v-col>
                    <v-col v-if="dialogOptions.cancel.length > 0" style="margin-bottom:10px;">
                      <v-btn :disabled="loading" @click="dialog = false" outlined color="#e74d3c">{{ dialogOptions.cancel }}</v-btn>
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
import EventBus from '../../js/event-bus'
import { mapFields } from '../../js/map-fields'

export default {
  data() {
    return {
      loading: false,
      // Dialog
      dialog: false,
      dialogOptions: { mode: '', title: '', text: '', item: {}, submit: '', cancel: '' },
      // Database
      encodings: [],
      collations: [],
    }
  },
  computed: {
    ...mapFields([
      'server',
      'database',
      'databaseItems',
      'sidebarLoading',
      'headerTab',
      'headerTabSelected',
    ], { path: 'client/connection' }),
  },
  watch: {
    dialog (val) {
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.dialogForm !== 'undefined') this.$refs.dialogForm.resetValidation()
      })
    },
  },
  methods: {
    refreshObjects() {
      new Promise((resolve, reject) => { 
        EventBus.$emit('REFRESH_SIDEBAR_OBJECTS', resolve, reject)
      })
    },
    createDatabase() {
      // Build selectors
      this.buildSelectors()

      // Build Dialog
      let dialogOptions = { 
        mode: 'createDatabase', 
        title: 'Create Database', 
        text: '', 
        item: { name: '', encoding: this.encodings[0].value, collation: '' }, 
        submit: 'Submit', 
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    dropDatabase() {
      let dialogOptions = { 
        mode: 'dropDatabase', 
        title: 'Drop Database?', 
        text: "Are you sure you want to drop the database '" + this.database + "'? This operation cannot be undone.",
        item: { name: '' }, 
        submit: 'Submit',
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    importSQL() {
      let dialogOptions = { 
        mode: 'importSQL', 
        title: 'Import SQL', 
        text: "",
        item: { file: '', progress: 0 }, 
        submit: 'Import',
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    dialogSubmit() {
      // Check if all fields are filled
      if (!this.$refs.dialogForm.validate()) {
        EventBus.$emit('SEND_NOTIFICATION', 'Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      this.loading = true
      if (this.dialogOptions.mode == 'createDatabase') this.createDatabaseSubmit()
      else if (this.dialogOptions.mode == 'dropDatabase') this.dropDatabaseSubmit()
      else if (this.dialogOptions.mode == 'importSQL') this.importSQLSubmit()
    },
    createDatabaseSubmit() {
      let databaseName = this.dialogOptions.item.name
      let databaseEncoding = this.dialogOptions.item.encoding 
      let databaseCollation = this.dialogOptions.item.collation
      let query = "CREATE DATABASE " + databaseName + " CHARACTER SET " + databaseEncoding + " COLLATE " + databaseCollation + ';'
      console.log(query)
      new Promise((resolve, reject) => { 
        EventBus.$emit('EXECUTE_SIDEBAR', [query], resolve, reject)
      }).then(() => { 
        return new Promise((resolve, reject) => {
          // Change current database
          this.database = databaseName
          EventBus.$emit('REFRESH_SIDEBAR_OBJECTS', resolve, reject)
        }).then(() => {
          // Hide Dialog
          this.dialog = false
          // Change view to Client
          this.headerTab = 0
          this.headerTabSelected = 'client'
        })
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    dropDatabaseSubmit() {
      let databaseName = this.dialogOptions.item.name
      let query = "DROP DATABASE " + databaseName + ';'
      console.log(query)
      new Promise((resolve, reject) => { 
        EventBus.$emit('EXECUTE_SIDEBAR', [query], resolve, reject)
      }).then(() => { 
        // Change current database
        this.databaseItems = this.databaseItems.filter(item => item.text !== databaseName)
        this.database = ''
        // Hide Dialog
        this.dialog = false
        // Change view to Client
        this.headerTab = 0
        this.headerTabSelected = 'client'
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    buildSelectors() {
      // Build Encodings
      this.encodings = [{ text: 'Default (' + this.server.defaults.encoding + ')', value: this.server.defaults.encoding }]
      this.encodings.push({ divider: true })
      this.encodings.push(...this.server.encodings.reduce((acc, val) => { 
        acc.push({ text: val.description + ' (' + val.encoding + ')', value: val.encoding })
        return acc
      }, []))

      // Build Collations
      this.getCollations(this.server.defaults.encoding)
    },
    getCollations(encoding) {
      // Retrieve Databases
      this.loading = true
      const payload = {
        server: this.server.id, 
        encoding: encoding
      }
      axios.get('/client/collations', { params: payload })
        .then((response) => {
          this.parseCollations(encoding, response.data.collations)
        })
        .catch((error) => {
          console.log(error)
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('SEND_NOTIFICATION', error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
        })
    },
    parseCollations(encoding, data) {
      if (this.collations.length == 0) this.collations = [{ text: 'Default (' + this.server.defaults.collation + ')', value: this.server.defaults.collation }, { divider: true }, ...JSON.parse(data)]
      else {
        let def = this.server.encodings.filter(obj => { return obj.encoding == encoding })[0]
        this.collations = [{ text: 'Default (' + def.collation + ')', value: def.collation }, { divider: true }, ...JSON.parse(data)]
      }
      this.dialogOptions.item.collation = this.collations[0].value
    },
    importSQLSelected(file) {
      this.dialogOptions.item.file = file
      this.dialogOptions.item.progress = 0
    },
    importSQLSubmit() {
       if (!this.dialogOptions.item.file) {
        EventBus.$emit('SEND_NOTIFICATION', 'Please select a file', 'info')
        this.loading = false
        return
      }
      const options = {
        onUploadProgress: (progressEvent) => {
          var percentCompleted = Math.round((progressEvent.loaded * 100) / progressEvent.total)
          this.dialogOptions.item.progress = percentCompleted
        }
      }
      const data = new FormData();
      data.append('server', this.server.id)
      data.append('database', this.database)
      data.append('file', this.dialogOptions.item.file)
      axios.post('client/import', data, options)
        .then((response) => {
          EventBus.$emit('SEND_NOTIFICATION', 'File successfully uploaded', 'success')
          this.dialog = false
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('SEND_NOTIFICATION', error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
        })
    },
  }
}
</script>