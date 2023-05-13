<template>
  <div>
    <!------------>
    <!-- TABLES -->
    <!------------>
    <v-dialog v-model="dialog" max-width="60%">
      <v-card>
        <v-toolbar dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="margin-right:10px; padding-bottom:3px">{{ dialogOptions.icon }}</v-icon>{{ dialogOptions.title }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="dialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <v-flex xs12>
                <v-form ref="dialogForm" style="margin-bottom:15px">
                  <div v-if="dialogOptions.text.length > 0" class="body-1">{{ dialogOptions.text }}</div>
                  <div v-if="dialogOptions.mode == 'createTable'">
                    <v-text-field @keyup.enter="dialogSubmit" v-model="dialogOptions.item.name" :rules="[v => !!v || '']" label="Table Name" autofocus required style="padding-top:8px"></v-text-field>
                    <v-autocomplete @change="getCollations" v-model="dialogOptions.item.encoding" :items="encodings" :rules="[v => !!v || '']" label="Table Encoding" auto-select-first required style="padding-top:0px;"></v-autocomplete>
                    <v-autocomplete :disabled="loading" :loading="loading" v-model="dialogOptions.item.collation" :items="collations" :rules="[v => !!v || '']" label="Table Collation" auto-select-first required style="padding-top:0px;"></v-autocomplete>
                    <v-select v-model="dialogOptions.item.engine" :items="engines" :rules="[v => !!v || '']" label="Table Engine" hide-details required style="padding-top:0px;"></v-select>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'renameTable'">
                    <v-text-field readonly v-model="dialogOptions.item.currentName" :rules="[v => !!v || '']" label="Current Name" required></v-text-field>
                    <v-text-field @keyup.enter="dialogSubmit" v-model="dialogOptions.item.newName" :rules="[v => !!v || '']" label="New Name" autofocus required hide-details style="padding-top:0px;"></v-text-field>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'duplicateTable'">
                    <v-text-field readonly v-model="dialogOptions.item.currentName" :rules="[v => !!v || '']" label="Current Name" required></v-text-field>
                    <v-text-field @keyup.enter="dialogSubmit" v-model="dialogOptions.item.newName" :rules="[v => !!v || '']" label="New Name" autofocus required hide-details style="padding-top:0px;"></v-text-field>
                    <v-checkbox v-model="dialogOptions.item.duplicateContent" label="Duplicate Content" hide-details class="body-1"></v-checkbox>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'truncateTable'">
                    <v-card style="margin-top:15px; margin-bottom:15px">
                      <v-list>
                        <v-list-item v-for="item in sidebarSelected" :key="item.key" style="min-height:35px">
                          <v-list-item-content style="padding:0px">
                            <v-list-item-title>{{ item.name }}</v-list-item-title>
                          </v-list-item-content>
                        </v-list-item>
                      </v-list>
                    </v-card>
                    <v-checkbox v-model="dialogOptions.item.force" label="Force Truncate (Disable Integrity Checks)" hide-details class="body-1" style="margin:0px"></v-checkbox>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'deleteTable'">
                    <v-card style="margin-top:15px; margin-bottom:15px">
                      <v-list>
                        <v-list-item v-for="item in sidebarSelected" :key="item.key" style="min-height:35px">
                          <v-list-item-content style="padding:0px">
                            <v-list-item-title>{{ item.name }}</v-list-item-title>
                          </v-list-item-content>
                        </v-list-item>
                      </v-list>
                    </v-card>
                    <v-checkbox v-model="dialogOptions.item.force" label="Force Delete (Disable Integrity Checks)" hide-details class="body-1" style="margin:0"></v-checkbox>
                  </div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px">
                  <v-row no-gutters>
                    <v-col v-if="dialogOptions.submit.length > 0" cols="auto" style="margin-right:5px">
                      <v-btn :loading="loading" @click="dialogSubmit" color="#00b16a">{{ dialogOptions.submit }}</v-btn>
                    </v-col>
                    <v-col v-if="dialogOptions.cancel.length > 0">
                      <v-btn :disabled="loading" @click="dialog = false" color="#EF5354">{{ dialogOptions.cancel }}</v-btn>
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
      dialogOptions: { mode: '', icon: '', title: '', text: '', item: {}, submit: '', cancel: '' },
      // Database
      encodings: [],
      collations: [],
      engines: [],
    }
  },
  props: { contextMenuItem: Object },
  computed: {
    ...mapFields([
      'dialogOpened',
    ], { path: 'client/client' }),
    ...mapFields([
      'index',
      'id',
      'server',
      'database',
      'sidebarOpened',
      'sidebarSelected',
      'headerTab',
      'headerTabSelected',
      'tabStructureSelected',
    ], { path: 'client/connection' }),
  },
  activated() {
    EventBus.$on('click-contextmenu-table', this.contextMenuClicked)
  },
  watch: {
    dialog (val) {
      this.dialogOpened = val
      if (!val) return
      requestAnimationFrame(() => {
        if (typeof this.$refs.dialogForm !== 'undefined') this.$refs.dialogForm.resetValidation()
      })
    },
  },
  methods: {
    buildSelectors() {
      // Build Encodings
      let item = this.server.defaults.encoding
      this.encodings = [{ text: 'Default (' + item + ')', value: item }]
      this.encodings.push({ divider: true })
      this.encodings.push(...this.server.encodings.reduce((acc, val) => { 
        acc.push({ text: val.description + ' (' + val.encoding + ')', value: val.encoding })
        return acc
      }, []))

      // Build Collations
      this.getCollations(item)

      // Build Engines
      item = this.server.engines.filter(obj => { return obj.support == 'DEFAULT' })[0]
      this.engines = [{ text: 'Default (' + item.engine + ')', value: item.engine }]
      this.engines.push({ divider: true })
      this.engines.push(...this.server.engines.reduce((acc, val) => { 
        acc.push(val.engine)
        return acc
      }, []))
    },
    getCollations(encoding) {
      if (encoding == null) return
      // Retrieve Databases
      this.loading = true
      const payload = {
        connection: this.id + '-shared',
        server: this.server.id, 
        encoding: encoding
      }
      axios.get('/client/collations', { params: payload })
        .then((response) => {
          this.parseCollations(encoding, response.data.collations)
        })
        .catch((error) => {
          if (error.response === undefined || error.response.status != 400) this.$store.dispatch('app/logout').then(() => this.$router.push('/login'))
          else EventBus.$emit('send-notification', error.response.data.message, '#EF5354')
        })
        .finally(() => {
          this.loading = false
        })
    },
    parseCollations(encoding, data) {
      let def = this.server.encodings.filter(obj => { return obj.encoding == encoding })[0]
      this.collations = [{ text: 'Default (' + def.collation + ')', value: def.collation }, { divider: true }, ...JSON.parse(data)]
      this.dialogOptions.item.collation = this.collations[0].value
    },
    contextMenuClicked(item) {
      if (item == 'Create Table') this.createTable()
      else if (item == 'Rename Table') this.renameTable()
      else if (item == 'Duplicate Table') this.duplicateTable()
      else if (item == 'Truncate Table') this.truncateTable()
      else if (item == 'Delete Table') this.deleteTable()
      else if (item == 'Export Table') this.exportTable()
      else if (item == 'Clone Table') this.cloneTable()
      else if (item == 'Copy Table Name') this.copyTableNameSubmit()
      else if (item == 'Copy Table Syntax') this.copyTableSyntaxSubmit()
    },
    createTable() {
      this.buildSelectors()
      let dialogOptions = { 
        mode: 'createTable', 
        icon: 'fas fa-plus',
        title: 'CREATE TABLE', 
        text: '', 
        item: { name: '', encoding: this.encodings[0].value, collation: '', engine: this.engines[0].value }, 
        submit: 'Confirm', 
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    renameTable() {
      let dialogOptions = { 
        mode: 'renameTable', 
        icon: 'fas fa-feather-alt',
        title: 'RENAME TABLE', 
        text: '', 
        item: { currentName: this.contextMenuItem.name, newName: '' }, 
        submit: 'Confirm', 
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    duplicateTable() {
      let dialogOptions = { 
        mode: 'duplicateTable', 
        icon: 'fas fa-clone',
        title: 'DUPLICATE TABLE', 
        text: '', 
        item: { currentName: this.contextMenuItem.name, newName: '', duplicateContent: false }, 
        submit: 'Confirm',
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    truncateTable() {
      let dialogOptions = { 
        mode: 'truncateTable', 
        icon: 'fas fa-broom',
        title: 'TRUNCATE TABLE', 
        text: "Are you sure you want to delete ALL records in the selected tables? This operation cannot be undone.", 
        item: { force: false }, 
        submit: 'Confirm',
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    deleteTable() {
      let dialogOptions = { 
        mode: 'deleteTable', 
        icon: 'fas fa-minus',
        title: 'DELETE TABLE', 
        text: "Are you sure you want to delete the selected tables? This operation cannot be undone.",
        item: { force: false }, 
        submit: 'Confirm',
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    exportTable() {
      const items = this.sidebarSelected.map(x => x.name)
      EventBus.$emit('show-bottombar-objects-export', { object: 'tables', items })
    },
    cloneTable() {
      const items = this.sidebarSelected.map(x => x.name)
      EventBus.$emit('show-bottombar-objects-clone', { object: 'tables', items })
    },
    dialogSubmit() {
      // Check if all fields are filled
      if (!this.$refs.dialogForm.validate()) {
        EventBus.$emit('send-notification', 'Please make sure all required fields are filled out correctly', '#EF5354')
        this.loading = false
        return
      }
      this.loading = true
      if (this.dialogOptions.mode == 'createTable') this.createTableSubmit()
      else if (this.dialogOptions.mode == 'renameTable') this.renameTableSubmit() 
      else if (this.dialogOptions.mode == 'duplicateTable') this.duplicateTableSubmit() 
      else if (this.dialogOptions.mode == 'truncateTable') this.truncateTableSubmit() 
      else if (this.dialogOptions.mode == 'deleteTable') this.deleteTableSubmit() 
    },
    createTableSubmit() {
      let tableName = this.dialogOptions.item.name
      let query = "CREATE TABLE `" + tableName.replaceAll('`','``') + "` (id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY) ENGINE=" + this.dialogOptions.item.engine + " DEFAULT CHARSET=" + this.dialogOptions.item.encoding + " COLLATE= " + this.dialogOptions.item.collation + ";"
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', [query], resolve, reject)
      }).then(() => { 
        return new Promise((resolve, reject) => { 
          EventBus.$emit('get-sidebar-objects', this.database, resolve, reject)
        }).then(() => {
          // Hide Dialog
          this.dialog = false
          // Select new created table
          this.sidebarSelected = [{ id: 'table|' + tableName, name: tableName, type: 'Table' }]
          // Open sidebar parent
          this.sidebarOpened = ['tables']
          // Change view to Structure (columns)
          this.headerTab = 1
          this.headerTabSelected = 'structure'
          this.tabStructureSelected = 'columns'
          EventBus.$emit('get-structure')
        })
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    renameTableSubmit() {
      let currentName = this.contextMenuItem.name
      let newName = this.dialogOptions.item.newName
      let query = "ALTER TABLE `" + currentName.replaceAll('`','``') + "` RENAME TO `" + newName.replaceAll('`','``') + "`;"
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', [query], resolve, reject)
      }).then(() => { 
        return new Promise((resolve, reject) => { 
          EventBus.$emit('get-sidebar-objects', this.database, resolve, reject)
        }).then(() => {
          // Hide Dialog
          this.dialog = false
          // Select renamed table
          this.sidebarSelected = [{ id: 'table|' + newName, name: newName, type: 'Table' }]
        })
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    duplicateTableSubmit() {
      let currentName = this.contextMenuItem.name
      let newName = this.dialogOptions.item.newName
      let duplicateContent = this.dialogOptions.item.duplicateContent
      let queries = ["SET sql_mode = 'NO_AUTO_VALUE_ON_ZERO'", "CREATE TABLE `" + newName + "` LIKE `" + currentName + "`;"]
      if (duplicateContent) queries.push("INSERT INTO `" + newName.replaceAll('`','``') + "` SELECT * FROM `" + currentName.replaceAll('`','``') + "`;")
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', queries, resolve, reject)
      }).then(() => { 
        return new Promise((resolve, reject) => { 
          EventBus.$emit('get-sidebar-objects', this.database, resolve, reject)
        }).then(() => {
          // Hide Dialog
          this.dialog = false
          // Select duplicated table
          this.sidebarSelected = [{ id: 'table|' + newName, name: newName, type: 'Table' }]
        })
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    truncateTableSubmit() {
      let force = this.dialogOptions.item.force
      let queries = []
      if (force) queries.push("SET FOREIGN_KEY_CHECKS = 0")
      for (let item of this.sidebarSelected) queries.push("TRUNCATE TABLE " + item.name + ";")
      if (force) queries.push("SET FOREIGN_KEY_CHECKS = 1")
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', queries, resolve, reject)
      }).then(() => { 
        // Hide Dialog
        this.dialog = false
        // Clean Table
        if (this.headerTabSelected == 'content') EventBus.$emit('get-content', true)
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    deleteTableSubmit() {
      let force = this.dialogOptions.item.force
      let queries = []
      if (force) queries.push("SET FOREIGN_KEY_CHECKS = 0")
      for (let item of this.sidebarSelected) queries.push("DROP TABLE `" + item.name.replaceAll('`','``') + "`;")
      if (force) queries.push("SET FOREIGN_KEY_CHECKS = 1")
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', queries, resolve, reject)
      }).then(() => { 
        return new Promise((resolve, reject) => { 
          EventBus.$emit('get-sidebar-objects', this.database, resolve, reject)
        }).then(() => {
          // Hide Dialog
          this.dialog = false
          // Unselect deleted table
          this.sidebarSelected = []
          // Change view to Client
          this.headerTab = 0
          this.headerTabSelected = 'client'
        })
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    copyTableNameSubmit() {
      const name = this.contextMenuItem.name
      this.copyToClipboard(name)
      EventBus.$emit('send-notification', 'Copied to clipboard.', '#00b16a', 1)
    },
    copyTableSyntaxSubmit() {
      let name = this.contextMenuItem.name
      let query = "SHOW CREATE TABLE `" + name.replaceAll('`','``') + "`;"
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', [query], resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['Create Table'] + ';'
        this.copyToClipboard(syntax)
        EventBus.$emit('send-notification', 'Copied to clipboard.', '#00b16a', 1)
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    copyToClipboard(textToCopy) {
      if (navigator.clipboard && window.isSecureContext) return navigator.clipboard.writeText(textToCopy)
      else {
        let textArea = document.createElement("textarea")
        textArea.value = textToCopy
        textArea.style.position = "absolute"
        textArea.style.opacity = 0
        document.body.appendChild(textArea)
        textArea.select()
        return new Promise((res, rej) => {
          document.execCommand('copy') ? res() : rej()
          textArea.remove()
        })
      }
    },
  }
}
</script>