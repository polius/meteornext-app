<template>
  <div>
    <!--------------->
    <!-- FUNCTIONS -->
    <!--------------->
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
                  <div v-if="dialogOptions.mode == 'createFunction'">
                    <v-text-field v-model="dialogOptions.item.name" label="Name" autofocus :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>
                    <v-text-field v-model="dialogOptions.item.params" label="Parameters" placeholder="credit DECIMAL(10,2)" style="padding-top:0px;"></v-text-field>
                    <v-text-field v-model="dialogOptions.item.returns" label="Returns" placeholder="VARCHAR(20)" style="padding-top:0px;"></v-text-field>
                    <div style="margin-left:auto; margin-right:auto; height:35vh; width:100%">
                      <div id="dialogEditor" style="height:100%;"></div>
                    </div>
                    <v-checkbox v-model="dialogOptions.item.deterministic" label="Deterministic" hide-details class="body-1" style="padding:0px"></v-checkbox>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'renameFunction'">
                    <v-text-field readonly v-model="dialogOptions.item.currentName" :rules="[v => !!v || '']" label="Current name" required style="padding-top:0px;"></v-text-field>
                    <v-text-field @keyup.enter="dialogSubmit" v-model="dialogOptions.item.newName" :rules="[v => !!v || '']" label="New name" autofocus required hide-details style="padding-top:0px;"></v-text-field>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'duplicateFunction'">
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
      'sidebar',
      'sidebarOpened',
      'sidebarSelected',
      'headerTab',
      'headerTabSelected',
      'tableItems',
    ], { path: 'client/connection' }),
  },
  mounted() {
    EventBus.$on('CLICK_CONTEXTMENU_FUNCTION', this.contextMenuClicked);
  },
  watch: {
    dialog (val) {
      if (!val) return
      if (this.dialogEditor == null && this.dialogOptions.mode == 'createFunction') this.initEditor()
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
        let placeholder = `/*
DECLARE customerLevel VARCHAR(20);

IF credit > 50000 THEN
    SET customerLevel = 'PLATINUM';
ELSE
    SET customerLevel = 'SILVER';
END IF;

RETURN (customerLevel);
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
      if (item == 'Create Function') this.createFunction()
      else if (item == 'Rename Function') this.renameFunction()
      else if (item == 'Duplicate Function') this.duplicateFunction()
      else if (item == 'Delete Function') this.deleteFunction()
      else if (item == 'Export') this.exportFunction()
      else if (item == 'Copy Function Syntax') this.copyFunctionSyntaxSubmit()
    },
    createFunction() {
      let dialogOptions = { 
        mode: 'createFunction', 
        title: 'Create Function', 
        text: '', 
        item: { name: '', params: '' }, 
        submit: 'Submit', 
        cancel: 'Cancel'
      }
      if (this.dialogEditor != null) this.dialogEditor.setValue('')
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    renameFunction() {
      let dialogOptions = { 
        mode: 'renameFunction', 
        title: 'Rename Function', 
        text: '', 
        item: { currentName: this.contextMenuItem.name, newName: '' }, 
        submit: 'Submit', 
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    duplicateFunction() {
      let dialogOptions = { 
        mode: 'duplicateFunction', 
        title: 'Duplicate Function', 
        text: '', 
        item: { currentName: this.contextMenuItem.name, newName: '' }, 
        submit: 'Submit',
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    deleteFunction() {
      let dialogOptions = { 
        mode: 'deleteFunction', 
        title: 'Delete Function?', 
        text: "Are you sure you want to delete the function '" + this.contextMenuItem.name + "'? This operation cannot be undone.",
        item: {}, 
        submit: 'Submit',
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    exportFunction() {
      EventBus.$emit('SHOW_BOTTOMBAR_OBJECTS_EXPORT', { object: 'functions', name: this.contextMenuItem.name })
    },
    dialogSubmit() {
      // Check if all fields are filled
      if (!this.$refs.dialogForm.validate()) {
        EventBus.$emit('SEND_NOTIFICATION', 'Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      this.loading = true
      if (this.dialogOptions.mode == 'createFunction') this.createFunctionSubmit()
      else if (this.dialogOptions.mode == 'renameFunction') this.renameFunctionSubmit() 
      else if (this.dialogOptions.mode == 'duplicateFunction') this.duplicateFunctionSubmit() 
      else if (this.dialogOptions.mode == 'deleteFunction') this.deleteFunctionSubmit() 
    },
    createFunctionSubmit() {
      let functionName = this.dialogOptions.item.name
      let functionParams = this.dialogOptions.item.params
      let functionReturns = this.dialogOptions.item.returns
      let functionCode = this.dialogEditor.getValue().endsWith(';') ? this.dialogEditor.getValue() : this.dialogEditor.getValue() + ';'
      let functionDeterministic = this.dialogOptions.item.deterministic ? '\nDETERMINISTIC' : ''
      let query = "CREATE FUNCTION " + functionName + ' (' + functionParams + ')\nRETURNS ' + functionReturns + functionDeterministic + '\nBEGIN\n' + functionCode + '\nEND;'
      new Promise((resolve, reject) => { 
        EventBus.$emit('EXECUTE_SIDEBAR', [query], resolve, reject)
      }).then(() => { 
        return new Promise((resolve, reject) => { 
          EventBus.$emit('GET_SIDEBAR_OBJECTS', this.database, resolve, reject)
        }).then(() => {
          // Hide Dialog
          this.dialog = false
          // Select new created proceure
          this.sidebarSelected = { id: 'function|' + functionName, name: functionName, type: 'Function' }
          this.sidebar = ['function|' + functionName]
          // Open sidebar parent
          this.sidebarOpened = ['functions']
          // Change view to Info
          this.headerTab = 3
          this.headerTabSelected = 'info_function'
          EventBus.$emit('GET_INFO', 'function')
        })
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    renameFunctionSubmit() {
      let currentName = this.dialogOptions.item.currentName
      let newName = this.dialogOptions.item.newName
      let queries = ["SHOW CREATE FUNCTION " + currentName, "DROP FUNCTION IF EXISTS " + currentName]
      new Promise((resolve, reject) => { 
        EventBus.$emit('EXECUTE_SIDEBAR', queries, resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['Create Function'].split(' FUNCTION `' + currentName + '`')[1]
        let query = "CREATE FUNCTION " + newName + " " + syntax
        return new Promise((resolve, reject) => {
          EventBus.$emit('EXECUTE_SIDEBAR', [query], resolve, reject)
        }).then(() => { 
          return new Promise((resolve, reject) => { 
            EventBus.$emit('GET_SIDEBAR_OBJECTS', this.database, resolve, reject)
          }).then(() => {
            // Hide Dialog
            this.dialog = false
            // Select duplicated view
            this.sidebarSelected = { id: 'function|' + newName, name: newName, type: 'Function' }
            this.sidebar = ['function|' + newName]
            // Change view to Info
            this.headerTab = 3
            this.headerTabSelected = 'info_function'
            EventBus.$emit('GET_INFO', 'function')
          })
        }).catch(() => {})
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    duplicateFunctionSubmit() {
      let currentName = this.dialogOptions.item.currentName
      let newName = this.dialogOptions.item.newName
      let queries = ["SHOW CREATE FUNCTION " + currentName]
      new Promise((resolve, reject) => { 
        EventBus.$emit('EXECUTE_SIDEBAR', queries, resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['Create Function'].split(' FUNCTION `' + currentName + '`')[1]
        let query = "CREATE FUNCTION " + newName + " " + syntax
        return new Promise((resolve, reject) => {
          EventBus.$emit('EXECUTE_SIDEBAR', [query], resolve, reject)
        }).then(() => { 
          return new Promise((resolve, reject) => { 
            EventBus.$emit('GET_SIDEBAR_OBJECTS', this.database, resolve, reject)
          }).then(() => {
            // Hide Dialog
            this.dialog = false
            // Select duplicated view
            this.sidebarSelected = { id: 'function|' + newName, name: newName, type: 'Function' }
            this.sidebar = ['function|' + newName]
            // Change view to Info
            this.headerTab = 3
            this.headerTabSelected = 'info_function'
            EventBus.$emit('GET_INFO', 'function')
          })
        }).catch(() => {})
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    deleteFunctionSubmit() {
      let name = this.contextMenuItem.name
      let query = "DROP FUNCTION " + name + ";"
      new Promise((resolve, reject) => { 
        EventBus.$emit('EXECUTE_SIDEBAR', [query], resolve, reject)
      }).then(() => { 
        return new Promise((resolve, reject) => { 
          EventBus.$emit('GET_SIDEBAR_OBJECTS', this.database, resolve, reject)
        }).then(() => {
          // Hide Dialog
          this.dialog = false
          // Unselect deleted view
          this.sidebarSelected = {}
          this.sidebar = []
          // Change view to Client
          this.headerTab = 0
          this.headerTabSelected = 'client'
        })
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    copyFunctionSyntaxSubmit() {
      let name = this.contextMenuItem.name
      let query = "SHOW CREATE FUNCTION " + name + ";"
      new Promise((resolve, reject) => { 
        EventBus.$emit('EXECUTE_SIDEBAR', [query], resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['Create Function']
        if (syntax == null) EventBus.$emit('SEND_NOTIFICATION', "Insufficient privileges to copy the function syntax", 'error')
        else navigator.clipboard.writeText(syntax) + ';'
      }).catch(() => {}).finally(() => { this.loading = false })
    },
  }
}
</script>