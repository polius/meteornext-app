<template>
  <div>
    <!------------>
    <!-- DIALOG -->
    <!------------>
    <v-dialog v-model="dialog" persistent max-width="60%">
      <v-card>
        <v-toolbar v-if="dialogOptions.mode != 'delete'" flat color="primary">
          <v-toolbar-title class="white--text">{{ dialogOptions.title }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="dialog = false" icon><v-icon>fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <div v-if="dialogOptions.mode == 'delete'" class="text-h6" style="font-weight:400;">{{ dialogOptions.title }}</div>
              <v-flex xs12>
                <v-form ref="dialogForm" style="margin-top:10px; margin-bottom:15px;">
                  <div v-if="dialogOptions.text.length > 0" class="body-1" style="font-weight:300; font-size:1.05rem!important;">{{ dialogOptions.text }}</div>
                  <div v-if="dialogOptions.mode == 'createTable'">
                    <v-text-field @keyup.enter="dialogSubmit" v-model="dialogOptions.item.name" :rules="[v => !!v || '']" label="Table Name" autofocus required style="padding-top:0px;"></v-text-field>
                    <v-autocomplete @change="getCollations" v-model="dialogOptions.item.encoding" :items="encodings" :rules="[v => !!v || '']" label="Table Encoding" auto-select-first required style="padding-top:0px;"></v-autocomplete>
                    <v-autocomplete :loading="loading" v-model="dialogOptions.item.collation" :items="collations" :rules="[v => !!v || '']" label="Table Collation" auto-select-first required style="padding-top:0px;"></v-autocomplete>
                    <v-select v-model="dialogOptions.item.engine" :items="engines" :rules="[v => !!v || '']" label="Table Engine" hide-details required style="padding-top:0px;"></v-select>
                  </div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col v-if="dialogOptions.submit.length > 0" cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loading" @click="dialogSubmit" color="primary">{{ dialogOptions.submit }}</v-btn>
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
      // Loading
      loading: false,
      // Dialog
      dialog: false,
      dialogOptions: { mode: '', title: '', text: '', item: {}, submit: '', cancel: '' },
      // Selectors
      collations: [],
    }
  },
  props: { contextMenuItem: Object },
  computed: {
    ...mapFields([
      'server',
      'database',
      'databaseItems',
      'treeview',
      'treeviewSelected',
      'headerTab',
      'headerTabSelected',
      'tabStructureSelected',
    ], { path: 'client/connection' }),
    encodings: function () {
      let db = this.databaseItems.filter(obj => { return obj.text == this.database })[0]
      let encodings = [{ text: 'Default (' + db.encoding + ')', value: db.encoding }]
      encodings.push({ divider: true })
      encodings.push(...this.server.encodings.reduce((acc, val) => { 
        acc.push({ text: val.description + ' (' + val.encoding + ')', value: val.encoding })
        return acc
      }, []))
      return encodings
    },
    engines: function() {
      let db = this.server.engines.filter(obj => { return obj.support == 'DEFAULT' })[0]
      let engines = [{ text: 'Default (' + db.engine + ')', value: db.engine }]
      engines.push({ divider: true })
      engines.push(...this.server.engines.reduce((acc, val) => { 
        acc.push(val.engine)
        return acc
      }, []))
      return engines
    },
  },
  created() {
    // Build Collations
    let db = this.databaseItems.filter(obj => { return obj.text == this.database })[0]
    this.getCollations(db.encoding)
  },
  mounted() {
    EventBus.$on('CLICK_CONTEXTMENU_TABLE', this.contextMenuClicked);
  },
  methods: {
    contextMenuClicked(item) {
      if (item == 'Create Table') this.createTable()
      else if (item == 'Rename Table') 1 == 1
      else if (item == 'Duplicate Table') 1 == 1
      else if (item == 'Truncate Table') 1 == 1
      else if (item == 'Delete Table') 1 == 1
      else if (item == 'Export') 1 == 1
      else if (item == 'Copy Table Syntax') 1 == 1
    },
    createTable() {
      let dialogOptions = { 
        mode: 'createTable', 
        title: 'Create Table', 
        text: '', 
        item: { name: '', encoding: this.encodings[0].value, collation: this.collations[0].value, engine: this.engines[0].value }, 
        submit: 'Submit', 
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
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
          this.parseCollations(response.data.collations)
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('SEND_NOTIFICATION', error.response.data.message, 'error')
        })
        .finally(() => {
          this.loading = false
        })
    },
    parseCollations(data) {
      let db = this.databaseItems.filter(obj => { return obj.text == this.database })[0]
      this.collations = [{ text: 'Default (' + db.collation + ')', value: db.collation }, { divider: true }, ...JSON.parse(data)]
    },
    showObjectsTab(object) {
      let promise = new Promise((resolve, reject) => {
        this.headerTab = 6
        this.headerTabSelected = 'objects'
        this.objectsTab = (object == 'tables') ? 1 : (object == 'views') ? 2 : (object == 'triggers') ? 3 : (object == 'functions') ? 4 : (object == 'procedures') ? 5 : (object == 'events') ? 6 : 0
        this.tabObjectsSelected = object
        if (this.objectsHeaders[object].length == 0) {
          setTimeout(() => {
            this.gridApi.objects[object].showLoadingOverlay()
            EventBus.$emit('GET_OBJECTS', resolve, reject)
          }, 100)        
        }
      })
      promise.then(() => {})
        .catch(() => {})
        .finally(() => {
          this.gridApi.objects[object].hideOverlay() 
        })
    },
    dialogSubmit() {
      // Check if all fields are filled
      if (!this.$refs.dialogForm.validate()) {
        EventBus.$emit('SEND_NOTIFICATION', 'Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      this.loading = true
      if (this.dialogOptions.mode == 'createTable') {
        let tableName = this.dialogOptions.item.name
        let query = "CREATE TABLE " + tableName + " (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY) ENGINE=" + this.dialogOptions.item.engine + " DEFAULT CHARSET=" + this.dialogOptions.item.encoding + " COLLATE= " + this.dialogOptions.item.collation + ";"
        new Promise((resolve, reject) => { EventBus.$emit('EXECUTE_SIDEBAR', query, resolve, reject) }).then(() => { 
          // Hide Dialog
          this.dialog = false
          // Select new created table
          this.treeview = ['table|' + tableName]
          this.treeviewSelected = { id: 'table|' + tableName, name: tableName, type: 'Table' }
          // Change view to Structure - columns
          this.headerTab = 1
          this.headerTabSelected = 'structure'
          this.tabStructureSelected = 'columns'
          EventBus.$emit('GET_STRUCTURE')
        }).catch(() => {}).finally(() => { this.loading = false })
      }
      // else if (this.dialogOptions.mode == 'createView') {
        
      // }
    },
  }
}
</script>