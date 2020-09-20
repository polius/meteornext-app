<template>
  <div>
    <v-dialog v-model="dialog" persistent max-width="60%">
      <v-card>
        <v-toolbar flat color="primary">
          <v-toolbar-title class="white--text">Create Database</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="dialog = false" icon><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form @submit.prevent ref="dialogForm" style="margin-top:10px; margin-bottom:15px;">
                  <v-text-field @keyup.enter="dialogSubmit" v-model="name" :rules="[v => !!v || '']" label="Database Name" autofocus required style="padding-top:0px;"></v-text-field>
                  <v-autocomplete @change="getCollations" v-model="encoding" :items="encodings" :rules="[v => !!v || '']" label="Database Encoding" auto-select-first required style="padding-top:0px;"></v-autocomplete>
                  <v-autocomplete :disabled="collation.length == 0" :loading="loading" v-model="collation" :items="collations" :rules="[v => !!v || '']" label="Database Collation" auto-select-first required hide-details style="padding-top:0px;"></v-autocomplete>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loading" @click="dialogSubmit" color="primary">Submit</v-btn>
                    </v-col>
                    <v-col style="margin-bottom:10px;">
                      <v-btn :disabled="loading" @click="dialog = false" outlined color="#e74d3c">Cancel</v-btn>
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
      name: '',
      encoding: '',
      collation: '',
      // Database
      encodings: [],
      collations: [],
    }
  },
  computed: {
    ...mapFields([
      'server',
      'database',
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
  mounted() {
    EventBus.$on('SHOW_BOTTOMBAR_OBJECTS_CREATE', this.showDialog);
  },
  methods: {
    showDialog() {
      this.buildSelectors()
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
      let databaseName = this.name
      let databaseEncoding = this.encoding 
      let databaseCollation = this.collation
      let query = "CREATE DATABASE " + databaseName + " CHARACTER SET " + databaseEncoding + " COLLATE " + databaseCollation + ';'
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
    buildSelectors() {
      // Build Encodings
      this.encodings = [{ text: 'Default (' + this.server.defaults.encoding + ')', value: this.server.defaults.encoding }]
      this.encodings.push({ divider: true })
      this.encodings.push(...this.server.encodings.reduce((acc, val) => { 
        acc.push({ text: val.description + ' (' + val.encoding + ')', value: val.encoding })
        return acc
      }, []))
      this.encoding = this.server.defaults.encoding
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
      this.collation = this.collations[0].value
    },
  }
}
</script>