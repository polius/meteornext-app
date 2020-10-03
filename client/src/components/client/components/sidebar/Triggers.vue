<template>
  <div>
    <!-------------->
    <!-- TRIGGERS -->
    <!-------------->
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
                  <div v-if="dialogOptions.mode == 'createTrigger'">
                    <v-text-field v-model="dialogOptions.item.name" label="Name" autofocus :rules="[v => !!v || '']" required style="padding-top:0px;"></v-text-field>
                    <v-select v-model="dialogOptions.item.time" :items="['Before','After']" :rules="[v => !!v || '']" label="Action Time" required style="padding-top:0px;"></v-select>
                    <v-select v-model="dialogOptions.item.event" :items="['Insert','Update','Delete']" :rules="[v => !!v || '']" label="Event" required style="padding-top:0px;"></v-select>
                    <v-select v-model="dialogOptions.item.table" :items="tableItems" :rules="[v => !!v || '']" label="Table" required style="padding-top:0px;"></v-select>
                    <div style="margin-left:auto; margin-right:auto; height:35vh; width:100%">
                      <div id="dialogEditor" style="height:100%;"></div>
                    </div>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'renameTrigger'">
                    <v-text-field readonly v-model="dialogOptions.item.currentName" :rules="[v => !!v || '']" label="Current name" required style="padding-top:0px;"></v-text-field>
                    <v-text-field @keyup.enter="dialogSubmit" v-model="dialogOptions.item.newName" :rules="[v => !!v || '']" label="New name" autofocus required hide-details style="padding-top:0px;"></v-text-field>
                  </div>
                  <div v-else-if="dialogOptions.mode == 'duplicateTrigger'">
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
    EventBus.$on('CLICK_CONTEXTMENU_TRIGGER', this.contextMenuClicked);
  },
  watch: {
    dialog (val) {
      if (!val) return
      if (this.dialogEditor == null && this.dialogOptions.mode == 'createTrigger') this.initEditor()
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
      if (item == 'Create Trigger') this.createTrigger()
      else if (item == 'Rename Trigger') this.renameTrigger()
      else if (item == 'Duplicate Trigger') this.duplicateTrigger()
      else if (item == 'Delete Trigger') this.deleteTrigger()
      else if (item == 'Export') this.exportTrigger()
      else if (item == 'Copy Trigger Syntax') this.copyTriggerSyntaxSubmit()
    },
    createTrigger() {
      let dialogOptions = { 
        mode: 'createTrigger', 
        title: 'Create Trigger', 
        text: '', 
        item: { name: '', table: '', time: '', event: '' }, 
        submit: 'Submit', 
        cancel: 'Cancel'
      }
      if (this.dialogEditor != null) this.dialogEditor.setValue('')
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    renameTrigger() {
      let dialogOptions = { 
        mode: 'renameTrigger', 
        title: 'Rename Trigger', 
        text: '', 
        item: { currentName: this.contextMenuItem.name, newName: '' }, 
        submit: 'Submit', 
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    duplicateTrigger() {
      let dialogOptions = { 
        mode: 'duplicateTrigger', 
        title: 'Duplicate Trigger', 
        text: '', 
        item: { currentName: this.contextMenuItem.name, newName: '' }, 
        submit: 'Submit',
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    deleteTrigger() {
      let dialogOptions = { 
        mode: 'deleteTrigger', 
        title: 'Delete Trigger?', 
        text: "Are you sure you want to delete the trigger '" + this.contextMenuItem.name + "'? This operation cannot be undone.",
        item: {}, 
        submit: 'Submit',
        cancel: 'Cancel'
      }
      this.dialogOptions = dialogOptions
      this.dialog = true
    },
    exportTrigger() {
      EventBus.$emit('SHOW_BOTTOMBAR_OBJECTS_EXPORT', { object: 'triggers', name: this.contextMenuItem.name })
    },
    dialogSubmit() {
      // Check if all fields are filled
      if (!this.$refs.dialogForm.validate()) {
        EventBus.$emit('SEND_NOTIFICATION', 'Please make sure all required fields are filled out correctly', 'error')
        this.loading = false
        return
      }
      this.loading = true
      if (this.dialogOptions.mode == 'createTrigger') this.createTriggerSubmit()
      else if (this.dialogOptions.mode == 'renameTrigger') this.renameTriggerSubmit() 
      else if (this.dialogOptions.mode == 'duplicateTrigger') this.duplicateTriggerSubmit() 
      else if (this.dialogOptions.mode == 'deleteTrigger') this.deleteTriggerSubmit() 
    },
    createTriggerSubmit() {
      let triggerName = this.dialogOptions.item.name
      let triggerCode = this.dialogEditor.getValue().endsWith(';') ? this.dialogEditor.getValue() : this.dialogEditor.getValue() + ';'
      let query = "CREATE TRIGGER " + triggerName + ' ' + this.dialogOptions.item.time + ' ' + this.dialogOptions.item.event + ' ON ' + this.dialogOptions.item.table + ' FOR EACH ROW BEGIN\n' + triggerCode + '\nEND;'
      new Promise((resolve, reject) => { 
        EventBus.$emit('EXECUTE_SIDEBAR', [query], resolve, reject)
      }).then(() => { 
        return new Promise((resolve, reject) => { 
          EventBus.$emit('GET_SIDEBAR_OBJECTS', this.database, resolve, reject)
        }).then(() => {
          // Hide Dialog
          this.dialog = false
          // Select new created trigger
          this.sidebarSelected = { id: 'trigger|' + triggerName, name: triggerName, type: 'Trigger' }
          this.sidebar = ['trigger|' + triggerName]
          // Open sidebar parent
          this.sidebarOpened = ['triggers']
          // Change view to Info
          this.headerTab = 3
          this.headerTabSelected = 'info_trigger'
          EventBus.$emit('GET_INFO', 'trigger')
        })
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    renameTriggerSubmit() {
      let currentName = this.dialogOptions.item.currentName
      let newName = this.dialogOptions.item.newName
      let queries = ["SHOW CREATE TRIGGER " + currentName, "DROP TRIGGER IF EXISTS " + currentName]
      new Promise((resolve, reject) => { 
        EventBus.$emit('EXECUTE_SIDEBAR', queries, resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['SQL Original Statement'].split(' TRIGGER ' + currentName + ' ')[1]
        let query = "CREATE TRIGGER " + newName + " " + syntax
        return new Promise((resolve, reject) => {
          EventBus.$emit('EXECUTE_SIDEBAR', [query], resolve, reject)
        }).then(() => { 
          return new Promise((resolve, reject) => { 
            EventBus.$emit('GET_SIDEBAR_OBJECTS', this.database, resolve, reject)
          }).then(() => {
            // Hide Dialog
            this.dialog = false
            // Select duplicated view
            this.sidebarSelected = { id: 'trigger|' + newName, name: newName, type: 'Trigger' }
            this.sidebar = ['trigger|' + newName]
            // Change view to Info
            this.headerTab = 3
            this.headerTabSelected = 'info_trigger'
            EventBus.$emit('GET_INFO', 'trigger')
          })
        }).catch(() => {})
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    duplicateTriggerSubmit() {
      let currentName = this.dialogOptions.item.currentName
      let newName = this.dialogOptions.item.newName
      let queries = ["SHOW CREATE TRIGGER " + currentName]
      new Promise((resolve, reject) => { 
        EventBus.$emit('EXECUTE_SIDEBAR', queries, resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['SQL Original Statement'].split(' TRIGGER ' + currentName + ' ')[1]
        let query = "CREATE TRIGGER " + newName + " " + syntax
        return new Promise((resolve, reject) => {
          EventBus.$emit('EXECUTE_SIDEBAR', [query], resolve, reject)
        }).then(() => { 
          return new Promise((resolve, reject) => { 
            EventBus.$emit('GET_SIDEBAR_OBJECTS', this.database, resolve, reject)
          }).then(() => {
            // Hide Dialog
            this.dialog = false
            // Select duplicated view
            this.sidebarSelected = { id: 'trigger|' + newName, name: newName, type: 'Trigger' }
            this.sidebar = ['trigger|' + newName]
            // Change view to Info
            this.headerTab = 3
            this.headerTabSelected = 'info_trigger'
            EventBus.$emit('GET_INFO', 'trigger')
          })
        }).catch(() => {})
      }).catch(() => {}).finally(() => { this.loading = false })
    },
    deleteTriggerSubmit() {
      let name = this.contextMenuItem.name
      let query = "DROP TRIGGER " + name + ";"
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
    copyTriggerSyntaxSubmit() {
      let name = this.contextMenuItem.name
      let query = "SHOW CREATE TRIGGER " + name + ";"
      new Promise((resolve, reject) => { 
        EventBus.$emit('EXECUTE_SIDEBAR', [query], resolve, reject)
      }).then((res) => {
        let syntax = JSON.parse(res.data)[0].data[0]['SQL Original Statement'] + ';'
        navigator.clipboard.writeText(syntax)
        EventBus.$emit('SEND_NOTIFICATION', "Syntax copied to clipboard", 'info')
      }).catch(() => {}).finally(() => { this.loading = false })
    },
  }
}
</script>