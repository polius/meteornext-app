<template>
  <div>
    <!--------------->
    <!-- FUNCTIONS -->
    <!--------------->
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
                <v-form ref="dialogForm" style="margin-bottom:10px">
                  <div v-if="dialogOptions.text.length > 0" class="body-1">{{ dialogOptions.text }}</div>
                  <div v-if="dialogOptions.mode == 'createFunction'">
                    <v-text-field v-model="dialogOptions.item.name" label="Name" autofocus :rules="[v => !!v || '']" required style="padding-top:8px"></v-text-field>
                    <v-text-field v-model="dialogOptions.item.params" label="Parameters" placeholder="credit DECIMAL(10,2)" style="padding-top:0px;"></v-text-field>
                    <v-text-field v-model="dialogOptions.item.returns" label="Returns" placeholder="VARCHAR(20)" style="padding-top:0px;"></v-text-field>
                    <div style="margin-left:auto; margin-right:auto; height:35vh; width:100%">
                      <div id="dialogEditor" style="height:100%;"></div>
                    </div>
                    <v-checkbox v-model="dialogOptions.item.deterministic" label="Deterministic" hide-details class="body-1" style="padding:0px; padding-bottom:5px"></v-checkbox>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'renameFunction'">
                    <v-text-field readonly v-model="dialogOptions.item.currentName" :rules="[v => !!v || '']" label="Current Name" required></v-text-field>
                    <v-text-field @keyup.enter="dialogSubmit" v-model="dialogOptions.item.newName" :rules="[v => !!v || '']" label="New Name" autofocus required hide-details style="padding-top:0px; padding-bottom:5px"></v-text-field>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'duplicateFunction'">
                    <v-text-field readonly v-model="dialogOptions.item.currentName" :rules="[v => !!v || '']" label="Current Name" required></v-text-field>
                    <v-text-field @keyup.enter="dialogSubmit" v-model="dialogOptions.item.newName" :rules="[v => !!v || '']" label="New Name" autofocus required hide-details style="padding-top:0px; padding-bottom:5px"></v-text-field>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'deleteFunction'">
                    <v-card style="margin-top:15px; margin-bottom:15px">
                      <v-list>
                        <v-list-item v-for="item in sidebarSelected" :key="item.key" style="min-height:35px">
                          <v-list-item-content style="padding:0px">
                            <v-list-item-title>{{ item.name }}</v-list-item-title>
                          </v-list-item-content>
                        </v-list-item>
                      </v-list>
                    </v-card>
                  </div>
                </v-form>
                <v-divider></v-divider>
                <div style="margin-top:15px;">
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
  activated() {
    EventBus.$on('click-contextmenu-function', this.contextMenuClicked)
  },
  watch: {
    dialog (val) {
      this.dialogOpened = val
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
          keyboardHandler: "ace/keyboard/vscode",
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
      else if (item == 'Export Function') this.exportFunction()
      else if (item == 'Clone Function') this.cloneFunction()
      else if (item == 'Copy Function Name') this.copyFunctionNameSubmit()
      else if (item == 'Copy Function Syntax') this.copyFunctionSyntaxSubmit()
    },
    createFunction() {
      let dialogOptions = { 
        mode: 'createFunction', 
        icon: 'fas fa-plus',
        title: 'CREATE FUNCTION', 
        text: '', 
        item: { name: '', params: '' }, 
        submit: 'Confirm', 
        cancel: 'Cancel'
      }
      if (this.dialogEditor != null) this.dialogEditor.setValue('')
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    renameFunction() {
      let dialogOptions = { 
        mode: 'renameFunction', 
        icon: 'fas fa-feather-alt',
        title: 'RENAME FUNCTION', 
        text: '', 
        item: { currentName: this.contextMenuItem.name, newName: '' }, 
        submit: 'Confirm', 
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    duplicateFunction() {
      let dialogOptions = { 
        mode: 'duplicateFunction', 
        icon: 'fas fa-clone',
        title: 'DUPLICATE FUNCTION', 
        text: '', 
        item: { currentName: this.contextMenuItem.name, newName: '' }, 
        submit: 'Confirm',
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    deleteFunction() {
      let dialogOptions = { 
        mode: 'deleteFunction', 
        icon: 'fas fa-minus',
        title: 'DELETE FUNCTION', 
        text: "Are you sure you want to delete the selected functions? This operation cannot be undone.",
        item: {}, 
        submit: 'Confirm',
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    exportFunction() {
      const items = this.sidebarSelected.map(x => x.name)
      EventBus.$emit('show-bottombar-objects-export', { object: 'functions', items })
    },
    cloneFunction() {
      const items = this.sidebarSelected.map(x => x.name)
      EventBus.$emit('show-bottombar-objects-clone', { object: 'functions', items })
    },
    dialogSubmit() {
      // Check if all fields are filled
      if (!this.$refs.dialogForm.validate()) {
        EventBus.$emit('send-notification', 'Please make sure all required fields are filled out correctly', '#EF5354')
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
      let query = "CREATE FUNCTION `" + functionName.replaceAll('`','``') + '` (' + functionParams + ')\nRETURNS ' + functionReturns + functionDeterministic + '\nBEGIN\n' + functionCode + '\nEND;'
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', [query], resolve, reject)
      }).then(() => { 
        return new Promise((resolve, reject) => { 
          EventBus.$emit('get-sidebar-objects', this.database, resolve, reject)
        }).then(() => {
          // Hide Dialog
          this.dialog = false
          // Select new created proceure
          this.sidebarSelected = [{ id: 'function|' + functionName, name: functionName, type: 'Function' }]
          // Open sidebar parent
          this.sidebarOpened = ['functions']
          // Change view to Info
          this.headerTab = 3
          this.headerTabSelected = 'info_function'
          EventBus.$emit('get-info', 'function')
        })
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    renameFunctionSubmit() {
      let currentName = this.dialogOptions.item.currentName
      let newName = this.dialogOptions.item.newName
      let queries = ["SHOW CREATE FUNCTION `" + currentName.replaceAll('`','``') + "`", "DROP FUNCTION IF EXISTS `" + currentName.replaceAll('`','``') + "`"]
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', queries, resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['Create Function'].split(' FUNCTION `' + currentName.replaceAll('`','``') + '`')[1]
        let query = "CREATE FUNCTION `" + newName.replaceAll('`','``') + "` " + syntax
        return new Promise((resolve, reject) => {
          EventBus.$emit('execute-sidebar', [query], resolve, reject)
        }).then(() => { 
          return new Promise((resolve, reject) => { 
            EventBus.$emit('get-sidebar-objects', this.database, resolve, reject)
          }).then(() => {
            // Hide Dialog
            this.dialog = false
            // Select duplicated view
            this.sidebarSelected = [{ id: 'function|' + newName, name: newName, type: 'Function' }]
            // Change view to Info
            this.headerTab = 3
            this.headerTabSelected = 'info_function'
            EventBus.$emit('get-info', 'function')
          })
        }).catch(() => {})
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    duplicateFunctionSubmit() {
      let currentName = this.dialogOptions.item.currentName
      let newName = this.dialogOptions.item.newName
      let queries = ["SHOW CREATE FUNCTION `" + currentName.replaceAll('`','``') + "`"]
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', queries, resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['Create Function'].split(' FUNCTION `' + currentName.replaceAll('`','``') + '`')[1]
        let query = "CREATE FUNCTION `" + newName.replaceAll('`','``') + "` " + syntax
        return new Promise((resolve, reject) => {
          EventBus.$emit('execute-sidebar', [query], resolve, reject)
        }).then(() => { 
          return new Promise((resolve, reject) => { 
            EventBus.$emit('get-sidebar-objects', this.database, resolve, reject)
          }).then(() => {
            // Hide Dialog
            this.dialog = false
            // Select duplicated view
            this.sidebarSelected = [{ id: 'function|' + newName, name: newName, type: 'Function' }]
            // Change view to Info
            this.headerTab = 3
            this.headerTabSelected = 'info_function'
            EventBus.$emit('get-info', 'function')
          })
        }).catch(() => {})
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    deleteFunctionSubmit() {
      let queries = []
      for (let item of this.sidebarSelected) queries.push("DROP FUNCTION `" + item.name.replaceAll('`','``') + "`;")
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
    copyFunctionNameSubmit() {
      const name = this.contextMenuItem.name
      this.copyToClipboard(name)
      EventBus.$emit('send-notification', 'Copied to clipboard.', '#00b16a', 1)
    },
    copyFunctionSyntaxSubmit() {
      let name = this.contextMenuItem.name
      let query = "SHOW CREATE FUNCTION `" + name.replaceAll('`','``') + "`;"
      new Promise((resolve, reject) => { 
        EventBus.$emit('execute-sidebar', [query], resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['Create Function']
        if (syntax == null) EventBus.$emit('send-notification', "Insufficient privileges to copy the function syntax", '#EF5354')
        else {
          this.copyToClipboard(syntax + ';')
          EventBus.$emit('send-notification', 'Copied to clipboard.', '#00b16a', 1)
        }
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