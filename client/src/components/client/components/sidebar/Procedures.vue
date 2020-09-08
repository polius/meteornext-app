<template>
  <div>
    <!---------------->
    <!-- PROCEDURES -->
    <!---------------->
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
                <v-form ref="dialogForm" style="margin-top:10px; margin-bottom:15px;">
                  <div v-if="dialogOptions.text.length > 0" class="body-1" style="font-weight:300; font-size:1.05rem!important;">{{ dialogOptions.text }}</div>
                  <div v-if="dialogOptions.mode == 'createProcedure'">
                    <v-text-field v-model="dialogOptions.item.name" label="Name" autofocus :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>
                    <v-text-field v-model="dialogOptions.item.params" label="Parameters" placeholder="IN param1 CHAR(3), OUT param2 INT" style="padding-top:0px;"></v-text-field>
                    <div style="margin-left:auto; margin-right:auto; height:35vh; width:100%">
                      <div id="dialogEditor" style="height:100%;"></div>
                    </div>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'renameProcedure'">
                    <v-text-field readonly v-model="dialogOptions.item.currentName" :rules="[v => !!v || '']" label="Current name" required style="padding-top:0px;"></v-text-field>
                    <v-text-field @keyup.enter="dialogSubmit" v-model="dialogOptions.item.newName" :rules="[v => !!v || '']" label="New name" autofocus required hide-details style="padding-top:0px;"></v-text-field>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'duplicateProcedure'">
                    <v-text-field readonly v-model="dialogOptions.item.currentName" :rules="[v => !!v || '']" label="Current name" required style="padding-top:0px;"></v-text-field>
                    <v-text-field @keyup.enter="dialogSubmit" v-model="dialogOptions.item.newName" :rules="[v => !!v || '']" label="New name" autofocus required hide-details style="padding-top:0px;"></v-text-field>
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
import * as ace from 'ace-builds';
import 'ace-builds/webpack-resolver';
import 'ace-builds/src-noconflict/ext-language_tools';

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
      'database',
      'treeview',
      'treeviewOpened',
      'treeviewSelected',
      'headerTab',
      'headerTabSelected',
      'tableItems',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('CLICK_CONTEXTMENU_PROCEDURE', this.contextMenuClicked);
  },
  watch: {
    dialog (val) {
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
          mode: "ace/mode/sql",
          theme: "ace/theme/monokai",
          fontSize: 14,
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
        let placeholder = '/* SELECT COUNT(*) INTO param2 FROM tbl WHERE col = param1; */'
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
      else if (item == 'Export') 1 == 1
      else if (item == 'Copy Procedure Syntax') this.copyProcedureSyntaxSubmit()
    },
    createProcedure() {
      let dialogOptions = { 
        mode: 'createProcedure', 
        title: 'Create Procedure', 
        text: '', 
        item: { name: '', params: '' }, 
        submit: 'Submit', 
        cancel: 'Cancel'
      }
      if (this.dialogEditor != null) this.dialogEditor.setValue('')
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    renameProcedure() {
      let dialogOptions = { 
        mode: 'renameProcedure', 
        title: 'Rename Procedure', 
        text: '', 
        item: { currentName: this.contextMenuItem.name, newName: '' }, 
        submit: 'Submit', 
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    duplicateProcedure() {
      let dialogOptions = { 
        mode: 'duplicateProcedure', 
        title: 'Duplicate Procedure', 
        text: '', 
        item: { currentName: this.contextMenuItem.name, newName: '' }, 
        submit: 'Submit',
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    deleteProcedure() {
      let dialogOptions = { 
        mode: 'deleteProcedure', 
        title: 'Delete Procedure?', 
        text: "Are you sure you want to delete the procedure '" + this.contextMenuItem.name + "'? This operation cannot be undone.",
        item: {}, 
        submit: 'Submit',
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
      if (this.dialogOptions.mode == 'createProcedure') this.createProcedureSubmit()
      else if (this.dialogOptions.mode == 'renameProcedure') this.renameProcedureSubmit() 
      else if (this.dialogOptions.mode == 'duplicateProcedure') this.duplicateProcedureSubmit() 
      else if (this.dialogOptions.mode == 'deleteProcedure') this.deleteProcedureSubmit() 
    },
    createProcedureSubmit() {
      let procedureName = this.dialogOptions.item.name
      let procedureParams = this.dialogOptions.item.params
      let procedureCode = this.dialogEditor.getValue().endsWith(';') ? this.dialogEditor.getValue() : this.dialogEditor.getValue() + ';'
      let query = "CREATE PROCEDURE " + procedureName + ' (' + procedureParams + ')\nBEGIN\n' + procedureCode + '\nEND;'
      new Promise((resolve, reject) => { 
        EventBus.$emit('EXECUTE_SIDEBAR', [query], resolve, reject)
      }).then(() => { 
        return new Promise((resolve, reject) => { 
          EventBus.$emit('GET_SIDEBAR_OBJECTS', this.database, resolve, reject)
        }).then(() => {
          // Hide Dialog
          this.dialog = false
          // Select new created proceure
          this.treeviewSelected = { id: 'procedure|' + procedureName, name: procedureName, type: 'Procedure' }
          this.treeview = ['procedure|' + procedureName]
          // Open treeview parent
          this.treeviewOpened = ['procedures']
          // Change view to Info
          this.headerTab = 3
          this.headerTabSelected = 'info_procedure'
          EventBus.$emit('GET_INFO', 'procedure')
        })
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    renameProcedureSubmit() {
      let currentName = this.dialogOptions.item.currentName
      let newName = this.dialogOptions.item.newName
      let queries = ["SHOW CREATE PROCEDURE " + currentName, "DROP PROCEDURE IF EXISTS " + currentName]
      new Promise((resolve, reject) => { 
        EventBus.$emit('EXECUTE_SIDEBAR', queries, resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['Create Procedure'].split(' PROCEDURE `' + currentName + '`')[1]
        let query = "CREATE PROCEDURE " + newName + " " + syntax
        return new Promise((resolve, reject) => {
          EventBus.$emit('EXECUTE_SIDEBAR', [query], resolve, reject)
        }).then(() => { 
          return new Promise((resolve, reject) => { 
            EventBus.$emit('GET_SIDEBAR_OBJECTS', this.database, resolve, reject)
          }).then(() => {
            // Hide Dialog
            this.dialog = false
            // Select duplicated view
            this.treeviewSelected = { id: 'procedure|' + newName, name: newName, type: 'Procedure' }
            this.treeview = ['procedure|' + newName]
            // Change view to Info
            this.headerTab = 3
            this.headerTabSelected = 'info_procedure'
            EventBus.$emit('GET_INFO', 'procedure')
          })
        }).catch(() => {})
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    duplicateProcedureSubmit() {
      let currentName = this.dialogOptions.item.currentName
      let newName = this.dialogOptions.item.newName
      let queries = ["SHOW CREATE PROCEDURE " + currentName]
      new Promise((resolve, reject) => { 
        EventBus.$emit('EXECUTE_SIDEBAR', queries, resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['Create Procedure'].split(' PROCEDURE `' + currentName + '`')[1]
        let query = "CREATE PROCEDURE " + newName + " " + syntax
        return new Promise((resolve, reject) => {
          EventBus.$emit('EXECUTE_SIDEBAR', [query], resolve, reject)
        }).then(() => { 
          return new Promise((resolve, reject) => { 
            EventBus.$emit('GET_SIDEBAR_OBJECTS', this.database, resolve, reject)
          }).then(() => {
            // Hide Dialog
            this.dialog = false
            // Select duplicated view
            this.treeviewSelected = { id: 'procedure|' + newName, name: newName, type: 'Procedure' }
            this.treeview = ['procedure|' + newName]
            // Change view to Info
            this.headerTab = 3
            this.headerTabSelected = 'info_procedure'
            EventBus.$emit('GET_INFO', 'procedure')
          })
        }).catch(() => {})
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    deleteProcedureSubmit() {
      let name = this.contextMenuItem.name
      let query = "DROP PROCEDURE " + name + ";"
      new Promise((resolve, reject) => { 
        EventBus.$emit('EXECUTE_SIDEBAR', [query], resolve, reject)
      }).then(() => { 
        return new Promise((resolve, reject) => { 
          EventBus.$emit('GET_SIDEBAR_OBJECTS', this.database, resolve, reject)
        }).then(() => {
          // Hide Dialog
          this.dialog = false
          // Unselect deleted view
          this.treeviewSelected = {}
          this.treeview = []
          // Change view to Client
          this.headerTab = 0
          this.headerTabSelected = 'client'
        })
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    copyProcedureSyntaxSubmit() {
      let name = this.contextMenuItem.name
      let query = "SHOW CREATE PROCEDURE " + name + ";"
      new Promise((resolve, reject) => { 
        EventBus.$emit('EXECUTE_SIDEBAR', [query], resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['Create Procedure']
        navigator.clipboard.writeText(syntax)
        EventBus.$emit('SEND_NOTIFICATION', "Syntax copied to clipboard", 'info')
      }).catch(() => {}).finally(() => { this.loading = false })
    },
  }
}
</script>