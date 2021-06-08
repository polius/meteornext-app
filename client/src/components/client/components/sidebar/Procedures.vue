<template>
  <div>
    <!---------------->
    <!-- PROCEDURES -->
    <!---------------->
    <v-dialog v-model="dialog" max-width="60%">
      <v-card>
        <v-toolbar v-if="dialogOptions.text.length == 0" dense flat color="primary">
          <v-toolbar-title class="white--text subtitle-1"><v-icon small style="padding-right:10px; padding-bottom:3px">fas fa-compress</v-icon>{{ dialogOptions.title }}</v-toolbar-title>
          <v-spacer></v-spacer>
          <v-btn :disabled="loading" @click="dialog = false" icon><v-icon size="22">fas fa-times-circle</v-icon></v-btn>
        </v-toolbar>
        <v-card-text style="padding:15px 15px 5px;">
          <v-container style="padding:0px; max-width:100%;">
            <v-layout wrap>
              <div v-if="dialogOptions.text.length > 0" class="text-h6" style="font-weight:400;"> {{ dialogOptions.title }}</div>
              <v-flex xs12>
                <v-form ref="dialogForm" style="margin-top:10px; margin-bottom:10px;">
                  <div v-if="dialogOptions.text.length > 0" class="body-1" style="font-weight:300; font-size:1.05rem!important;">{{ dialogOptions.text }}</div>
                  <div v-if="dialogOptions.mode == 'createProcedure'">
                    <v-text-field v-model="dialogOptions.item.name" label="Name" autofocus :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>
                    <v-text-field v-model="dialogOptions.item.params" label="Parameters" placeholder="IN country CHAR(3), OUT cities INT" style="padding-top:0px;"></v-text-field>
                    <div style="margin-left:auto; margin-right:auto; height:40vh; width:100%">
                      <div id="dialogEditor" style="height:100%;"></div>
                    </div>
                    <v-checkbox v-model="dialogOptions.item.deterministic" label="Deterministic" hide-details class="body-1" style="padding:0px; padding-bottom:5px;"></v-checkbox>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'renameProcedure'">
                    <v-text-field readonly v-model="dialogOptions.item.currentName" :rules="[v => !!v || '']" label="Current name" required style="padding-top:0px;"></v-text-field>
                    <v-text-field @keyup.enter="dialogSubmit" v-model="dialogOptions.item.newName" :rules="[v => !!v || '']" label="New name" autofocus required hide-details style="padding-top:0px; padding-bottom:5px;"></v-text-field>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'duplicateProcedure'">
                    <v-text-field readonly v-model="dialogOptions.item.currentName" :rules="[v => !!v || '']" label="Current name" required style="padding-top:0px;"></v-text-field>
                    <v-text-field @keyup.enter="dialogSubmit" v-model="dialogOptions.item.newName" :rules="[v => !!v || '']" label="New name" autofocus required hide-details style="padding-top:0px; padding-bottom:5px;"></v-text-field>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'deleteProcedure'">
                    <v-list style="padding-bottom:0px;">
                      <v-list-item v-for="item in sidebarSelected" :key="item.key" style="min-height:35px; padding-left:10px;">
                        <v-list-item-content style="padding:0px">
                          <v-list-item-title style="font-weight:300;"><span style="margin-right:10px;">-</span>{{ item.name }}</v-list-item-title>
                        </v-list-item-content>
                      </v-list-item>
                    </v-list>
                  </div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
                  <v-row no-gutters>
                    <v-col v-if="dialogOptions.submit.length > 0" cols="auto" style="margin-right:5px; margin-bottom:10px;">
                      <v-btn :loading="loading" @click="dialogSubmit" color="#00b16a">{{ dialogOptions.submit }}</v-btn>
                    </v-col>
                    <v-col v-if="dialogOptions.cancel.length > 0" style="margin-bottom:10px;">
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
import ace from 'ace-builds';

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
      dialogEditor: null,
    }
  },
  props: { contextMenuItem: Object },
  computed: {
    ...mapFields([
      'settings',
      'dialogOpened',
    ], { path: 'client/client' }),
    ...mapFields([
      'database',
      'sidebarOpened',
      'sidebarSelected',
      'headerTab',
      'headerTabSelected',
      'tableItems',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('click-contextmenu-procedure', this.contextMenuClicked);
  },
  watch: {
    dialog (val) {
      this.dialogOpened = val
      if (!val) return
      if (this.dialogEditor == null && this.dialogOptions.mode == 'createProcedure') this.initEditor()
      requestAnimationFrame(() => {
        if (typeof this.$refs.dialogForm !== 'undefined') this.$refs.dialogForm.resetValidation()
      })
    },
  },
  methods: {
    initEditor() {
      this.$nextTick(() => {
        // Editor Settings
        this.dialogEditor = ace.edit("dialogEditor", {
          mode: "ace/mode/mysql",
          theme: "ace/theme/monokai",
          fontSize: parseInt(this.settings['font_size']) || 14,
          showPrintMargin: false,
          wrap: true,
          autoScrollEditorIntoView: true,
          enableBasicAutocompletion: true,
          enableLiveAutocompletion: true,
          enableSnippets: false,
          highlightActiveLine: false
        });
        this.dialogEditor.session.setOptions({ tabSize: 4, useSoftTabs: false })

        // Add default value + placeholder
        let placeholder = `/*
SELECT COUNT(*) INTO cities
FROM world.city
WHERE CountryCode = country;
*/`
        this.dialogEditor.setValue(placeholder, -1)
        this.dialogEditor.on("focus", () => {
          if (this.dialogEditor.getValue() == placeholder) this.dialogEditor.setValue('')
        })
        this.dialogEditor.on("blur", () => {
          if (this.dialogEditor.getValue().length == 0) this.dialogEditor.setValue(placeholder, -1)
        })

        // Add custom keybinds
        this.dialogEditor.container.addEventListener("keydown", (e) => {
          // - Increase Font Size -
          if (e.key.toLowerCase() == "+" && (e.ctrlKey || e.metaKey)) {
            e.preventDefault()
            let size = parseInt(this.dialogEditor.getFontSize(), 10) || 12
            this.dialogEditor.setFontSize(size + 1)
          }
          // - Decrease Font Size -
          else if (e.key.toLowerCase() == "-" && (e.ctrlKey || e.metaKey)) {
            e.preventDefault()
            let size = parseInt(this.dialogEditor.getFontSize(), 10) || 12
            this.dialogEditor.setFontSize(Math.max(size - 1 || 1))
          }
        }, false);
      })
    },
    contextMenuClicked(item) {
      if (item == 'Create Procedure') this.createProcedure()
      else if (item == 'Rename Procedure') this.renameProcedure()
      else if (item == 'Duplicate Procedure') this.duplicateProcedure()
      else if (item == 'Delete Procedure') this.deleteProcedure()
      else if (item == 'Export') this.exportProcedure()
      else if (item == 'Copy Procedure Syntax') this.copyProcedureSyntaxSubmit()
    },
    createProcedure() {
      let dialogOptions = { 
        mode: 'createProcedure', 
        title: 'CREATE PROCEDURE', 
        text: '', 
        item: { name: '', params: '' }, 
        submit: 'Confirm', 
        cancel: 'Cancel'
      }
      if (this.dialogEditor != null) this.dialogEditor.setValue('')
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    renameProcedure() {
      let dialogOptions = { 
        mode: 'renameProcedure', 
        title: 'RENAME PROCEDURE', 
        text: '', 
        item: { currentName: this.contextMenuItem.name, newName: '' }, 
        submit: 'Confirm', 
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    duplicateProcedure() {
      let dialogOptions = { 
        mode: 'duplicateProcedure', 
        title: 'DUPLICATE PROCEDURE', 
        text: '', 
        item: { currentName: this.contextMenuItem.name, newName: '' }, 
        submit: 'Confirm',
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    deleteProcedure() {
      let dialogOptions = { 
        mode: 'deleteProcedure', 
        title: 'DELETE PROCEDURE', 
        text: "Are you sure you want to delete the following procedures? This operation cannot be undone.",
        item: {}, 
        submit: 'Confirm',
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    exportProcedure() {
      const items = this.sidebarSelected.map(x => x.name)
      EventBus.$emit('show-bottombar-objects-export', { object: 'procedures', items })
    },
    dialogSubmit() {
      // Check if all fields are filled
      if (!this.$refs.dialogForm.validate()) {
        EventBus.$emit('send-notification', 'Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      this.loading = true
      if (this.dialogOptions.mode == 'createProcedure') this.createProcedureSubmit()
      else if (this.dialogOptions.mode == 'renameProcedure') this.renameProcedureSubmit() 
      else if (this.dialogOptions.mode == 'duplicateProcedure') this.duplicateProcedureSubmit() 
      else if (this.dialogOptions.mode == 'deleteProcedure') this.deleteProcedureSubmit() 
    },
    createProcedureSubmit() {
      let procedureName = this.dialogOptions.item.name
      let procedureParams = this.dialogOptions.item.params
      let procedureCode = this.dialogEditor.getValue().endsWith(';') ? this.dialogEditor.getValue() : this.dialogEditor.getValue() + ';'
      let procedureDeterministic = this.dialogOptions.item.deterministic ? '\nDETERMINISTIC' : ''
      let query = "CREATE PROCEDURE `" + procedureName + '` (' + procedureParams + ')' + procedureDeterministic + '\nBEGIN\n' + procedureCode + '\nEND;'
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', [query], resolve, reject)
      }).then(() => { 
        return new Promise((resolve, reject) => { 
          EventBus.$emit('get-sidebar-objects', this.database, resolve, reject)
        }).then(() => {
          // Hide Dialog
          this.dialog = false
          // Select new created proceure
          this.sidebarSelected = [{ id: 'procedure|' + procedureName, name: procedureName, type: 'Procedure' }]
          // Open sidebar parent
          this.sidebarOpened = ['procedures']
          // Change view to Info
          this.headerTab = 3
          this.headerTabSelected = 'info_procedure'
          EventBus.$emit('get-info', 'procedure')
        })
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    renameProcedureSubmit() {
      let currentName = this.dialogOptions.item.currentName
      let newName = this.dialogOptions.item.newName
      let queries = ["SHOW CREATE PROCEDURE `" + currentName + "`", "DROP PROCEDURE IF EXISTS `" + currentName + "`"]
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', queries, resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['Create Procedure'].split(' PROCEDURE `' + currentName + '`')[1]
        let query = "CREATE PROCEDURE `" + newName + "` " + syntax
        return new Promise((resolve, reject) => {
          EventBus.$emit('execute-sidebar', [query], resolve, reject)
        }).then(() => { 
          return new Promise((resolve, reject) => { 
            EventBus.$emit('get-sidebar-objects', this.database, resolve, reject)
          }).then(() => {
            // Hide Dialog
            this.dialog = false
            // Select duplicated view
            this.sidebarSelected = [{ id: 'procedure|' + newName, name: newName, type: 'Procedure' }]
            // Change view to Info
            this.headerTab = 3
            this.headerTabSelected = 'info_procedure'
            EventBus.$emit('get-info', 'procedure')
          })
        }).catch(() => {})
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    duplicateProcedureSubmit() {
      let currentName = this.dialogOptions.item.currentName
      let newName = this.dialogOptions.item.newName
      let queries = ["SHOW CREATE PROCEDURE `" + currentName + "`"]
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', queries, resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['Create Procedure'].split(' PROCEDURE `' + currentName + '`')[1]
        let query = "CREATE PROCEDURE `" + newName + "` " + syntax
        return new Promise((resolve, reject) => {
          EventBus.$emit('execute-sidebar', [query], resolve, reject)
        }).then(() => { 
          return new Promise((resolve, reject) => { 
            EventBus.$emit('get-sidebar-objects', this.database, resolve, reject)
          }).then(() => {
            // Hide Dialog
            this.dialog = false
            // Select duplicated view
            this.sidebarSelected = [{ id: 'procedure|' + newName, name: newName, type: 'Procedure' }]
            // Change view to Info
            this.headerTab = 3
            this.headerTabSelected = 'info_procedure'
            EventBus.$emit('get-info', 'procedure')
          })
        }).catch(() => {})
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    deleteProcedureSubmit() {
      let queries = []
      for (let item of this.sidebarSelected) queries.push("DROP PROCEDURE `" + item.name + "`;")
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', queries, resolve, reject)
      }).then(() => { 
        return new Promise((resolve, reject) => { 
          EventBus.$emit('get-sidebar-objects', this.database, resolve, reject)
        }).then(() => {
          // Hide Dialog
          this.dialog = false
          // Unselect deleted view
          this.sidebarSelected = []
          // Change view to Client
          this.headerTab = 0
          this.headerTabSelected = 'client'
        })
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    copyProcedureSyntaxSubmit() {
      let name = this.contextMenuItem.name
      let query = "SHOW CREATE PROCEDURE `" + name + "`;"
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', [query], resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['Create Procedure']
        if (syntax == null) EventBus.$emit('send-notification', "Insufficient privileges to copy the procedure syntax", 'error')
        else navigator.clipboard.writeText(syntax) + ';'
      }).catch(() => {}).finally(() => { this.loading = false })
    },
  }
}
</script>